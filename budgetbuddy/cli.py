"""Command line entry point: python -m budgetbuddy <command>."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from budgetbuddy.db import connect, default_data_dir
from budgetbuddy.importer import import_file
from budgetbuddy.parsers import PARSERS

STATEMENT_SUFFIXES = {".csv", ".xlsx", ".xlsm"}


def _pounds(pence: int | None) -> str:
    if pence is None:
        return ""
    sign = "-" if pence < 0 else ""
    return f"{sign}£{abs(pence) / 100:,.2f}"


def _expand(paths: list[str]) -> list[Path]:
    """Accept files or folders (folders are scanned for statement files)."""
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(f for f in p.iterdir() if f.suffix.lower() in STATEMENT_SUFFIXES))
        else:
            files.append(p)
    return files


def cmd_import(args: argparse.Namespace, conn: sqlite3.Connection, data_dir: Path) -> int:
    failures = 0
    for path in _expand(args.files):
        try:
            r = import_file(conn, path, data_dir, account=args.account, owner=args.owner, fmt=args.format)
        except (OSError, ValueError) as exc:
            print(f"FAILED  {path.name}: {exc}", file=sys.stderr)
            failures += 1
            continue
        if r.skipped_file:
            print(f"SKIPPED {r.file_name}: already imported into {r.account}")
            continue
        print(
            f"OK      {r.file_name} -> {r.account} [{r.parser}]: "
            f"{r.rows_added} new, {r.duplicates} duplicates, {r.transfers_linked} transfers linked"
        )
        for w in r.warnings:
            print(f"        warning: {w}")
    return 1 if failures else 0


def cmd_status(args: argparse.Namespace, conn: sqlite3.Connection, data_dir: Path) -> int:
    print(f"Data folder: {data_dir}\n")
    rows = conn.execute(
        """
        SELECT a.name, a.kind, a.owner,
               COUNT(t.id) AS n, MIN(t.posted_on) AS first, MAX(t.posted_on) AS last,
               SUM(t.is_transfer) AS transfers,
               (SELECT balance_pence FROM transactions x WHERE x.account_id = a.id
                  AND x.balance_pence IS NOT NULL ORDER BY posted_on DESC, id DESC LIMIT 1) AS balance
        FROM accounts a LEFT JOIN transactions t ON t.account_id = a.id
        GROUP BY a.id ORDER BY a.name
        """
    ).fetchall()
    if not rows:
        print("No accounts yet. Run: python -m budgetbuddy import <file>")
        return 0
    for r in rows:
        print(f"{r['name']} ({r['kind']}, {r['owner']})")
        print(f"  {r['n']} cash transactions, {r['first'] or '-'} to {r['last'] or '-'}")
        print(f"  {r['transfers'] or 0} marked as transfers between your accounts")
        if r["balance"] is not None:
            print(f"  latest balance {_pounds(r['balance'])}")
    unmatched = conn.execute(
        """
        SELECT a.name, t.posted_on, t.amount_pence, t.description FROM transactions t
        JOIN accounts a ON a.id = t.account_id
        WHERE a.kind = 'isa' AND t.kind IN ('deposit', 'withdrawal') AND t.transfer_group IS NULL
        ORDER BY t.posted_on
        """
    ).fetchall()
    if unmatched:
        print("\nISA deposits/withdrawals with no matching Starling payment (normal for other sources):")
        for r in unmatched:
            print(f"  {r['posted_on']}  {_pounds(r['amount_pence']):>12}  {r['name']}: {r['description']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="budgetbuddy", description="Local joint finance dashboard")
    parser.add_argument("--data-dir", type=Path, default=None, help="where the database lives")
    sub = parser.add_subparsers(dest="command", required=True)

    p_import = sub.add_parser("import", help="import downloaded statements (files or folders)")
    p_import.add_argument("files", nargs="+")
    p_import.add_argument("--account", help='account name, e.g. "Vanguard ISA Olly" (Starling defaults to "Starling Joint")')
    p_import.add_argument("--owner", default="Joint", help="whose account it is (default Joint)")
    p_import.add_argument("--format", choices=sorted(PARSERS), help="force a file format instead of detecting it")
    p_import.set_defaults(func=cmd_import)

    p_status = sub.add_parser("status", help="show accounts, date ranges and unmatched transfers")
    p_status.set_defaults(func=cmd_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    data_dir = args.data_dir or default_data_dir()
    conn = connect(data_dir)
    try:
        return args.func(args, conn, data_dir)
    finally:
        conn.close()

"""Command line entry point: python -m budgetbuddy <command>."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from budgetbuddy import categorise as cat
from budgetbuddy.db import connect, default_data_dir
from budgetbuddy.importer import import_file
from budgetbuddy.models import parse_date
from budgetbuddy.parsers import PARSERS
from budgetbuddy.valuations import import_values, isa_summaries, record_value

STATEMENT_SUFFIXES = {".csv", ".txt", ".xlsx", ".xlsm"}


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
        if r["n"] == 0:
            continue
        print(f"  {r['n']} cash transactions, {r['first'] or '-'} to {r['last'] or '-'}")
        print(f"  {r['transfers'] or 0} marked as transfers between your accounts")
        if r["balance"] is not None:
            print(f"  latest balance {_pounds(r['balance'])}")
    isas = isa_summaries(conn)
    if isas:
        print("\nISAs:")
        total = 0
        for i in isas:
            if i.value_pence is None:
                print(f"  {i.account}: no value recorded yet (python -m budgetbuddy value \"{i.account}\" <amount>)")
                continue
            total += i.value_pence
            print(
                f"  {i.account}: {_pounds(i.value_pence)} on {i.valued_on}, "
                f"net invested {_pounds(i.invested_pence)}, growth {_pounds(i.growth_pence)}"
            )
        if total:
            print(f"  Total ISA value {_pounds(total)}")
    (waiting,) = conn.execute("SELECT COUNT(*) FROM transactions WHERE category = ?", (cat.UNCATEGORISED,)).fetchone()
    if waiting:
        print(f"\n{waiting} transactions need a category: python -m budgetbuddy uncategorised")
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


def cmd_value(args: argparse.Namespace, conn: sqlite3.Connection, data_dir: Path) -> int:
    if args.file:
        print(f"Recorded {import_values(conn, args.file)} values from {args.file.name}")
        return 0
    if not (args.account and args.amount):
        print('Give an account and amount, e.g. value "Vanguard ISA A" 12450.00, or --file', file=sys.stderr)
        return 2
    on = parse_date(args.date) if args.date else None
    record_value(conn, args.account, args.amount, on)
    print(f"Recorded {args.account} = £{args.amount}" + (f" on {on.isoformat()}" if on else " today"))
    return 0


def cmd_uncategorised(args: argparse.Namespace, conn: sqlite3.Connection, data_dir: Path) -> int:
    groups = cat.uncategorised(conn)
    if not groups:
        print("Everything has a category.")
        return 0
    print("Needs a category (biggest first). Fix with: python -m budgetbuddy rule \"<merchant>\" <category>\n")
    for g in groups:
        print(f"  {_pounds(g.total_pence):>12}  x{g.count:<3} {g.merchant}")
    print(f"\nCategories: {', '.join(c for c in cat.CATEGORIES if c != cat.UNCATEGORISED)}")
    return 0


def cmd_rule(args: argparse.Namespace, conn: sqlite3.Connection, data_dir: Path) -> int:
    if args.delete is not None:
        cat.delete_rule(conn, args.delete)
        print(f"Deleted rule {args.delete}")
        return 0
    if not (args.pattern and args.category):
        rules = conn.execute("SELECT id, match, pattern, category FROM rules ORDER BY id").fetchall()
        if not rules:
            print('No rules yet. Add one: python -m budgetbuddy rule "Premier Vet Alliance" Pets')
        for r in rules:
            how = "merchant is" if r["match"] == "merchant" else "text contains"
            print(f"  [{r['id']}] {how} '{r['pattern']}' -> {r['category']}")
        return 0
    category, changed = cat.add_rule(conn, args.pattern, args.category, contains=args.contains)
    new = "" if category in cat.CATEGORIES else " (new category)"
    print(f"Rule saved: {args.pattern} -> {category}{new}. {changed} transactions updated.")
    return 0


def cmd_recategorise(args: argparse.Namespace, conn: sqlite3.Connection, data_dir: Path) -> int:
    category = cat.set_transaction_category(conn, args.id, args.category)
    print(f"Transaction {args.id} -> {category} (this one only)")
    return 0


def cmd_transactions(args: argparse.Namespace, conn: sqlite3.Connection, data_dir: Path) -> int:
    sql = """
        SELECT t.id, t.posted_on, t.amount_pence, t.merchant, t.category, t.category_source
        FROM transactions t JOIN accounts a ON a.id = t.account_id WHERE a.kind = 'bank'
    """
    params: list[object] = []
    if args.month:
        sql += " AND substr(t.posted_on, 1, 7) = ?"
        params.append(args.month)
    if args.category:
        sql += " AND t.category = ? COLLATE NOCASE"
        params.append(args.category)
    if args.search:
        sql += " AND (t.merchant LIKE ? OR t.counterparty LIKE ? OR t.reference LIKE ?)"
        params.extend([f"%{args.search}%"] * 3)
    sql += " ORDER BY t.posted_on, t.id"
    for r in conn.execute(sql, params):
        print(f"  [{r['id']:>5}] {r['posted_on']}  {_pounds(r['amount_pence']):>12}  {r['merchant']:<30} {r['category']} ({r['category_source']})")
    return 0


def cmd_spending(args: argparse.Namespace, conn: sqlite3.Connection, data_dir: Path) -> int:
    rows = cat.spending_by_category(conn, args.month)
    if not rows:
        print("No spending found" + (f" for {args.month}" if args.month else ""))
        return 0
    total = sum(spent for _, spent, _ in rows)
    print(f"Spending {'in ' + args.month if args.month else 'all time'} (transfers to your ISAs left out)\n")
    for category, spent, n in rows:
        share = spent / total * 100 if total else 0
        print(f"  {category:<24} {_pounds(spent):>12}  {share:5.1f}%  ({n})")
    print(f"  {'Total':<24} {_pounds(total):>12}")
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

    p_value = sub.add_parser("value", help="record an ISA's current value from the Vanguard summary page")
    p_value.add_argument("account", nargs="?")
    p_value.add_argument("amount", nargs="?")
    p_value.add_argument("--date", help="dd/mm/yyyy (default today)")
    p_value.add_argument("--file", type=Path, help="CSV with Date, Account, Value columns")
    p_value.set_defaults(func=cmd_value)

    p_unc = sub.add_parser("uncategorised", help="list merchants that still need a category")
    p_unc.set_defaults(func=cmd_uncategorised)

    p_rule = sub.add_parser("rule", help="teach a category for a merchant; with no arguments, list rules")
    p_rule.add_argument("pattern", nargs="?", help="merchant name as shown by uncategorised/transactions")
    p_rule.add_argument("category", nargs="?")
    p_rule.add_argument("--contains", action="store_true", help="match any payee or reference containing the text")
    p_rule.add_argument("--delete", type=int, metavar="ID", help="delete a rule by id")
    p_rule.set_defaults(func=cmd_rule)

    p_recat = sub.add_parser("recategorise", help="set the category of one transaction only")
    p_recat.add_argument("id", type=int)
    p_recat.add_argument("category")
    p_recat.set_defaults(func=cmd_recategorise)

    p_txn = sub.add_parser("transactions", help="list bank transactions with their ids and categories")
    p_txn.add_argument("--month", help="YYYY-MM")
    p_txn.add_argument("--category")
    p_txn.add_argument("--search", help="text in merchant, payee or reference")
    p_txn.set_defaults(func=cmd_transactions)

    p_spend = sub.add_parser("spending", help="spending by category")
    p_spend.add_argument("--month", help="YYYY-MM")
    p_spend.set_defaults(func=cmd_spending)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    data_dir = args.data_dir or default_data_dir()
    conn = connect(data_dir)
    try:
        return args.func(args, conn, data_dir)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()

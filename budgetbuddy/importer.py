"""Import downloaded statements: parse, archive, remove duplicates, store, link transfers."""

from __future__ import annotations

import hashlib
import shutil
import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from budgetbuddy.categorise import categorise_all
from budgetbuddy.db import get_or_create_account
from budgetbuddy.parsers import parse_file
from budgetbuddy.recurring import refresh as refresh_recurring
from budgetbuddy.transfers import link_transfers

DEFAULT_ACCOUNT_NAMES = {"starling": "Starling Joint"}


@dataclass
class ImportResult:
    file_name: str
    account: str
    parser: str
    rows_read: int = 0
    rows_added: int = 0
    duplicates: int = 0
    skipped_file: bool = False
    transfers_linked: int = 0
    warnings: list[str] = field(default_factory=list)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _new_items(conn: sqlite3.Connection, table: str, account_id: int, items: list) -> list:
    """Keep only items not already stored.

    Overlapping downloads repeat transactions, but two identical coffees on
    the same day are real. So for each fingerprint we keep as many as the file
    has beyond what the database already holds.
    """
    in_file = Counter(item.fingerprint() for item in items)
    already: dict[str, int] = {}
    for fp in in_file:
        (count,) = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE account_id = ? AND fingerprint = ?", (account_id, fp)
        ).fetchone()
        already[fp] = count
    fresh = []
    for item in items:
        fp = item.fingerprint()
        if already[fp] > 0:
            already[fp] -= 1
        else:
            fresh.append(item)
    return fresh


def import_file(
    conn: sqlite3.Connection,
    path: Path,
    data_dir: Path,
    account: str | None = None,
    owner: str = "Joint",
    fmt: str | None = None,
) -> ImportResult:
    statement = parse_file(path, fmt)
    if account is None:
        account = DEFAULT_ACCOUNT_NAMES.get(statement.parser)
        if account is None:
            raise ValueError(
                f"{path.name}: say which account this is with --account "
                '(e.g. --account "Vanguard ISA Olly" --owner Olly)'
            )
    result = ImportResult(file_name=path.name, account=account, parser=statement.parser)
    result.warnings.extend(statement.warnings)
    result.rows_read = len(statement.transactions) + len(statement.trades)

    with conn:
        account_id = get_or_create_account(conn, account, statement.account_kind, statement.provider, owner)
        digest = _sha256(path)
        if conn.execute(
            "SELECT 1 FROM imports WHERE account_id = ? AND sha256 = ?", (account_id, digest)
        ).fetchone():
            result.skipped_file = True
            return result

        archive_dir = data_dir / "raw" / statement.parser
        archive_dir.mkdir(parents=True, exist_ok=True)
        archived = archive_dir / f"{digest[:12]}_{path.name}"
        shutil.copy2(path, archived)

        txns = _new_items(conn, "transactions", account_id, statement.transactions)
        trades = _new_items(conn, "investment_trades", account_id, statement.trades)
        result.rows_added = len(txns) + len(trades)
        result.duplicates = result.rows_read - result.rows_added

        import_id = conn.execute(
            "INSERT INTO imports (account_id, file_name, sha256, parser, rows_read, rows_added, archived_path)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (account_id, path.name, digest, statement.parser, result.rows_read, result.rows_added, str(archived)),
        ).lastrowid
        conn.executemany(
            "INSERT INTO transactions (account_id, import_id, posted_on, amount_pence, description,"
            " counterparty, reference, txn_type, source_category, notes, balance_pence, kind, fingerprint)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    account_id, import_id, t.posted_on.isoformat(), t.amount_pence, t.description,
                    t.counterparty, t.reference, t.txn_type, t.source_category, t.notes,
                    t.balance_pence, t.kind, t.fingerprint(),
                )
                for t in txns
            ],
        )
        conn.executemany(
            "INSERT INTO investment_trades (account_id, import_id, traded_on, fund, details, quantity,"
            " price, cost_pence, fingerprint) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    account_id, import_id, t.traded_on.isoformat(), t.fund, t.details,
                    str(t.quantity), str(t.price), t.cost_pence, t.fingerprint(),
                )
                for t in trades
            ],
        )
        result.transfers_linked = link_transfers(conn)
    categorise_all(conn)
    refresh_recurring(conn)
    return result

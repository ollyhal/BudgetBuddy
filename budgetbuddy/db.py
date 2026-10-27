"""SQLite storage. One file on your own disk; nothing is sent anywhere."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id        INTEGER PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE,
    kind      TEXT NOT NULL CHECK (kind IN ('bank', 'isa')),
    provider  TEXT NOT NULL,
    owner     TEXT NOT NULL DEFAULT 'Joint'
);

CREATE TABLE IF NOT EXISTS imports (
    id            INTEGER PRIMARY KEY,
    account_id    INTEGER NOT NULL REFERENCES accounts(id),
    file_name     TEXT NOT NULL,
    sha256        TEXT NOT NULL,
    parser        TEXT NOT NULL,
    imported_at   TEXT NOT NULL DEFAULT (datetime('now')),
    rows_read     INTEGER NOT NULL,
    rows_added    INTEGER NOT NULL,
    archived_path TEXT,
    UNIQUE (account_id, sha256)
);

CREATE TABLE IF NOT EXISTS transactions (
    id              INTEGER PRIMARY KEY,
    account_id      INTEGER NOT NULL REFERENCES accounts(id),
    import_id       INTEGER NOT NULL REFERENCES imports(id),
    posted_on       TEXT NOT NULL,
    amount_pence    INTEGER NOT NULL,
    description     TEXT NOT NULL,
    counterparty    TEXT NOT NULL DEFAULT '',
    reference       TEXT NOT NULL DEFAULT '',
    txn_type        TEXT NOT NULL DEFAULT '',
    source_category TEXT NOT NULL DEFAULT '',
    notes           TEXT NOT NULL DEFAULT '',
    balance_pence   INTEGER,
    kind            TEXT,
    fingerprint     TEXT NOT NULL,
    category        TEXT,
    is_transfer     INTEGER NOT NULL DEFAULT 0,
    transfer_group  INTEGER
);
CREATE INDEX IF NOT EXISTS ix_txn_account_fp ON transactions (account_id, fingerprint);
CREATE INDEX IF NOT EXISTS ix_txn_date ON transactions (posted_on);

CREATE TABLE IF NOT EXISTS investment_trades (
    id           INTEGER PRIMARY KEY,
    account_id   INTEGER NOT NULL REFERENCES accounts(id),
    import_id    INTEGER NOT NULL REFERENCES imports(id),
    traded_on    TEXT NOT NULL,
    fund         TEXT NOT NULL,
    details      TEXT NOT NULL,
    quantity     TEXT NOT NULL,
    price        TEXT NOT NULL,
    cost_pence   INTEGER NOT NULL,
    fingerprint  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_trade_account_fp ON investment_trades (account_id, fingerprint);
"""


def default_data_dir() -> Path:
    """Where the database and archived statements live.

    Override with the BUDGETBUDDY_DATA environment variable. The default is a
    folder in your user profile, outside the git repository, e.g.
    C:\\Users\\<you>\\BudgetBuddyData on Windows.
    """
    env = os.environ.get("BUDGETBUDDY_DATA")
    return Path(env) if env else Path.home() / "BudgetBuddyData"


def connect(data_dir: Path) -> sqlite3.Connection:
    data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(data_dir / "budgetbuddy.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    return conn


def get_or_create_account(
    conn: sqlite3.Connection, name: str, kind: str, provider: str, owner: str = "Joint"
) -> int:
    row = conn.execute("SELECT id, kind FROM accounts WHERE name = ?", (name,)).fetchone()
    if row is not None:
        if row["kind"] != kind:
            raise ValueError(f"Account {name!r} is a {row['kind']} account, but this file is {kind}")
        return row["id"]
    cur = conn.execute(
        "INSERT INTO accounts (name, kind, provider, owner) VALUES (?, ?, ?, ?)",
        (name, kind, provider, owner),
    )
    return cur.lastrowid

"""SQLite storage. One file on your own disk; nothing is sent anywhere."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

SCHEMA_VERSION = 3

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
    merchant        TEXT,
    category        TEXT,
    -- transfer, manual, rule, builtin, starling, fallback (how category was chosen)
    category_source TEXT,
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

-- Your own categorisation rules; they beat the built in ones
CREATE TABLE IF NOT EXISTS rules (
    id         INTEGER PRIMARY KEY,
    match      TEXT NOT NULL CHECK (match IN ('merchant', 'contains')),
    pattern    TEXT NOT NULL,
    category   TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (match, pattern)
);

-- Monthly ISA values typed in from the Vanguard summary page
CREATE TABLE IF NOT EXISTS valuations (
    id          INTEGER PRIMARY KEY,
    account_id  INTEGER NOT NULL REFERENCES accounts(id),
    valued_on   TEXT NOT NULL,
    value_pence INTEGER NOT NULL,
    UNIQUE (account_id, valued_on)
);

-- Regular payments and income, detected from history or added by hand.
-- user_status and amount_override_pence are yours and survive re-detection.
CREATE TABLE IF NOT EXISTS recurring (
    id                    INTEGER PRIMARY KEY,
    key                   TEXT UNIQUE,
    source                TEXT NOT NULL CHECK (source IN ('detected', 'manual')),
    name                  TEXT NOT NULL,
    category              TEXT,
    frequency             TEXT NOT NULL,
    amount_pence          INTEGER NOT NULL,
    previous_amount_pence INTEGER,
    variable              INTEGER NOT NULL DEFAULT 0,
    occurrences           INTEGER NOT NULL DEFAULT 0,
    last_seen             TEXT,
    next_due              TEXT,
    status                TEXT NOT NULL DEFAULT 'active',
    user_status           TEXT CHECK (user_status IN ('ignored', 'ended')),
    amount_override_pence INTEGER
);
"""

# Columns added after version 1, for databases created before them
_ADDED_COLUMNS = {
    "transactions": (("merchant", "TEXT"), ("category_source", "TEXT")),
}


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
    for table, columns in _ADDED_COLUMNS.items():
        if conn.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (table,)).fetchone():
            existing = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
            for name, sql_type in columns:
                if name not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}")
    conn.executescript(SCHEMA)
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    return conn


def find_account(conn: sqlite3.Connection, name: str) -> sqlite3.Row:
    """Look up an account by name, ignoring case, with a helpful error."""
    row = conn.execute("SELECT * FROM accounts WHERE name = ? COLLATE NOCASE", (name,)).fetchone()
    if row is None:
        names = ", ".join(r["name"] for r in conn.execute("SELECT name FROM accounts ORDER BY name"))
        raise ValueError(f"No account called {name!r}. Accounts: {names or 'none yet'}")
    return row


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

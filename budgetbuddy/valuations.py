"""ISA values, recorded by hand once a month from the Vanguard summary page.

The orders list says what was bought; only Vanguard knows what it is worth
today, so a monthly value is enough for net worth and growth.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from budgetbuddy.db import find_account
from budgetbuddy.models import parse_date, parse_pence
from budgetbuddy.parsers.common import is_blank_row, map_columns, read_csv_rows

ALIASES = {"date": ("date",), "account": ("account",), "value": ("value", "valuegbp")}


def record_value(conn: sqlite3.Connection, account: str, value: object, on: dt.date | None = None) -> None:
    row = find_account(conn, account)
    if row["kind"] != "isa":
        raise ValueError(f"{row['name']} is a bank account; its balance comes from the statement")
    pence = parse_pence(value)
    if pence is None:
        raise ValueError("No value given")
    with conn:
        conn.execute(
            "INSERT INTO valuations (account_id, valued_on, value_pence) VALUES (?, ?, ?)"
            " ON CONFLICT (account_id, valued_on) DO UPDATE SET value_pence = excluded.value_pence",
            (row["id"], (on or dt.date.today()).isoformat(), pence),
        )


def import_values(conn: sqlite3.Connection, path: Path) -> int:
    """Load a Date, Account, Value file. Returns the number of values recorded."""
    rows = read_csv_rows(path)
    if not rows:
        raise ValueError(f"{path.name} is empty")
    columns = map_columns(rows[0], ALIASES)
    if set(columns) != set(ALIASES):
        raise ValueError(f"{path.name}: expected columns Date, Account, Value")
    count = 0
    for row in rows[1:]:
        if is_blank_row(row):
            continue
        record_value(
            conn, row[columns["account"]].strip(), row[columns["value"]], parse_date(row[columns["date"]])
        )
        count += 1
    return count


@dataclass
class IsaSummary:
    account: str
    owner: str
    value_pence: int | None
    valued_on: str | None
    invested_pence: int

    @property
    def growth_pence(self) -> int | None:
        return None if self.value_pence is None else self.value_pence - self.invested_pence


def isa_summaries(conn: sqlite3.Connection) -> list[IsaSummary]:
    """Latest value and net amount put into funds (buys less sells) per ISA."""
    out = []
    for acc in conn.execute("SELECT id, name, owner FROM accounts WHERE kind = 'isa' ORDER BY name"):
        latest = conn.execute(
            "SELECT valued_on, value_pence FROM valuations WHERE account_id = ? ORDER BY valued_on DESC LIMIT 1",
            (acc["id"],),
        ).fetchone()
        (invested,) = conn.execute(
            "SELECT COALESCE(SUM(cost_pence), 0) FROM investment_trades WHERE account_id = ?", (acc["id"],)
        ).fetchone()
        out.append(
            IsaSummary(
                account=acc["name"],
                owner=acc["owner"],
                value_pence=latest["value_pence"] if latest else None,
                valued_on=latest["valued_on"] if latest else None,
                invested_pence=invested,
            )
        )
    return out

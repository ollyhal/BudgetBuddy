"""Find regular income and payments: salaries, direct debits, subscriptions,
ISA standing orders. These are the backbone of the cash forecast.

A merchant counts as recurring when its payments arrive at a steady interval
(weekly, fortnightly, four weekly, monthly, quarterly or yearly). When one
merchant mixes regular and one-off payments (Amazon Prime among Amazon
orders, or two different ISA standing orders to Vanguard), payments of the
same exact amount are tested on their own.
"""

from __future__ import annotations

import calendar
import datetime as dt
import sqlite3
import statistics
from collections import defaultdict
from dataclasses import dataclass

from budgetbuddy.categorise import TRANSFERS

# name: (lowest median gap, highest median gap, allowed spread per gap in days, payments per year)
FREQUENCIES: dict[str, tuple[float, float, int, float]] = {
    "weekly": (6, 8, 2, 52),
    "fortnightly": (13, 15, 2, 26),
    "four weekly": (27.5, 28.5, 1, 13),
    "monthly": (26, 35, 5, 12),
    "quarterly": (84, 98, 10, 4),
    "yearly": (350, 380, 15, 1),
}
PER_YEAR = {name: spec[3] for name, spec in FREQUENCIES.items()}

# Starling payment types that are regular by nature, so two payments are enough
_SCHEDULED_TYPES = ("DIRECT DEBIT", "STANDING ORDER")
VARIABLE_SPREAD = 0.10


@dataclass
class Detected:
    key: str
    name: str
    category: str | None
    frequency: str
    amount_pence: int
    previous_amount_pence: int | None
    variable: bool
    occurrences: int
    last_seen: dt.date
    next_due: dt.date
    status: str


def _add_months(day: dt.date, months: int, day_of_month: int) -> dt.date:
    month_index = day.month - 1 + months
    year, month = day.year + month_index // 12, month_index % 12 + 1
    return dt.date(year, month, min(day_of_month, calendar.monthrange(year, month)[1]))


def next_after(last: dt.date, frequency: str, day_of_month: int | None = None) -> dt.date:
    """The next due date after `last` for a given frequency."""
    if frequency == "monthly":
        return _add_months(last, 1, day_of_month or last.day)
    if frequency == "quarterly":
        return _add_months(last, 3, day_of_month or last.day)
    if frequency == "yearly":
        return _add_months(last, 12, day_of_month or last.day)
    return last + dt.timedelta(days=round(365.25 / PER_YEAR[frequency]))


def _frequency(dates: list[dt.date]) -> str | None:
    gaps = [(b - a).days for a, b in zip(dates, dates[1:])]
    if not gaps or min(gaps) <= 0:
        return None
    median = statistics.median(gaps)
    for name, (low, high, spread, _) in FREQUENCIES.items():
        if not low <= median <= high:
            continue
        steady = sum(1 for g in gaps if abs(g - median) <= spread)
        if steady / len(gaps) >= 0.75:
            return name
    return None


def _analyse(key: str, rows: list[sqlite3.Row], data_end: dt.date) -> Detected | None:
    rows = sorted(rows, key=lambda r: (r["posted_on"], r["id"]))
    dates = [dt.date.fromisoformat(r["posted_on"]) for r in rows]
    scheduled = any(r["txn_type"].upper() in _SCHEDULED_TYPES for r in rows)
    frequency = _frequency(dates)
    if frequency is None:
        return None
    minimum = 2 if frequency == "yearly" or scheduled else 3
    if len(rows) < minimum:
        return None

    amounts = [r["amount_pence"] for r in rows]
    recent = amounts[-3:]
    median = statistics.median(amounts)
    # A price rise is one clean step between fixed amounts (10.99, 10.99, 12.99, 12.99),
    # not a bill that varies every time
    runs = [a for i, a in enumerate(amounts) if i == 0 or a != amounts[i - 1]]
    stepped = len(runs) == len(set(runs)) <= 3 and len(runs) < len(amounts)
    variable = not stepped and (max(amounts) - min(amounts)) > abs(median) * VARIABLE_SPREAD
    # Fixed payments use the latest amount (so price rises carry forward); variable bills average recently
    amount = round(statistics.mean(recent)) if variable else amounts[-1]
    previous = next((a for a in reversed(amounts[:-1]) if a != amounts[-1]), None)

    day_of_month = round(statistics.median(d.day for d in dates))
    next_due = next_after(dates[-1], frequency, day_of_month)
    allowed_gap = 365.25 / PER_YEAR[frequency] * 1.5 + 5
    status = "active" if (data_end - dates[-1]).days <= allowed_gap else "lapsed"
    categories = [r["category"] for r in rows if r["category"]]
    return Detected(
        key=key,
        name=rows[-1]["merchant"],
        category=statistics.mode(categories) if categories else None,
        frequency=frequency,
        amount_pence=amount,
        previous_amount_pence=None if variable else previous,
        variable=variable,
        occurrences=len(rows),
        last_seen=dates[-1],
        next_due=next_due,
        status=status,
    )


def detect(conn: sqlite3.Connection) -> list[Detected]:
    rows = conn.execute(
        """
        SELECT t.id, t.posted_on, t.amount_pence, t.merchant, t.category, t.txn_type
        FROM transactions t JOIN accounts a ON a.id = t.account_id
        WHERE a.kind = 'bank' AND t.merchant IS NOT NULL
        """
    ).fetchall()
    if not rows:
        return []
    data_end = max(dt.date.fromisoformat(r["posted_on"]) for r in rows)
    groups: dict[tuple[str, bool], list[sqlite3.Row]] = defaultdict(list)
    for r in rows:
        groups[(r["merchant"].casefold(), r["amount_pence"] > 0)].append(r)

    found: list[Detected] = []
    for (merchant, money_in), group in groups.items():
        direction = "in" if money_in else "out"
        result = _analyse(f"{merchant}|{direction}", group, data_end)
        if result is not None:
            found.append(result)
            continue
        by_amount: dict[int, list[sqlite3.Row]] = defaultdict(list)
        for r in group:
            by_amount[r["amount_pence"]].append(r)
        if len(by_amount) < 2:
            continue
        for amount, same in by_amount.items():
            result = _analyse(f"{merchant}|{direction}|{amount}", same, data_end)
            if result is not None:
                found.append(result)
    return found


def refresh(conn: sqlite3.Connection) -> int:
    """Re-detect and save, keeping your ignore/end choices and amount overrides.

    Returns the number of recurring items found this time.
    """
    found = detect(conn)
    keys = [d.key for d in found]
    with conn:
        for d in found:
            conn.execute(
                """
                INSERT INTO recurring (key, source, name, category, frequency, amount_pence,
                    previous_amount_pence, variable, occurrences, last_seen, next_due, status)
                VALUES (?, 'detected', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (key) DO UPDATE SET
                    name = excluded.name, category = excluded.category, frequency = excluded.frequency,
                    amount_pence = excluded.amount_pence,
                    previous_amount_pence = excluded.previous_amount_pence,
                    variable = excluded.variable, occurrences = excluded.occurrences,
                    last_seen = excluded.last_seen, next_due = excluded.next_due, status = excluded.status
                """,
                (
                    d.key, d.name, d.category, d.frequency, d.amount_pence, d.previous_amount_pence,
                    int(d.variable), d.occurrences, d.last_seen.isoformat(), d.next_due.isoformat(), d.status,
                ),
            )
        # Detected before but not now (e.g. the pattern broke): keep it, but as lapsed
        placeholders = ",".join("?" * len(keys)) or "''"
        conn.execute(
            f"UPDATE recurring SET status = 'lapsed' WHERE source = 'detected' AND key NOT IN ({placeholders})",
            keys,
        )
    return len(found)


def add_manual(
    conn: sqlite3.Connection, name: str, amount_pence: int, frequency: str, next_due: dt.date,
    category: str | None = None,
) -> int:
    """Add something history cannot show yet, e.g. annual car insurance (amount negative for money out)."""
    if frequency not in FREQUENCIES:
        raise ValueError(f"Frequency must be one of: {', '.join(FREQUENCIES)}")
    with conn:
        return conn.execute(
            "INSERT INTO recurring (source, name, category, frequency, amount_pence, next_due)"
            " VALUES ('manual', ?, ?, ?, ?, ?)",
            (name, category, frequency, amount_pence, next_due.isoformat()),
        ).lastrowid


def set_user_status(conn: sqlite3.Connection, item_id: int, user_status: str | None) -> None:
    with conn:
        if conn.execute("UPDATE recurring SET user_status = ? WHERE id = ?", (user_status, item_id)).rowcount == 0:
            raise ValueError(f"No recurring item with id {item_id}")


def set_amount(conn: sqlite3.Connection, item_id: int, amount_pence: int | None) -> None:
    with conn:
        if conn.execute(
            "UPDATE recurring SET amount_override_pence = ? WHERE id = ?", (amount_pence, item_id)
        ).rowcount == 0:
            raise ValueError(f"No recurring item with id {item_id}")


def items(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """All recurring items with the amount and status that should actually be used."""
    return conn.execute(
        """
        SELECT *, COALESCE(amount_override_pence, amount_pence) AS use_amount,
               COALESCE(user_status, status) AS use_status
        FROM recurring ORDER BY COALESCE(amount_override_pence, amount_pence) DESC
        """
    ).fetchall()


def monthly_equivalent(amount_pence: int, frequency: str) -> int:
    return round(amount_pence * PER_YEAR[frequency] / 12)


def group_of(item: sqlite3.Row) -> str:
    if item["category"] == TRANSFERS:
        return "Savings & ISAs"
    if item["use_amount"] > 0:
        return "Income"
    if item["category"] == "Subscriptions":
        return "Subscriptions"
    return "Bills & regular payments"

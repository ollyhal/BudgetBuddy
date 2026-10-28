"""Assign a spending category to every bank transaction.

Order of precedence, first match wins:
  1. transfer   money moving between your own accounts
  2. manual     a one-off category you set on a single transaction
  3. rule       your own rules (learned from your corrections)
  4. builtin    keyword rules shipped with BudgetBuddy
  5. starling   Starling's own Spending Category
  6. fallback   money in becomes Income, anything else Uncategorised
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from budgetbuddy.merchants import clean_merchant

UNCATEGORISED = "Uncategorised"
TRANSFERS = "Transfers"

CATEGORIES = (
    "Income",
    "Mortgage",
    "Council Tax",
    "Bills & Utilities",
    "Insurance",
    "Groceries",
    "Eating Out",
    "Transport",
    "Subscriptions",
    "Shopping",
    "Home",
    "Pets",
    "Health",
    "Personal Care",
    "Entertainment",
    "Holidays",
    "Family",
    "Gifts & Charity",
    "Cash",
    "Fees & Interest",
    "Savings & Investments",
    TRANSFERS,
    "Other",
    UNCATEGORISED,
)

STARLING_MAP = {
    "INCOME": "Income",
    "MORTGAGE": "Mortgage",
    "BILLS_AND_SERVICES": "Bills & Utilities",
    "GROCERIES": "Groceries",
    "EATING_OUT": "Eating Out",
    "TRANSPORT": "Transport",
    "SHOPPING": "Shopping",
    "HOME": "Home",
    "PETS": "Pets",
    "PERSONAL_CARE": "Personal Care",
    "LIFESTYLE": "Personal Care",
    "ENTERTAINMENT": "Entertainment",
    "HOLIDAYS": "Holidays",
    "FAMILY": "Family",
    "GIFTS": "Gifts & Charity",
    "CHARITY": "Gifts & Charity",
    "SAVING": "Savings & Investments",
    "INVESTMENTS": "Savings & Investments",
    "TRANSFERS": TRANSFERS,
    "CASH": "Cash",
    # GENERAL, PAYMENTS, EXPENSES are too vague to trust
}

# (keyword found in merchant or reference, category); first match wins
BUILTIN_RULES: tuple[tuple[str, str], ...] = (
    ("council tax", "Council Tax"),
    ("council", "Council Tax"),
    ("tv licensing", "Bills & Utilities"),
    ("water", "Bills & Utilities"),
    ("e.on", "Bills & Utilities"),
    ("octopus energy", "Bills & Utilities"),
    ("british gas", "Bills & Utilities"),
    ("edf", "Bills & Utilities"),
    ("ovo", "Bills & Utilities"),
    ("bt group", "Bills & Utilities"),
    ("virgin media", "Bills & Utilities"),
    ("sky", "Bills & Utilities"),
    ("vodafone", "Bills & Utilities"),
    ("o2", "Bills & Utilities"),
    ("insurance", "Insurance"),
    ("aviva", "Insurance"),
    ("admiral", "Insurance"),
    ("direct line", "Insurance"),
    ("netflix", "Subscriptions"),
    ("spotify", "Subscriptions"),
    ("disney", "Subscriptions"),
    ("prime video", "Subscriptions"),
    ("amazon prime", "Subscriptions"),
    ("apple", "Subscriptions"),
    ("youtube", "Subscriptions"),
    ("gym", "Health"),
    ("pharmacy", "Health"),
    ("boots", "Health"),
    ("dentist", "Health"),
    ("vet", "Pets"),
    ("vets", "Pets"),
    ("pets at home", "Pets"),
    ("tesco", "Groceries"),
    ("sainsbury", "Groceries"),
    ("asda", "Groceries"),
    ("morrisons", "Groceries"),
    ("waitrose", "Groceries"),
    ("lidl", "Groceries"),
    ("aldi", "Groceries"),
    ("ocado", "Groceries"),
    ("co-op", "Groceries"),
    ("costa", "Eating Out"),
    ("starbucks", "Eating Out"),
    ("pret", "Eating Out"),
    ("greggs", "Eating Out"),
    ("mcdonald", "Eating Out"),
    ("deliveroo", "Eating Out"),
    ("just eat", "Eating Out"),
    ("uber eats", "Eating Out"),
    ("uber", "Transport"),
    ("trainline", "Transport"),
    ("tfl", "Transport"),
    ("shell", "Transport"),
    ("bp", "Transport"),
    ("esso", "Transport"),
    ("parking", "Transport"),
    ("dvla", "Transport"),
    ("amazon", "Shopping"),
    ("ikea", "Home"),
    ("b&q", "Home"),
    ("screwfix", "Home"),
    ("cash machine", "Cash"),
    ("atm", "Cash"),
)


# Built in keywords match whole words only, so "o2" or "vet" never fire inside
# a reference code or another word
_BUILTIN_PATTERNS = tuple(
    (re.compile(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"), category)
    for keyword, category in BUILTIN_RULES
)


def canonical_category(name: str) -> str:
    """Match a typed category to an existing one ignoring case; otherwise keep it as typed."""
    for known in CATEGORIES:
        if known.casefold() == name.strip().casefold():
            return known
    return name.strip()


def _haystack(merchant: str, counterparty: str, reference: str) -> str:
    return f" {merchant} {counterparty} {reference} ".casefold()


def choose_category(
    row: sqlite3.Row, merchant: str, user_rules: list[sqlite3.Row]
) -> tuple[str, str]:
    """Return (category, source) for one bank transaction."""
    if row["is_transfer"]:
        return TRANSFERS, "transfer"
    if row["category_source"] == "manual" and row["category"]:
        return row["category"], "manual"
    text = _haystack(merchant, row["counterparty"], row["reference"])
    for rule in user_rules:
        if rule["match"] == "merchant" and merchant.casefold() == rule["pattern"]:
            return rule["category"], "rule"
        if rule["match"] == "contains" and rule["pattern"] in text:
            return rule["category"], "rule"
    for pattern, category in _BUILTIN_PATTERNS:
        if pattern.search(text):
            return category, "builtin"
    starling = STARLING_MAP.get(row["source_category"].upper())
    if starling:
        return starling, "starling"
    if row["amount_pence"] > 0:
        return "Income", "fallback"
    return UNCATEGORISED, "fallback"


def categorise_all(conn: sqlite3.Connection) -> int:
    """(Re)categorise every bank transaction. Returns how many changed."""
    # Exact merchant rules first, then "contains" rules, newest first within each
    user_rules = conn.execute(
        "SELECT match, pattern, category FROM rules ORDER BY match = 'contains', id DESC"
    ).fetchall()
    rows = conn.execute(
        """
        SELECT t.id, t.counterparty, t.reference, t.source_category, t.amount_pence,
               t.is_transfer, t.category, t.category_source, t.merchant
        FROM transactions t JOIN accounts a ON a.id = t.account_id
        WHERE a.kind = 'bank'
        """
    ).fetchall()
    changed = 0
    with conn:
        for row in rows:
            merchant = clean_merchant(row["counterparty"], row["reference"])
            category, source = choose_category(row, merchant, user_rules)
            if (merchant, category, source) != (row["merchant"], row["category"], row["category_source"]):
                conn.execute(
                    "UPDATE transactions SET merchant = ?, category = ?, category_source = ? WHERE id = ?",
                    (merchant, category, source, row["id"]),
                )
                changed += 1
    return changed


def add_rule(conn: sqlite3.Connection, pattern: str, category: str, contains: bool = False) -> tuple[str, int]:
    """Teach BudgetBuddy a category for a merchant (or any text containing a word).

    Returns the category as stored and how many transactions changed.
    """
    category = canonical_category(category)
    match = "contains" if contains else "merchant"
    with conn:
        conn.execute(
            "INSERT INTO rules (match, pattern, category) VALUES (?, ?, ?)"
            " ON CONFLICT (match, pattern) DO UPDATE SET category = excluded.category",
            (match, pattern.strip().casefold(), category),
        )
    return category, categorise_all(conn)


def delete_rule(conn: sqlite3.Connection, rule_id: int) -> None:
    with conn:
        if conn.execute("DELETE FROM rules WHERE id = ?", (rule_id,)).rowcount == 0:
            raise ValueError(f"No rule with id {rule_id}")
    categorise_all(conn)


def set_transaction_category(conn: sqlite3.Connection, txn_id: int, category: str) -> str:
    """One-off category for a single transaction (e.g. a holiday paid on Amazon)."""
    category = canonical_category(category)
    with conn:
        if conn.execute(
            "UPDATE transactions SET category = ?, category_source = 'manual' WHERE id = ?",
            (category, txn_id),
        ).rowcount == 0:
            raise ValueError(f"No transaction with id {txn_id}")
    return category


@dataclass
class MerchantGroup:
    merchant: str
    count: int
    total_pence: int
    first_id: int


def uncategorised(conn: sqlite3.Connection) -> list[MerchantGroup]:
    """The review queue, biggest spend first so one rule fixes the most."""
    return [
        MerchantGroup(r["merchant"], r["n"], r["total"], r["first_id"])
        for r in conn.execute(
            """
            SELECT merchant, COUNT(*) AS n, SUM(amount_pence) AS total, MIN(id) AS first_id
            FROM transactions WHERE category = ?
            GROUP BY merchant ORDER BY SUM(ABS(amount_pence)) DESC
            """,
            (UNCATEGORISED,),
        )
    ]


def spending_by_category(conn: sqlite3.Connection, month: str | None = None) -> list[tuple[str, int, int]]:
    """(category, money out in pence as a positive number, count), transfers and income left out."""
    sql = """
        SELECT category, -SUM(amount_pence) AS spent, COUNT(*) AS n
        FROM transactions t JOIN accounts a ON a.id = t.account_id
        WHERE a.kind = 'bank' AND category NOT IN (?, 'Income')
    """
    params: list[object] = [TRANSFERS]
    if month:
        sql += " AND substr(posted_on, 1, 7) = ?"
        params.append(month)
    sql += " GROUP BY category ORDER BY spent DESC"
    return [(r["category"], r["spent"], r["n"]) for r in conn.execute(sql, params)]

"""Link money moving between your own accounts so it is never counted as spending.

A Starling payment of £500 to Vanguard and the matching £500 deposit in the
ISA's cash account become one transfer group.
"""

from __future__ import annotations

import datetime as dt
import sqlite3

MAX_DAYS_APART = 7

# Bank payee names that are always your own investment accounts
OWN_ACCOUNT_PAYEES = ("vanguard",)


def link_transfers(conn: sqlite3.Connection) -> int:
    """Pair bank outflows with ISA deposits (and ISA withdrawals with bank inflows).

    Returns the number of new pairs. Safe to run repeatedly.
    """
    unmatched = conn.execute(
        """
        SELECT t.id, t.posted_on, t.amount_pence, t.kind, t.counterparty, a.kind AS account_kind
        FROM transactions t JOIN accounts a ON a.id = t.account_id
        WHERE t.transfer_group IS NULL
        ORDER BY t.posted_on, t.id
        """
    ).fetchall()

    bank = [r for r in unmatched if r["account_kind"] == "bank"]
    isa = [r for r in unmatched if r["account_kind"] == "isa" and r["kind"] in ("deposit", "withdrawal")]
    used: set[int] = set()
    pairs = 0

    for isa_row in isa:
        isa_date = dt.date.fromisoformat(isa_row["posted_on"])
        best = None
        for bank_row in bank:
            if bank_row["id"] in used or bank_row["amount_pence"] != -isa_row["amount_pence"]:
                continue
            gap = (isa_date - dt.date.fromisoformat(bank_row["posted_on"])).days
            # Deposits land after the bank payment leaves; withdrawals the other way round
            if isa_row["kind"] == "withdrawal":
                gap = -gap
            if 0 <= gap <= MAX_DAYS_APART and (best is None or gap < best[0]):
                best = (gap, bank_row)
        if best is None:
            continue
        bank_row = best[1]
        used.add(bank_row["id"])
        conn.execute(
            "UPDATE transactions SET transfer_group = ?, is_transfer = 1 WHERE id IN (?, ?)",
            (isa_row["id"], isa_row["id"], bank_row["id"]),
        )
        pairs += 1

    # Payments to Vanguard with no matching ISA statement yet are still transfers
    for row in bank:
        if row["id"] in used:
            continue
        if any(p in row["counterparty"].casefold() for p in OWN_ACCOUNT_PAYEES):
            conn.execute("UPDATE transactions SET is_transfer = 1 WHERE id = ?", (row["id"],))
    return pairs

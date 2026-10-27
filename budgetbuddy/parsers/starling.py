"""Starling Bank CSV statement export.

Starling's export columns are:
Date, Counter Party, Reference, Type, Amount (GBP), Balance (GBP), Spending Category, Notes
Dates are day first (dd/mm/yyyy). Money out is negative.
"""

from __future__ import annotations

import re
from pathlib import Path

from budgetbuddy.models import ParsedStatement, Transaction, normalise_text, parse_date, parse_pence
from budgetbuddy.parsers.common import cell, is_blank_row, map_columns, read_csv_rows

NAME = "starling"

ALIASES: dict[str, tuple[str, ...]] = {
    "date": ("date", "transactiondate"),
    "counterparty": ("counterparty", "payee", "name"),
    "reference": ("reference", "description"),
    "type": ("type", "transactiontype"),
    "amount": ("amountgbp", "amount"),
    "balance": ("balancegbp", "balance"),
    "category": ("spendingcategory", "category"),
    "notes": ("notes",),
}

REQUIRED = ("date", "counterparty", "amount")

# A long reference that Excel rewrote, e.g. 4E+15
_EXCEL_MANGLED = re.compile(r"^\d(\.\d+)?E\+\d+$", re.IGNORECASE)


def _find_header(rows: list[list[str]]) -> tuple[int, dict[str, int]] | None:
    for index, row in enumerate(rows[:10]):
        columns = map_columns(row, ALIASES)
        if all(f in columns for f in REQUIRED):
            return index, columns
    return None


def can_parse(path: Path) -> bool:
    if path.suffix.lower() != ".csv":
        return False
    try:
        rows = read_csv_rows(path)
    except (OSError, ValueError):
        return False
    found = _find_header(rows)
    # "Counter Party" plus "Spending Category" is distinctive to Starling
    return found is not None and "category" in found[1]


def parse(path: Path) -> ParsedStatement:
    rows = read_csv_rows(path)
    found = _find_header(rows)
    if found is None:
        raise ValueError(f"{path.name}: no Starling header row (Date, Counter Party, Amount) found")
    header_index, columns = found
    statement = ParsedStatement(parser=NAME, account_kind="bank", provider="Starling")
    excel_warned = False

    for line_no, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
        if is_blank_row(row):
            continue
        counterparty = normalise_text(cell(row, columns, "counterparty"))
        amount = parse_pence(cell(row, columns, "amount"))
        if amount is None:
            # Starling puts an "Opening Balance" line with no amount at the top
            if counterparty.casefold() != "opening balance":
                statement.warnings.append(f"line {line_no}: no amount, skipped")
            continue
        reference = normalise_text(cell(row, columns, "reference"))
        if _EXCEL_MANGLED.match(reference) and not excel_warned:
            statement.warnings.append(
                f"line {line_no}: reference {reference!r} looks rewritten by Excel; "
                "import the CSV straight from Starling rather than a copy saved in Excel"
            )
            excel_warned = True
        statement.transactions.append(
            Transaction(
                posted_on=parse_date(cell(row, columns, "date")),
                amount_pence=amount,
                description=counterparty or reference,
                counterparty=counterparty,
                reference=reference,
                txn_type=normalise_text(cell(row, columns, "type")),
                source_category=normalise_text(cell(row, columns, "category")),
                notes=normalise_text(cell(row, columns, "notes")),
                balance_pence=parse_pence(cell(row, columns, "balance")),
            )
        )
    return statement

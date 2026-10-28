"""Vanguard Investor UK orders list, copied from the website.

On the Vanguard site's orders/transactions page, select the table, copy it
and paste it into Notepad, then save as e.g. vanguard_a_orders.txt. Columns:

  Investment | Date | Order type | Order status | My units | Buy/Sell | Account | Value

Each copied row starts with an extra "Click for more details" cell and dates
carry a trailing "more information", both of which are stripped. Only
completed orders are imported; pending ones have not happened yet.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from budgetbuddy.models import InvestmentTrade, ParsedStatement, normalise_text, parse_date, parse_pence
from budgetbuddy.parsers.common import cell, is_blank_row, map_columns, read_csv_rows

NAME = "vanguard_orders"

ALIASES: dict[str, tuple[str, ...]] = {
    "fund": ("investment",),
    "date": ("date",),
    "order_type": ("ordertype",),
    "status": ("orderstatus", "status"),
    "units": ("myunits", "units"),
    "side": ("buysell",),
    "account": ("account",),
    "value": ("value",),
}
REQUIRED = ("fund", "date", "status", "units", "value")

_DATE_SUFFIX = re.compile(r"\s*more information\s*$", re.IGNORECASE)


def _find_header(rows: list[list[str]]) -> tuple[int, list[str], dict[str, int]] | None:
    for index, row in enumerate(rows[:10]):
        columns = map_columns(row, ALIASES)
        if all(f in columns for f in REQUIRED):
            return index, row, columns
    return None


def can_parse(path: Path) -> bool:
    if path.suffix.lower() not in (".csv", ".txt"):
        return False
    try:
        return _find_header(read_csv_rows(path)) is not None
    except (OSError, ValueError):
        return False


def _decimal(value: object) -> Decimal:
    text = str(value or "0").replace(",", "").replace("−", "-").strip()
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"Not a number: {value!r}") from exc


def parse(path: Path) -> ParsedStatement:
    rows = read_csv_rows(path)
    found = _find_header(rows)
    if found is None:
        raise ValueError(f"{path.name}: no Vanguard orders header (Investment, Date, Order status, My units, Value)")
    header_index, header, columns = found
    statement = ParsedStatement(parser=NAME, account_kind="isa", provider="Vanguard")
    pending = 0

    for line_no, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
        if is_blank_row(row):
            continue
        # Drop the "Click for more details" link cell that shifts every row right
        if len(row) == len(header) + 1:
            row = row[1:]
        status = normalise_text(cell(row, columns, "status")).casefold()
        if status != "completed":
            if status == "pending":
                pending += 1
            else:
                statement.warnings.append(f"line {line_no}: order status {status!r}, skipped")
            continue
        units = _decimal(cell(row, columns, "units"))
        value = parse_pence(cell(row, columns, "value"))
        if value is None:
            statement.warnings.append(f"line {line_no}: no value, skipped")
            continue
        side = normalise_text(cell(row, columns, "side"))
        order_type = normalise_text(cell(row, columns, "order_type"))
        statement.trades.append(
            InvestmentTrade(
                traded_on=parse_date(_DATE_SUFFIX.sub("", str(cell(row, columns, "date") or ""))),
                fund=normalise_text(cell(row, columns, "fund")),
                details=f"{order_type} {side}".strip(),
                quantity=units,
                # Price per unit; value is negative for sells, as are units
                price=(Decimal(value) / 100 / units).quantize(Decimal("0.0001")) if units else Decimal(0),
                cost_pence=value,
            )
        )

    if pending:
        statement.warnings.append(f"{pending} pending order(s) skipped; import again once they complete")
    if not statement.trades and not pending:
        raise ValueError(f"{path.name}: no completed Vanguard orders found")
    return statement

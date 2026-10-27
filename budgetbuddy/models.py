"""Plain data records shared by the parsers, importer and database."""

from __future__ import annotations

import datetime as dt
import hashlib
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

_WS = re.compile(r"\s+")


def parse_pence(value: object) -> int | None:
    """Turn '£1,234.56', '-12.3', '(4.00)' or a float into integer pence.

    Returns None for blanks so callers can skip rows with no amount.
    """
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        amount = Decimal(str(value))
    else:
        text = str(value).strip().replace("£", "").replace(",", "").replace("GBP", "").strip()
        if not text:
            return None
        negative = text.startswith("(") and text.endswith(")")
        text = text.strip("()")
        try:
            amount = Decimal(text)
        except InvalidOperation as exc:
            raise ValueError(f"Not a money amount: {value!r}") from exc
        if negative:
            amount = -amount
    return int((amount * 100).quantize(Decimal("1"), rounding="ROUND_HALF_UP"))


_DATE_FORMATS = ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%d %b %Y", "%d %B %Y")


def parse_date(value: object) -> dt.date:
    """Parse UK style dates (day first) or Excel date cells."""
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    text = str(value).strip()
    for fmt in _DATE_FORMATS:
        try:
            return dt.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date: {value!r}")


def normalise_text(value: object) -> str:
    return _WS.sub(" ", str(value or "")).strip()


@dataclass
class Transaction:
    """One movement of cash in an account (bank or the ISA's cash balance)."""

    posted_on: dt.date
    amount_pence: int
    description: str
    counterparty: str = ""
    reference: str = ""
    txn_type: str = ""
    source_category: str = ""
    notes: str = ""
    balance_pence: int | None = None
    # Vanguard only: deposit, withdrawal, buy, sell, fee, income, other
    kind: str | None = None

    def fingerprint(self) -> str:
        """Identity used to spot the same transaction in overlapping exports.

        Running balance is left out on purpose: identical same day payments
        are told apart by counting occurrences, not by balance.
        """
        key = "|".join(
            [
                self.posted_on.isoformat(),
                str(self.amount_pence),
                normalise_text(self.counterparty).casefold(),
                normalise_text(self.reference).casefold(),
                normalise_text(self.description).casefold(),
            ]
        )
        return hashlib.sha1(key.encode("utf-8")).hexdigest()


@dataclass
class InvestmentTrade:
    """A fund purchase or sale inside a Vanguard ISA."""

    traded_on: dt.date
    fund: str
    details: str
    quantity: Decimal
    price: Decimal
    cost_pence: int

    def fingerprint(self) -> str:
        key = "|".join(
            [
                self.traded_on.isoformat(),
                normalise_text(self.fund).casefold(),
                normalise_text(self.details).casefold(),
                str(self.quantity),
                str(self.cost_pence),
            ]
        )
        return hashlib.sha1(key.encode("utf-8")).hexdigest()


@dataclass
class ParsedStatement:
    """Everything a parser pulled out of one downloaded file."""

    parser: str
    account_kind: str  # "bank" or "isa"
    provider: str
    transactions: list[Transaction] = field(default_factory=list)
    trades: list[InvestmentTrade] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

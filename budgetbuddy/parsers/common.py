"""Helpers for reading the loosely structured files banks hand out."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def header_key(value: object) -> str:
    """'Amount (GBP)' -> 'amountgbp', 'Counter Party' -> 'counterparty'."""
    return _NON_ALNUM.sub("", str(value or "").casefold())


def read_csv_rows(path: Path) -> list[list[str]]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:  # pragma: no cover - cp1252 decodes almost anything
        raise ValueError(f"Cannot decode {path.name}")
    # Exports copied out of Excel come through tab separated
    first_line = text.split("\n", 1)[0]
    delimiter = "\t" if first_line.count("\t") > first_line.count(",") else ","
    return [row for row in csv.reader(io.StringIO(text), delimiter=delimiter)]


def map_columns(header: list[object], aliases: dict[str, tuple[str, ...]]) -> dict[str, int]:
    """Find each wanted field's column index using a list of accepted header names."""
    keys = [header_key(h) for h in header]
    found: dict[str, int] = {}
    for field_name, names in aliases.items():
        for name in names:
            if name in keys:
                found[field_name] = keys.index(name)
                break
    return found


def cell(row: list[object], columns: dict[str, int], field_name: str) -> object:
    index = columns.get(field_name)
    if index is None or index >= len(row):
        return None
    return row[index]


def is_blank_row(row: list[object]) -> bool:
    return all(v is None or str(v).strip() == "" for v in row)

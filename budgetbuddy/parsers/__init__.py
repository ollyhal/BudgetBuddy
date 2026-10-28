"""File format detection. Add a module here for each new bank or provider."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType

from budgetbuddy.models import ParsedStatement
from budgetbuddy.parsers import starling, vanguard, vanguard_orders

PARSERS: dict[str, ModuleType] = {m.NAME: m for m in (starling, vanguard_orders, vanguard)}


def detect(path: Path) -> ModuleType:
    for module in PARSERS.values():
        if module.can_parse(path):
            return module
    raise ValueError(
        f"{path.name}: format not recognised. Supported: {', '.join(PARSERS)}. "
        "Use --format to force one."
    )


def parse_file(path: Path, fmt: str | None = None) -> ParsedStatement:
    module = PARSERS[fmt] if fmt else detect(path)
    return module.parse(path)

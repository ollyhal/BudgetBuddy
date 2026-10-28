"""Turn raw payee text into a clean merchant name.

'TESCO STORES 1234' -> 'Tesco', 'PAYPAL *NETFLIX' -> 'Netflix',
'E.ON Energy' stays 'E.ON Energy'.
"""

from __future__ import annotations

import re

# Payment processors that put the real merchant after a '*'
_PROCESSORS = ("paypal", "sq", "sumup", "zettle", "izettle", "sp", "stripe")

# Known messy names, checked as case-insensitive "starts with"
_ALIASES: tuple[tuple[str, str], ...] = (
    ("amzn", "Amazon"),
    ("amazon", "Amazon"),
    ("tesco", "Tesco"),
    ("sainsbury", "Sainsbury's"),
    ("asda", "Asda"),
    ("morrisons", "Morrisons"),
    ("wm morrison", "Morrisons"),
    ("waitrose", "Waitrose"),
    ("lidl", "Lidl"),
    ("aldi", "Aldi"),
    ("co-op", "Co-op"),
    ("coop", "Co-op"),
    ("mcdonald", "McDonald's"),
    ("uber eats", "Uber Eats"),
    ("uber", "Uber"),
    ("deliveroo", "Deliveroo"),
    ("just eat", "Just Eat"),
    ("netflix", "Netflix"),
    ("spotify", "Spotify"),
    ("apple.com", "Apple"),
    ("google", "Google"),
    ("trainline", "Trainline"),
    ("tfl", "TfL"),
)

_TRAILING_NOISE = re.compile(
    r"(\s+(ltd|limited|plc|llp|uk|gb|london))+\.?$|\s+#?\d{3,}$|\s+[a-z]{2}\d{1,2}\s*\d[a-z]{2}$",
    re.IGNORECASE,
)


def clean_merchant(counterparty: str, reference: str = "") -> str:
    raw = re.sub(r"\s+", " ", (counterparty or reference or "").strip())
    if not raw:
        return "Unknown"
    if "*" in raw:
        head, _, tail = raw.partition("*")
        raw = tail.strip() if head.strip().casefold() in _PROCESSORS and tail.strip() else head.strip()
    lowered = raw.casefold()
    for prefix, name in _ALIASES:
        if lowered.startswith(prefix):
            return name
    previous = None
    while previous != raw:
        previous, raw = raw, _TRAILING_NOISE.sub("", raw).strip()
    # Shouting all-caps names read better in title case; mixed case is left as the bank sent it
    if raw.isupper() and len(raw) > 4:
        raw = raw.title()
    return raw or "Unknown"

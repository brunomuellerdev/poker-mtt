"""Classify an indicator value against ordered evaluation bands.

A band is a half-open interval [lower, upper): lower is inclusive, upper
exclusive. None means unbounded (-inf for lower, +inf for upper). Bands are
expected to tile the number line without gaps or overlap; the first matching
band (by ascending order) wins.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Band:
    lower: Decimal | None
    upper: Decimal | None
    label: str


def classify(value: Decimal | None, bands: list[Band]) -> str | None:
    """Return the label whose band contains `value`, or None if value is None
    or no band matches."""
    if value is None:
        return None
    for band in bands:
        lower_ok = band.lower is None or value >= band.lower
        upper_ok = band.upper is None or value < band.upper
        if lower_ok and upper_ok:
            return band.label
    return None

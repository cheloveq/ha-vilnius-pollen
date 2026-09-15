"""Plausibility screening for Vilnius pollen measurements."""

from __future__ import annotations

from math import isfinite

QUALITY_VALID = "valid"
QUALITY_SOURCE_NULL = "source_null"
QUALITY_INVALID_NUMBER = "invalid_number"
QUALITY_NEGATIVE = "negative"
QUALITY_ABOVE_PLAUSIBILITY_CEILING = "above_plausibility_ceiling"


def concentration_quality(value: object, ceiling: float) -> str:
    """Describe whether one raw source concentration is usable downstream."""
    if value is None:
        return QUALITY_SOURCE_NULL
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        return QUALITY_INVALID_NUMBER
    if value < 0:
        return QUALITY_NEGATIVE
    if value > ceiling:
        return QUALITY_ABOVE_PLAUSIBILITY_CEILING
    return QUALITY_VALID


def screened_concentration(value: object, ceiling: float) -> float | None:
    """Return a usable concentration, or None when the raw value is suspect."""
    if concentration_quality(value, ceiling) != QUALITY_VALID:
        return None
    return float(value)

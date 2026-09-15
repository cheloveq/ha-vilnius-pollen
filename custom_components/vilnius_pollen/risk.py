"""Source-published pollen symptom-risk mapping."""

from math import isfinite

from .const import RISK_OPTIONS


def symptom_risk(value: float | None, limits: tuple[float, float, float]) -> str | None:
    """Map a raw source concentration to its published four-band label."""
    if value is None:
        return None
    for limit, label in zip(limits, RISK_OPTIONS):
        if value <= limit:
            return label
    return RISK_OPTIONS[-1]


def displayed_concentration(value: object) -> float | None:
    """Return a finite numeric source value at useful display precision."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        return None
    return round(float(value), 1)

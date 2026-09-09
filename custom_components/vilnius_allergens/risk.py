"""Source-published pollen symptom-risk mapping."""

from .const import RISK_OPTIONS


def symptom_risk(value: float | int | None, limits: tuple[float, float, float]) -> str | None:
    """Map a raw source concentration to its published four-band label."""
    if value is None:
        return None
    for limit, label in zip(limits, RISK_OPTIONS):
        if value <= limit:
            return label
    return RISK_OPTIONS[-1]


def displayed_concentration(value: float | int | None) -> float | None:
    """Round a source concentration to the precision useful in Home Assistant."""
    return None if value is None else round(value, 1)

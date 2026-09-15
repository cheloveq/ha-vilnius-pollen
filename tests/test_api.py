"""Regression tests for the public OpenCity data contract."""

import asyncio
import importlib.util
import sys
import types
from datetime import UTC, datetime
from pathlib import Path

import pytest

component = Path(__file__).parents[1] / "custom_components" / "vilnius_pollen"
package = types.ModuleType("vilnius_pollen")
package.__path__ = [str(component)]
sys.modules["vilnius_pollen"] = package
for name in ("const", "api", "quality", "risk"):
    spec = importlib.util.spec_from_file_location(
        f"vilnius_pollen.{name}", component / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

from vilnius_pollen.api import VilniusPollenApi, VilniusPollenApiError, timestamp_from_arcgis
from vilnius_pollen.const import PLAUSIBILITY_CEILINGS
from vilnius_pollen.quality import (
    QUALITY_ABOVE_PLAUSIBILITY_CEILING,
    QUALITY_INVALID_NUMBER,
    QUALITY_NEGATIVE,
    QUALITY_SOURCE_NULL,
    QUALITY_VALID,
    concentration_quality,
    screened_concentration,
)
from vilnius_pollen.risk import displayed_concentration, symptom_risk


class Response:
    def __init__(self, payload):
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    def raise_for_status(self):
        return None

    async def json(self, **_):
        return self.payload


class Session:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, *, params):
        self.calls.append((url, params))
        return Response(self.payload)


def test_timestamp_is_aware_utc():
    assert timestamp_from_arcgis(0) == datetime(1970, 1, 1, tzinfo=UTC)


def test_latest_uses_descending_non_geometric_query():
    session = Session({"features": [{"attributes": {"timestamp": 1, "Artemisia": 2.5}}]})
    result = asyncio.run(VilniusPollenApi(session).async_latest())
    assert result == {"timestamp": 1, "Artemisia": 2.5}
    assert session.calls[0][1]["orderByFields"] == "timestamp DESC"
    assert session.calls[0][1]["returnGeometry"] == "false"


def test_latest_rejects_empty_source_response():
    with pytest.raises(VilniusPollenApiError):
        asyncio.run(VilniusPollenApi(Session({"features": []})).async_latest())


def test_history_is_bounded_ascending_and_preserves_nulls():
    session = Session({"features": [{"attributes": {"timestamp": 1000, "Alnus": None}}]})
    records = asyncio.run(
        VilniusPollenApi(session).async_history(
            datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 2, tzinfo=UTC), 3
        )
    )
    assert records == [{"timestamp": 1000, "Alnus": None}]
    params = session.calls[0][1]
    assert params["orderByFields"] == "timestamp ASC"
    assert params["resultRecordCount"] == "3"


def test_history_rejects_invalid_range():
    api = VilniusPollenApi(Session({}))
    with pytest.raises(VilniusPollenApiError):
        asyncio.run(
            api.async_history(datetime(2026, 1, 2, tzinfo=UTC), datetime(2026, 1, 1, tzinfo=UTC), 1)
        )


def test_source_symptom_risk_bands_and_null():
    limits = (15, 31, 50)
    assert [symptom_risk(value, limits) for value in (0, 15, 16, 31, 32, 50, 51)] == [
        "low",
        "low",
        "medium",
        "medium",
        "high",
        "high",
        "very_high",
    ]
    assert symptom_risk(None, limits) is None


def test_concentration_display_rounding_preserves_null():
    assert displayed_concentration(162.6000061) == 162.6
    assert displayed_concentration(0) == 0
    assert displayed_concentration(None) is None
    assert displayed_concentration("87.5") is None
    assert displayed_concentration(float("inf")) is None


def test_quality_screening_preserves_boundary_and_drops_extremes():
    ceiling = PLAUSIBILITY_CEILINGS["Artemisia"]
    assert concentration_quality(87.5, ceiling) == QUALITY_VALID
    assert concentration_quality(ceiling, ceiling) == QUALITY_VALID
    assert concentration_quality(9404.7, ceiling) == QUALITY_ABOVE_PLAUSIBILITY_CEILING
    assert screened_concentration(9404.7, ceiling) is None
    assert screened_concentration(87.5, ceiling) == 87.5


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, QUALITY_SOURCE_NULL),
        ("87.5", QUALITY_INVALID_NUMBER),
        (float("nan"), QUALITY_INVALID_NUMBER),
        (-1, QUALITY_NEGATIVE),
    ],
)
def test_quality_screening_rejects_unusable_values(value, expected):
    assert concentration_quality(value, 1000) == expected
    assert screened_concentration(value, 1000) is None


def test_all_taxa_have_positive_plausibility_ceilings():
    assert set(PLAUSIBILITY_CEILINGS) == {
        "Alnus",
        "Ambrosia",
        "Artemisia",
        "Betula",
        "Corylus",
        "Poaceae",
    }
    assert all(value > 0 for value in PLAUSIBILITY_CEILINGS.values())

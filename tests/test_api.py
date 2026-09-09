"""Regression tests for the public OpenCity data contract."""

import asyncio
import sys
import importlib.util
import types
from datetime import UTC, datetime
from pathlib import Path

import pytest

component = Path(__file__).parents[1] / "custom_components" / "vilnius_allergens"
package = types.ModuleType("vilnius_allergens")
package.__path__ = [str(component)]
sys.modules["vilnius_allergens"] = package
for name in ("const", "api", "risk"):
    spec = importlib.util.spec_from_file_location(f"vilnius_allergens.{name}", component / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

from vilnius_allergens.api import VilniusAllergensApi, VilniusAllergensApiError, timestamp_from_arcgis
from vilnius_allergens.risk import symptom_risk


class Response:
    def __init__(self, payload): self.payload = payload
    async def __aenter__(self): return self
    async def __aexit__(self, *_): return None
    def raise_for_status(self): return None
    async def json(self, **_): return self.payload


class Session:
    def __init__(self, payload): self.payload = payload; self.calls = []
    def get(self, url, *, params): self.calls.append((url, params)); return Response(self.payload)


def test_timestamp_is_aware_utc():
    assert timestamp_from_arcgis(0) == datetime(1970, 1, 1, tzinfo=UTC)


def test_latest_uses_descending_non_geometric_query():
    session = Session({"features": [{"attributes": {"timestamp": 1, "Artemisia": 2.5}}]})
    result = asyncio.run(VilniusAllergensApi(session).async_latest())
    assert result == {"timestamp": 1, "Artemisia": 2.5}
    assert session.calls[0][1]["orderByFields"] == "timestamp DESC"
    assert session.calls[0][1]["returnGeometry"] == "false"


def test_latest_rejects_empty_source_response():
    with pytest.raises(VilniusAllergensApiError):
        asyncio.run(VilniusAllergensApi(Session({"features": []})).async_latest())


def test_history_is_bounded_ascending_and_preserves_nulls():
    session = Session({"features": [{"attributes": {"timestamp": 1000, "Alnus": None}}]})
    records = asyncio.run(VilniusAllergensApi(session).async_history(datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 2, tzinfo=UTC), 3))
    assert records == [{"timestamp": 1000, "Alnus": None}]
    params = session.calls[0][1]
    assert params["orderByFields"] == "timestamp ASC"
    assert params["resultRecordCount"] == "3"


def test_history_rejects_invalid_range():
    api = VilniusAllergensApi(Session({}))
    with pytest.raises(VilniusAllergensApiError):
        asyncio.run(api.async_history(datetime(2026, 1, 2, tzinfo=UTC), datetime(2026, 1, 1, tzinfo=UTC), 1))


def test_source_symptom_risk_bands_and_null():
    limits = (15, 31, 50)
    assert [symptom_risk(value, limits) for value in (0, 15, 16, 31, 32, 50, 51)] == ["low", "low", "medium", "medium", "high", "high", "very_high"]
    assert symptom_risk(None, limits) is None

"""Client for the public Vilnius OpenCity bioaerosol layer."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

import aiohttp

from .const import DATA_FIELDS, LAYER_URL, TIMESTAMP_FIELD


class VilniusPollenApiError(Exception):
    """Raised when the public source cannot provide a usable response."""


class VilniusPollenApi:
    """Fetch the newest hourly source observation without geometry."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def async_latest(self) -> dict[str, Any]:
        params = {"where": "1=1", "outFields": ",".join((TIMESTAMP_FIELD, *DATA_FIELDS, "device_id", "latitude", "longitude", "Status")), "orderByFields": f"{TIMESTAMP_FIELD} DESC", "resultRecordCount": "1", "returnGeometry": "false", "f": "json"}
        try:
            async with self._session.get(f"{LAYER_URL}/query", params=params) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (aiohttp.ClientError, ValueError) as err:
            raise VilniusPollenApiError("Unable to fetch Vilnius pollen data") from err
        if payload.get("error") or not (features := payload.get("features")):
            raise VilniusPollenApiError("Vilnius pollen source returned no observation")
        attributes = features[0].get("attributes")
        if not isinstance(attributes, Mapping) or attributes.get(TIMESTAMP_FIELD) is None:
            raise VilniusPollenApiError("Vilnius pollen observation has no timestamp")
        return dict(attributes)

    async def async_history(
        self, start: datetime, end: datetime, limit: int
    ) -> list[dict[str, Any]]:
        """Return a bounded, ascending UTC history range from ArcGIS.

        The upstream layer is the historical system of record. This deliberately
        does not write external observations into Home Assistant Recorder.
        """
        if start.tzinfo is None or end.tzinfo is None or start >= end:
            raise VilniusPollenApiError("History start must be before end and timezone-aware")
        where = (
            f"{TIMESTAMP_FIELD} > TIMESTAMP '{start.astimezone(timezone.utc):%Y-%m-%d %H:%M:%S}' "
            f"AND {TIMESTAMP_FIELD} <= TIMESTAMP '{end.astimezone(timezone.utc):%Y-%m-%d %H:%M:%S}'"
        )
        params = {
            "where": where,
            "outFields": ",".join((TIMESTAMP_FIELD, *DATA_FIELDS)),
            "orderByFields": f"{TIMESTAMP_FIELD} ASC",
            "resultRecordCount": str(limit),
            "returnGeometry": "false",
            "f": "json",
        }
        try:
            async with self._session.get(f"{LAYER_URL}/query", params=params) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (aiohttp.ClientError, ValueError) as err:
            raise VilniusPollenApiError("Unable to fetch Vilnius pollen history") from err
        if payload.get("error"):
            raise VilniusPollenApiError("Vilnius pollen history query failed")
        return [dict(feature["attributes"]) for feature in payload.get("features", [])]


def timestamp_from_arcgis(value: int | float) -> datetime:
    """Convert an ArcGIS UTC millisecond timestamp to an aware datetime."""
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)

"""Client for the public Vilnius OpenCity bioaerosol layer."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

import aiohttp

from .const import DATA_FIELDS, LAYER_URL, TIMESTAMP_FIELD


class VilniusAllergensApiError(Exception):
    """Raised when the public source cannot provide a usable response."""


class VilniusAllergensApi:
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
            raise VilniusAllergensApiError("Unable to fetch Vilnius pollen data") from err
        if payload.get("error") or not (features := payload.get("features")):
            raise VilniusAllergensApiError("Vilnius pollen source returned no observation")
        attributes = features[0].get("attributes")
        if not isinstance(attributes, Mapping) or attributes.get(TIMESTAMP_FIELD) is None:
            raise VilniusAllergensApiError("Vilnius pollen observation has no timestamp")
        return dict(attributes)


def timestamp_from_arcgis(value: int | float) -> datetime:
    """Convert an ArcGIS UTC millisecond timestamp to an aware datetime."""
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)

"""Vilnius Pollen integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv
from homeassistant.core import HomeAssistant
from homeassistant.helpers.service import SupportsResponse

import voluptuous as vol

from .api import VilniusPollenApiError, timestamp_from_arcgis
from .const import DOMAIN, MAX_HISTORY_RECORDS, SERVICE_QUERY_HISTORY
from .coordinator import VilniusPollenCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Vilnius Pollen."""
    coordinator = VilniusPollenCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    _async_register_history_service(hass)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Vilnius Pollen."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


def _async_register_history_service(hass: HomeAssistant) -> None:
    """Register one bounded, read-only public-history service."""
    if hass.services.has_service(DOMAIN, SERVICE_QUERY_HISTORY):
        return

    async def async_query_history(call):
        start = call.data["start"]
        end = call.data["end"]
        limit = call.data.get("limit", 500)
        coordinator = next(iter(hass.data[DOMAIN].values()))
        try:
            records = await coordinator._api.async_history(start, end, limit)
        except VilniusPollenApiError as err:
            raise vol.Invalid(str(err)) from err
        return {
            "source": "Vilnius OpenCity Bioaerozoliai layer 0",
            "records": [
                {"timestamp": timestamp_from_arcgis(row["timestamp"]).isoformat(), **{key: row.get(key) for key in row if key != "timestamp"}}
                for row in records
            ],
        }

    hass.services.async_register(
        DOMAIN,
        SERVICE_QUERY_HISTORY,
        async_query_history,
        schema=vol.Schema({vol.Required("start"): cv.datetime, vol.Required("end"): cv.datetime, vol.Optional("limit", default=500): vol.All(vol.Coerce(int), vol.Range(min=1, max=MAX_HISTORY_RECORDS))}),
        supports_response=SupportsResponse.ONLY,
    )

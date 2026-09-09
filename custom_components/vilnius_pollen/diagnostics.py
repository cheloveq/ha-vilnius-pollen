"""Diagnostics for Vilnius Pollen."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, LAYER_URL


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    """Return public-source diagnostics; no secrets exist in this integration."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "entry": {"title": entry.title, "data": entry.data},
        "source_layer": LAYER_URL,
        "last_update_success": coordinator.last_update_success,
        "latest_observation": coordinator.data,
    }

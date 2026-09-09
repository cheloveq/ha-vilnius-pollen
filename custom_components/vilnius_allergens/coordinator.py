"""Coordinator for Vilnius Allergens."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VilniusAllergensApi, VilniusAllergensApiError
from .const import DOMAIN, UPDATE_INTERVAL

LOGGER = logging.getLogger(__name__)


class VilniusAllergensCoordinator(DataUpdateCoordinator[dict]):
    """Coordinate one source request for all pollen entities."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(hass, LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        self._api = VilniusAllergensApi(async_get_clientsession(hass))

    async def _async_update_data(self) -> dict:
        try:
            return await self._api.async_latest()
        except VilniusAllergensApiError as err:
            raise UpdateFailed(str(err)) from err

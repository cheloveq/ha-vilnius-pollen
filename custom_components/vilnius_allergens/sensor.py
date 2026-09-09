"""Sensors for Vilnius Allergens."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import timestamp_from_arcgis
from .const import DOMAIN, MANUFACTURER, MODEL, POLLEN_UNIT, TIMESTAMP_FIELD
from .coordinator import VilniusAllergensCoordinator


@dataclass(frozen=True, kw_only=True)
class PollenDescription(SensorEntityDescription):
    field: str


DESCRIPTIONS = (
    PollenDescription(key="alder", translation_key="alder", field="Alnus", native_unit_of_measurement=POLLEN_UNIT, state_class=SensorStateClass.MEASUREMENT),
    PollenDescription(key="ragweed", translation_key="ragweed", field="Ambrosia", native_unit_of_measurement=POLLEN_UNIT, state_class=SensorStateClass.MEASUREMENT),
    PollenDescription(key="mugwort", translation_key="mugwort", field="Artemisia", native_unit_of_measurement=POLLEN_UNIT, state_class=SensorStateClass.MEASUREMENT),
    PollenDescription(key="birch", translation_key="birch", field="Betula", native_unit_of_measurement=POLLEN_UNIT, state_class=SensorStateClass.MEASUREMENT),
    PollenDescription(key="hazel", translation_key="hazel", field="Corylus", native_unit_of_measurement=POLLEN_UNIT, state_class=SensorStateClass.MEASUREMENT),
    PollenDescription(key="grass", translation_key="grass", field="Poaceae", native_unit_of_measurement=POLLEN_UNIT, state_class=SensorStateClass.MEASUREMENT),
    PollenDescription(key="total", translation_key="total", field="Pollen", native_unit_of_measurement=POLLEN_UNIT, state_class=SensorStateClass.MEASUREMENT),
)
TIMESTAMP = SensorEntityDescription(key="last_measurement", translation_key="last_measurement", device_class=SensorDeviceClass.TIMESTAMP)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: VilniusAllergensCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PollenSensor(coordinator, description) for description in DESCRIPTIONS] + [LastMeasurementSensor(coordinator)])


class BaseSensor(CoordinatorEntity[VilniusAllergensCoordinator], SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, coordinator: VilniusAllergensCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, "vilnius-bioaerosol-site")}, manufacturer=MANUFACTURER, model=MODEL, name="Vilnius Allergens")


class PollenSensor(BaseSensor):
    entity_description: PollenDescription
    def __init__(self, coordinator: VilniusAllergensCoordinator, description: PollenDescription) -> None:
        super().__init__(coordinator); self.entity_description = description; self._attr_unique_id = f"vilnius_bioaerosol_{description.key}"
    @property
    def native_value(self): return self.coordinator.data.get(self.entity_description.field)


class LastMeasurementSensor(BaseSensor):
    entity_description = TIMESTAMP
    def __init__(self, coordinator: VilniusAllergensCoordinator) -> None:
        super().__init__(coordinator); self._attr_unique_id = "vilnius_bioaerosol_last_measurement"
    @property
    def native_value(self): return timestamp_from_arcgis(self.coordinator.data[TIMESTAMP_FIELD])

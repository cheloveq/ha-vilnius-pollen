"""Sensors for Vilnius Pollen."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import timestamp_from_arcgis
from .const import (
    DOMAIN,
    MANUFACTURER,
    MAX_MEASUREMENT_AGE,
    MODEL,
    PLAUSIBILITY_CEILINGS,
    POLLEN_UNIT,
    RISK_OPTIONS,
    SOURCE_RISK_LIMITS,
    TIMESTAMP_FIELD,
)
from .coordinator import VilniusPollenCoordinator
from .quality import QUALITY_VALID, concentration_quality, screened_concentration
from .risk import displayed_concentration, symptom_risk


@dataclass(frozen=True, kw_only=True)
class PollenDescription(SensorEntityDescription):
    field: str
    plausibility_ceiling: float


@dataclass(frozen=True, kw_only=True)
class RiskDescription(SensorEntityDescription):
    field: str
    limits: tuple[float, float, float]


RAW_DESCRIPTIONS = (
    PollenDescription(
        key="alder",
        translation_key="alder",
        field="Alnus",
        plausibility_ceiling=PLAUSIBILITY_CEILINGS["Alnus"],
        native_unit_of_measurement=POLLEN_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PollenDescription(
        key="ragweed",
        translation_key="ragweed",
        field="Ambrosia",
        plausibility_ceiling=PLAUSIBILITY_CEILINGS["Ambrosia"],
        native_unit_of_measurement=POLLEN_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PollenDescription(
        key="mugwort",
        translation_key="mugwort",
        field="Artemisia",
        plausibility_ceiling=PLAUSIBILITY_CEILINGS["Artemisia"],
        native_unit_of_measurement=POLLEN_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PollenDescription(
        key="birch",
        translation_key="birch",
        field="Betula",
        plausibility_ceiling=PLAUSIBILITY_CEILINGS["Betula"],
        native_unit_of_measurement=POLLEN_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PollenDescription(
        key="hazel",
        translation_key="hazel",
        field="Corylus",
        plausibility_ceiling=PLAUSIBILITY_CEILINGS["Corylus"],
        native_unit_of_measurement=POLLEN_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PollenDescription(
        key="grass",
        translation_key="grass",
        field="Poaceae",
        plausibility_ceiling=PLAUSIBILITY_CEILINGS["Poaceae"],
        native_unit_of_measurement=POLLEN_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)
SCREENED_DESCRIPTIONS = tuple(
    PollenDescription(
        key=f"{description.key}_screened",
        translation_key=f"{description.key}_screened",
        field=description.field,
        plausibility_ceiling=description.plausibility_ceiling,
        native_unit_of_measurement=POLLEN_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
    )
    for description in RAW_DESCRIPTIONS
)
TIMESTAMP = SensorEntityDescription(
    key="last_measurement",
    translation_key="last_measurement",
    device_class=SensorDeviceClass.TIMESTAMP,
)
RISK_DESCRIPTIONS = tuple(
    RiskDescription(
        key=f"{description.key}_risk",
        translation_key=f"{description.key}_risk",
        field=description.field,
        limits=SOURCE_RISK_LIMITS[description.field],
        device_class=SensorDeviceClass.ENUM,
        options=list(RISK_OPTIONS),
    )
    for description in RAW_DESCRIPTIONS
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VilniusPollenCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [PollenSensor(coordinator, description) for description in RAW_DESCRIPTIONS]
        + [ScreenedPollenSensor(coordinator, description) for description in SCREENED_DESCRIPTIONS]
        + [SymptomRiskSensor(coordinator, description) for description in RISK_DESCRIPTIONS]
        + [LastMeasurementSensor(coordinator)]
    )


class BaseSensor(CoordinatorEntity[VilniusPollenCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: VilniusPollenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "vilnius-bioaerosol-site")},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name="Vilnius Pollen",
        )

    @property
    def available(self) -> bool:
        """Do not present an old upstream measurement as a fresh reading."""
        if not super().available or not self.coordinator.data:
            return False
        try:
            timestamp = timestamp_from_arcgis(self.coordinator.data[TIMESTAMP_FIELD])
        except (KeyError, TypeError, ValueError, OSError):
            return False
        return datetime.now(timezone.utc) - timestamp <= MAX_MEASUREMENT_AGE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        timestamp = timestamp_from_arcgis(self.coordinator.data[TIMESTAMP_FIELD])
        return {
            "source": "Vilnius OpenCity Bioaerozoliai layer 0",
            "measurement_timestamp": timestamp.isoformat(),
        }


class PollenSensor(BaseSensor):
    entity_description: PollenDescription

    def __init__(
        self, coordinator: VilniusPollenCoordinator, description: PollenDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"vilnius_bioaerosol_{description.key}"

    @property
    def native_value(self) -> float | None:
        return displayed_concentration(self.coordinator.data.get(self.entity_description.field))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attributes = super().extra_state_attributes
        source_value = self.coordinator.data.get(self.entity_description.field)
        attributes.update(
            {
                "source_value": source_value,
                "data_quality": concentration_quality(
                    source_value, self.entity_description.plausibility_ceiling
                ),
                "plausibility_ceiling": self.entity_description.plausibility_ceiling,
            }
        )
        return attributes


class ScreenedPollenSensor(PollenSensor):
    """Pollen concentration with suspect source values omitted."""

    def __init__(
        self, coordinator: VilniusPollenCoordinator, description: PollenDescription
    ) -> None:
        super().__init__(coordinator, description)
        self._attr_unique_id = f"vilnius_bioaerosol_{description.key}"

    @property
    def native_value(self) -> float | None:
        value = screened_concentration(
            self.coordinator.data.get(self.entity_description.field),
            self.entity_description.plausibility_ceiling,
        )
        return displayed_concentration(value)


class LastMeasurementSensor(BaseSensor):
    entity_description = TIMESTAMP

    def __init__(self, coordinator: VilniusPollenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "vilnius_bioaerosol_last_measurement"

    @property
    def native_value(self):
        return timestamp_from_arcgis(self.coordinator.data[TIMESTAMP_FIELD])


class SymptomRiskSensor(BaseSensor):
    """Source-published symptom-risk band for one pollen taxon."""

    entity_description: RiskDescription

    def __init__(self, coordinator: VilniusPollenCoordinator, description: RiskDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"vilnius_bioaerosol_{description.key}"

    @property
    def native_value(self) -> str | None:
        source_value = self.coordinator.data.get(self.entity_description.field)
        ceiling = PLAUSIBILITY_CEILINGS[self.entity_description.field]
        value = screened_concentration(source_value, ceiling)
        return symptom_risk(value, self.entity_description.limits)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attributes = super().extra_state_attributes
        source_value = self.coordinator.data.get(self.entity_description.field)
        ceiling = PLAUSIBILITY_CEILINGS[self.entity_description.field]
        quality = concentration_quality(source_value, ceiling)
        attributes.update(
            {
                "source_value": source_value,
                "data_quality": quality,
                "plausibility_ceiling": ceiling,
                "risk_suppressed": quality != QUALITY_VALID,
            }
        )
        return attributes

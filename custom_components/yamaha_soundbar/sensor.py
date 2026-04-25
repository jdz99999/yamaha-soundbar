"""Sensor platform for Yamaha Soundbar.

The bar's read-only state lives across three coordinator data branches:
    coordinator.data["status"]   ← getStatusEx (RSSI, MAC, project, ...)
    coordinator.data["player"]   ← getPlayerStatus (mode, vol, status, ...)
    coordinator.data["yamaha"]   ← YAMAHA_DATA_GET (Audio Stream, firmware blob, ...)

We split the EntityDescription into three sibling dataclasses by source branch
rather than runtime-branching on a discriminator field. Same architectural
split as select.py (mode-int vs YAMAHA_DATA_GET) and number.py (YAMAHA_DATA_SET
vs setPlayerCmd).
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_UUID, DOMAIN
from .coordinator import YamahaCoordinator
from .entity import YamahaCoordinatorEntity


@dataclass(frozen=True, kw_only=True)
class YamahaYamahaSensorDescription(SensorEntityDescription):
    """Sensor reading from coordinator.data['yamaha']."""

    api_key: str


@dataclass(frozen=True, kw_only=True)
class YamahaPlayerSensorDescription(SensorEntityDescription):
    """Sensor reading from coordinator.data['player']."""

    read_field: str


@dataclass(frozen=True, kw_only=True)
class YamahaStatusSensorDescription(SensorEntityDescription):
    """Sensor reading from coordinator.data['status'] (getStatusEx)."""

    read_field: str


@dataclass(frozen=True, kw_only=True)
class YamahaPlayerMappedSensorDescription(SensorEntityDescription):
    """Player-side integer field mapped through a label dict.

    NOTE: the mode_map for input_mode is intentionally duplicated between
    select.py (which uses (label, set_verb) tuples for read+write) and this
    file (which uses just labels for read-only). The shapes differ enough
    that abstracting them out would cost more than it saves. If a new mode
    integer is added, it MUST be added in BOTH select.py's SELECTS entry
    and the PLAYER_MAPPED_SENSORS entry below.
    """

    read_field: str
    mode_map: dict[int, str]


YAMAHA_SENSORS: tuple[YamahaYamahaSensorDescription, ...] = (
    YamahaYamahaSensorDescription(
        key="audio_stream",
        translation_key="audio_stream",
        icon="mdi:waveform",
        api_key="Audio Stream",
    ),
    YamahaYamahaSensorDescription(
        key="firmware_system",
        translation_key="firmware_system",
        icon="mdi:chip",
        api_key="System Version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    YamahaYamahaSensorDescription(
        key="firmware_a118",
        translation_key="firmware_a118",
        icon="mdi:chip",
        api_key="A118",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    YamahaYamahaSensorDescription(
        key="firmware_mcu",
        translation_key="firmware_mcu",
        icon="mdi:chip",
        api_key="MCU",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    YamahaYamahaSensorDescription(
        key="firmware_dsp",
        translation_key="firmware_dsp",
        icon="mdi:chip",
        api_key="DSP(FW)",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    YamahaYamahaSensorDescription(
        key="firmware_hdmi",
        translation_key="firmware_hdmi",
        icon="mdi:chip",
        api_key="HDMI",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


PLAYER_SENSORS: tuple[YamahaPlayerSensorDescription, ...] = ()


STATUS_SENSORS: tuple[YamahaStatusSensorDescription, ...] = (
    YamahaStatusSensorDescription(
        key="rssi",
        translation_key="rssi",
        icon="mdi:wifi-strength-2",
        read_field="RSSI",
        native_unit_of_measurement="dBm",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


# IMPORTANT: input_mode's mode_map below duplicates the read side of
# select.py's input_source mode_map (which also has set verbs). If a new
# mode integer ever needs to be supported, add it BOTH here and there.
PLAYER_MAPPED_SENSORS: tuple[YamahaPlayerMappedSensorDescription, ...] = (
    YamahaPlayerMappedSensorDescription(
        key="input_mode",
        translation_key="input_mode",
        icon="mdi:video-input-hdmi",
        read_field="mode",
        mode_map={
            41: "Bluetooth",
            43: "TV",
            49: "HDMI",
            31: "Net",
        },
        device_class=SensorDeviceClass.ENUM,
        options=["Bluetooth", "TV", "HDMI", "Net"],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Yamaha sensors from a config entry."""
    bucket = hass.data[DOMAIN][entry.entry_id]
    coordinator: YamahaCoordinator = bucket["coordinator"]
    uuid = entry.data.get(CONF_UUID) or entry.entry_id

    entities: list[SensorEntity] = []
    entities.extend(
        YamahaYamahaSensor(coordinator, uuid, d) for d in YAMAHA_SENSORS
    )
    entities.extend(
        YamahaPlayerSensor(coordinator, uuid, d) for d in PLAYER_SENSORS
    )
    entities.extend(
        YamahaStatusSensor(coordinator, uuid, d) for d in STATUS_SENSORS
    )
    entities.extend(
        YamahaPlayerMappedSensor(coordinator, uuid, d)
        for d in PLAYER_MAPPED_SENSORS
    )
    async_add_entities(entities)


class _YamahaSensorBase(YamahaCoordinatorEntity, SensorEntity):
    """Shared init for the three sensor variants."""

    def __init__(
        self,
        coordinator: YamahaCoordinator,
        uuid: str,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{uuid}_{description.key}"


class YamahaYamahaSensor(_YamahaSensorBase):
    """A read-only string sensor sourced from YAMAHA_DATA_GET."""

    entity_description: YamahaYamahaSensorDescription

    @property
    def native_value(self) -> str | None:
        data = self.coordinator.data or {}
        yamaha = data.get("yamaha") or {}
        raw = yamaha.get(self.entity_description.api_key)
        if raw is None:
            return None
        return str(raw)


class YamahaPlayerSensor(_YamahaSensorBase):
    """A read-only string sensor sourced from getPlayerStatus."""

    entity_description: YamahaPlayerSensorDescription

    @property
    def native_value(self) -> str | None:
        data = self.coordinator.data or {}
        player = data.get("player") or {}
        raw = player.get(self.entity_description.read_field)
        if raw is None:
            return None
        return str(raw)


class YamahaStatusSensor(_YamahaSensorBase):
    """A sensor sourced from getStatusEx.

    RSSI is the only entry today and needs int coercion. Other status fields
    that get added later may be numeric or string — coerce to int when the
    description sets state_class=MEASUREMENT, else pass through as string.
    """

    entity_description: YamahaStatusSensorDescription

    @property
    def native_value(self) -> int | str | None:
        data = self.coordinator.data or {}
        status = data.get("status") or {}
        raw = status.get(self.entity_description.read_field)
        if raw is None:
            return None
        if self.entity_description.state_class == SensorStateClass.MEASUREMENT:
            try:
                return int(raw)
            except (TypeError, ValueError):
                return None
        return str(raw)


class YamahaPlayerMappedSensor(_YamahaSensorBase):
    """A player-side int field exposed as a labeled ENUM sensor.

    Duplicates the read side of select.py's input source for users who want
    to trigger automations on input changes — sensor state changes are easier
    to subscribe to than poking at a select entity's current_option attribute.
    """

    entity_description: YamahaPlayerMappedSensorDescription

    @property
    def native_value(self) -> str | None:
        data = self.coordinator.data or {}
        player = data.get("player") or {}
        raw = player.get(self.entity_description.read_field)
        if raw is None:
            return None
        try:
            mode_int = int(raw)
        except (TypeError, ValueError):
            return None
        return self.entity_description.mode_map.get(mode_int)

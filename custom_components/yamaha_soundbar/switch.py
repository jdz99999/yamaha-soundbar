"""Switch platform for Yamaha Soundbar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._yamaha_codec import _build_set_payload
from .const import CONF_UUID, DOMAIN
from .coordinator import YamahaCoordinator
from .entity import YamahaCoordinatorEntity


@dataclass(frozen=True, kw_only=True)
class YamahaSwitchDescription(SwitchEntityDescription):
    """Describes a Yamaha toggleable feature."""

    api_key: str


SWITCHES: tuple[YamahaSwitchDescription, ...] = (
    YamahaSwitchDescription(
        key="clear_voice",
        translation_key="clear_voice",
        api_key="clear voice",
        icon="mdi:account-voice",
    ),
    YamahaSwitchDescription(
        key="surround_3d",
        translation_key="surround_3d",
        api_key="3D surround",
        icon="mdi:surround-sound",
    ),
    YamahaSwitchDescription(
        key="bass_extension",
        translation_key="bass_extension",
        api_key="bass extension",
        icon="mdi:speaker",
    ),
    YamahaSwitchDescription(
        key="voice_control",
        translation_key="voice_control",
        api_key="voice control",
        icon="mdi:microphone",
    ),
    YamahaSwitchDescription(
        key="power_saving",
        translation_key="power_saving",
        api_key="power saving",
        icon="mdi:leaf",
    ),
    YamahaSwitchDescription(
        key="auto_power_stby",
        translation_key="auto_power_stby",
        api_key="Auto Power Stby",
        icon="mdi:timer-off",
    ),
    YamahaSwitchDescription(
        key="hdmi_control",
        translation_key="hdmi_control",
        api_key="HDMI Control",
        icon="mdi:hdmi-port",
    ),
    YamahaSwitchDescription(
        key="net_standby",
        translation_key="net_standby",
        api_key="NET Standby",
        icon="mdi:wifi",
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Yamaha switches from a config entry."""
    bucket = hass.data[DOMAIN][entry.entry_id]
    coordinator: YamahaCoordinator = bucket["coordinator"]
    uuid = entry.data.get(CONF_UUID) or entry.entry_id
    async_add_entities(
        YamahaSwitch(coordinator, uuid, description) for description in SWITCHES
    )


class YamahaSwitch(YamahaCoordinatorEntity, SwitchEntity):
    """A single toggleable Yamaha feature backed by YAMAHA_DATA_GET/SET."""

    entity_description: YamahaSwitchDescription

    def __init__(
        self,
        coordinator: YamahaCoordinator,
        uuid: str,
        description: YamahaSwitchDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{uuid}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data or {}
        yamaha = data.get("yamaha") or {}
        raw = yamaha.get(self.entity_description.api_key)
        if raw is None:
            return None
        return str(raw) == "1"

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.raw_command(
            _build_set_payload(self.entity_description.api_key, "1")
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.raw_command(
            _build_set_payload(self.entity_description.api_key, "0")
        )
        await self.coordinator.async_request_refresh()

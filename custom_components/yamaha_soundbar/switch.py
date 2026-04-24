"""Switch platform for Yamaha Soundbar."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_UUID, DOMAIN
from .coordinator import YamahaCoordinator
from .entity import YamahaCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Yamaha switches from a config entry."""
    bucket = hass.data[DOMAIN][entry.entry_id]
    coordinator: YamahaCoordinator = bucket["coordinator"]
    uuid = entry.data.get(CONF_UUID) or entry.entry_id
    async_add_entities([ClearVoiceSwitch(coordinator, uuid)])


class ClearVoiceSwitch(YamahaCoordinatorEntity, SwitchEntity):
    """Toggle the soundbar's Clear Voice enhancement."""

    _attr_has_entity_name = True
    _attr_translation_key = "clear_voice"

    def __init__(self, coordinator: YamahaCoordinator, uuid: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{uuid}_clear_voice"

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data or {}
        yamaha = data.get("yamaha") or {}
        raw = yamaha.get("clear voice")
        if raw is None:
            return None
        return str(raw) == "1"

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.raw_command(
            'YAMAHA_DATA_SET:{"clear voice":"1"}'
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.raw_command(
            'YAMAHA_DATA_SET:{"clear voice":"0"}'
        )
        await self.coordinator.async_request_refresh()

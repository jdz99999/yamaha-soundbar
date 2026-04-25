"""Number platform for Yamaha Soundbar."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._yamaha_codec import _build_set_payload
from .const import CONF_UUID, DOMAIN
from .coordinator import YamahaCoordinator
from .entity import YamahaCoordinatorEntity


@dataclass(frozen=True, kw_only=True)
class YamahaNumberDescription(NumberEntityDescription):
    """Describes a numeric Yamaha setting backed by YAMAHA_DATA_GET/SET."""

    api_key: str


NUMBERS: tuple[YamahaNumberDescription, ...] = (
    YamahaNumberDescription(
        key="subwoofer_volume",
        translation_key="subwoofer_volume",
        icon="mdi:speaker",
        api_key="subwoofer volume",
        native_min_value=-4,
        native_max_value=4,
        native_step=1,
        mode=NumberMode.SLIDER,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Yamaha number entities from a config entry."""
    bucket = hass.data[DOMAIN][entry.entry_id]
    coordinator: YamahaCoordinator = bucket["coordinator"]
    uuid = entry.data.get(CONF_UUID) or entry.entry_id
    async_add_entities(
        YamahaNumber(coordinator, uuid, description) for description in NUMBERS
    )


class YamahaNumber(YamahaCoordinatorEntity, NumberEntity):
    """A YAMAHA_DATA_GET/SET-backed integer setting (subwoofer volume, ...)."""

    entity_description: YamahaNumberDescription

    def __init__(
        self,
        coordinator: YamahaCoordinator,
        uuid: str,
        description: YamahaNumberDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{uuid}_{description.key}"

    @property
    def native_value(self) -> int | None:
        data = self.coordinator.data or {}
        yamaha = data.get("yamaha") or {}
        raw = yamaha.get(self.entity_description.api_key)
        if raw is None:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        # Bar clamps out-of-range, but clamp at the entity too so we never send
        # values the firmware would have to fix up. int(value) truncates toward
        # zero — HA's frontend already enforces step=1, but a service call could
        # pass a float, in which case we round-toward-zero and accept that.
        clamped = max(
            int(self.entity_description.native_min_value),
            min(int(self.entity_description.native_max_value), int(value)),
        )
        await self.coordinator.client.raw_command(
            _build_set_payload(self.entity_description.api_key, str(clamped))
        )
        await self.coordinator.async_request_refresh()

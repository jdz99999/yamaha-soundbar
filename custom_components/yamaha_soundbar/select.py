"""Select platform for Yamaha Soundbar."""

from __future__ import annotations

from dataclasses import dataclass, field

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_UUID, DOMAIN
from .coordinator import YamahaCoordinator
from .entity import YamahaCoordinatorEntity


@dataclass(frozen=True, kw_only=True)
class YamahaSelectDescription(SelectEntityDescription):
    """Describes a Yamaha multi-value selector backed by a Linkplay mode integer."""

    read_field: str
    mode_map: dict[int, tuple[str, str]] = field(default_factory=dict)


SELECTS: tuple[YamahaSelectDescription, ...] = (
    YamahaSelectDescription(
        key="input_source",
        translation_key="input_source",
        icon="mdi:video-input-hdmi",
        read_field="mode",
        mode_map={
            41: ("Bluetooth", "bluetooth"),
            43: ("TV", "optical"),
            49: ("HDMI", "HDMI"),
            31: ("Net", "wifi"),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Yamaha selects from a config entry."""
    bucket = hass.data[DOMAIN][entry.entry_id]
    coordinator: YamahaCoordinator = bucket["coordinator"]
    uuid = entry.data.get(CONF_UUID) or entry.entry_id
    async_add_entities(
        YamahaSelect(coordinator, uuid, description) for description in SELECTS
    )


class YamahaSelect(YamahaCoordinatorEntity, SelectEntity):
    """A Linkplay mode-int selector exposed as a Home Assistant select entity."""

    entity_description: YamahaSelectDescription

    def __init__(
        self,
        coordinator: YamahaCoordinator,
        uuid: str,
        description: YamahaSelectDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{uuid}_{description.key}"
        self._attr_options = [label for label, _ in description.mode_map.values()]

    @property
    def options(self) -> list[str]:
        return [label for label, _ in self.entity_description.mode_map.values()]

    @property
    def current_option(self) -> str | None:
        data = self.coordinator.data or {}
        player = data.get("player") or {}
        raw = player.get(self.entity_description.read_field)
        if raw is None:
            return None
        try:
            mode_int = int(raw)
        except (TypeError, ValueError):
            return None
        entry = self.entity_description.mode_map.get(mode_int)
        if entry is None:
            return None
        label, _ = entry
        return label

    async def async_select_option(self, option: str) -> None:
        for label, set_value in self.entity_description.mode_map.values():
            if label == option:
                await self.coordinator.client.set_player_cmd(
                    f"switchmode:{set_value}"
                )
                await self.coordinator.async_request_refresh()
                return
        raise ValueError(
            f"Option {option!r} is not valid for {self.entity_description.key}"
        )

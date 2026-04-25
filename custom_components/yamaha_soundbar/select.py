"""Select platform for Yamaha Soundbar."""

from __future__ import annotations

from dataclasses import dataclass, field

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._yamaha_codec import _build_set_payload
from .const import CONF_UUID, DOMAIN
from .coordinator import YamahaCoordinator
from .entity import YamahaCoordinatorEntity


@dataclass(frozen=True, kw_only=True)
class YamahaSelectDescription(SelectEntityDescription):
    """Describes a Yamaha multi-value selector backed by a Linkplay mode integer."""

    read_field: str
    mode_map: dict[int, tuple[str, str]] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class YamahaSoundProgramDescription(SelectEntityDescription):
    """Sound program / DSP preset, read+written via YAMAHA_DATA_GET/SET."""

    api_key: str
    valid_values: tuple[str, ...]


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


SOUND_PROGRAMS: tuple[YamahaSoundProgramDescription, ...] = (
    YamahaSoundProgramDescription(
        key="sound_program",
        translation_key="sound_program",
        icon="mdi:equalizer",
        api_key="sound program",
        valid_values=("movie", "music", "sports", "tv program", "game", "stereo"),
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
    entities: list[SelectEntity] = [
        YamahaSelect(coordinator, uuid, description) for description in SELECTS
    ]
    entities.extend(
        YamahaSoundProgramSelect(coordinator, uuid, description)
        for description in SOUND_PROGRAMS
    )
    async_add_entities(entities)


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


class YamahaSoundProgramSelect(YamahaCoordinatorEntity, SelectEntity):
    """A YAMAHA_DATA_GET/SET-backed selector (sound program / DSP preset)."""

    entity_description: YamahaSoundProgramDescription

    def __init__(
        self,
        coordinator: YamahaCoordinator,
        uuid: str,
        description: YamahaSoundProgramDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{uuid}_{description.key}"
        self._attr_options = list(description.valid_values)

    @property
    def options(self) -> list[str]:
        return list(self.entity_description.valid_values)

    @property
    def current_option(self) -> str | None:
        data = self.coordinator.data or {}
        yamaha = data.get("yamaha") or {}
        raw = yamaha.get(self.entity_description.api_key)
        if raw is None:
            return None
        if raw not in self.entity_description.valid_values:
            return None
        return raw

    async def async_select_option(self, option: str) -> None:
        if option not in self.entity_description.valid_values:
            raise ValueError(
                f"Option {option!r} is not valid for {self.entity_description.key}"
            )
        await self.coordinator.client.raw_command(
            _build_set_payload(self.entity_description.api_key, option)
        )
        await self.coordinator.async_request_refresh()

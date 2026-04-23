"""Coordinator for Yamaha device polling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import YamahaClient
from .const import DOMAIN


@dataclass(slots=True)
class YamahaState:
    """Normalized state model used by entities."""

    status: dict[str, Any]
    player: dict[str, Any]
    yamaha: dict[str, Any]


class YamahaCoordinator(DataUpdateCoordinator[YamahaState]):
    """Poll Yamaha state from a single API client."""

    def __init__(self, hass: HomeAssistant, client: YamahaClient) -> None:
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=5),
        )
        self.client = client

    async def _async_update_data(self) -> YamahaState:
        try:
            status = await self.client.get_status_ex()
            player = await self.client.get_player_status()
            yamaha = await self.client.get_yamaha_data()
            return YamahaState(status=status, player=player, yamaha=yamaha)
        except Exception as err:  # pragma: no cover - HA coordinator pattern
            raise UpdateFailed(f"Failed to update Yamaha state: {err}") from err

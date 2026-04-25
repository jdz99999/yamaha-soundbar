"""Coordinator for Yamaha device polling."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import YamahaClient

_LOGGER = logging.getLogger(__name__)

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=10)


class YamahaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll Yamaha state from a single API client."""

    def __init__(self, hass: HomeAssistant, client: YamahaClient, name: str) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=name,
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            status = await self.client.get_status_ex()
            player = await self.client.get_player_status()
            yamaha = await self.client.get_yamaha_data()
        except Exception as err:
            raise UpdateFailed(f"Failed to update Yamaha state: {err}") from err
        return {"status": status, "player": player, "yamaha": yamaha}

"""Support for Yamaha Linkplay A118 based devices."""

from __future__ import annotations

import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant

from .api import YamahaClient, YamahaClientConfig
from .const import DOMAIN, PLATFORMS
from .coordinator import YamahaCoordinator
from .services import async_register_services

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    bucket = hass.data[DOMAIN].setdefault(entry.entry_id, {"entities": []})

    host = entry.data[CONF_HOST]
    name = entry.data.get(CONF_NAME, host)

    if "client" not in bucket:
        bucket["client"] = YamahaClient(
            YamahaClientConfig(host=host, cert_dir=os.path.dirname(__file__))
        )
        _LOGGER.debug("YamahaClient ready for %s", host)

    if "coordinator" not in bucket:
        coordinator = YamahaCoordinator(
            hass, bucket["client"], name=f"{DOMAIN}_{entry.entry_id}"
        )
        bucket["coordinator"] = coordinator
        await coordinator.async_config_entry_first_refresh()

    async_register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        bucket = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        client = bucket.get("client")
        if client is not None:
            await client.close()
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)

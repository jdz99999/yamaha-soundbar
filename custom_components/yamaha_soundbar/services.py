"""Service handlers for Yamaha Soundbar integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_BASS,
    ATTR_CMD,
    ATTR_MASTER,
    ATTR_MUTE,
    ATTR_NOTIF,
    ATTR_POWER_SAVING,
    ATTR_PRESET,
    ATTR_SNAP,
    ATTR_SOUND,
    ATTR_SUB,
    ATTR_SURROUND,
    ATTR_TRACK,
    ATTR_VOICE,
    DOMAIN,
    SERVICE_CMD,
    SERVICE_JOIN,
    SERVICE_PLAY,
    SERVICE_PRESET,
    SERVICE_REST,
    SERVICE_SNAP,
    SERVICE_SOUND,
    SERVICE_UNJOIN,
)

SERVICE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.comp_entity_ids})
JOIN_SERVICE_SCHEMA = SERVICE_SCHEMA.extend({vol.Required(ATTR_MASTER): cv.entity_id})
PRESET_BUTTON_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
        vol.Required(ATTR_PRESET): cv.positive_int,
    }
)
CMND_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
        vol.Required(ATTR_CMD): cv.string,
        vol.Optional(ATTR_NOTIF, default=True): cv.boolean,
    }
)
REST_SERVICE_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids})
SNAP_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids, vol.Optional(ATTR_SNAP, default=True): cv.boolean}
)
PLYTRK_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTITY_ID): cv.entity_id, vol.Required(ATTR_TRACK): cv.template}
)
SOUND_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional(ATTR_SOUND): cv.string,
        vol.Optional(ATTR_SUB): int,
        vol.Optional(ATTR_SURROUND): cv.boolean,
        vol.Optional(ATTR_VOICE): cv.boolean,
        vol.Optional(ATTR_BASS): cv.boolean,
        vol.Optional(ATTR_MUTE): cv.boolean,
        vol.Optional(ATTR_POWER_SAVING): cv.boolean,
    }
)

_LOGGER = logging.getLogger(__name__)


def _get_target_entities(hass: HomeAssistant, entity_ids: list[str] | str | None) -> list[Any]:
    all_entities: list[Any] = []
    for bucket in hass.data.get(DOMAIN, {}).values():
        if isinstance(bucket, dict):
            all_entities.extend(bucket.get("entities", []))

    if not entity_ids or entity_ids == "all":
        resolved = all_entities
    else:
        resolved = [entity for entity in all_entities if entity.entity_id in entity_ids]

    _LOGGER.debug("Resolved %d target entities: %s", len(resolved), [ent.entity_id for ent in resolved])
    return resolved


def async_register_services(hass: HomeAssistant) -> None:
    """Register domain services once."""
    if hass.services.has_service(DOMAIN, SERVICE_JOIN):
        return

    async def async_service_handle(service: ServiceCall) -> None:
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        entities = _get_target_entities(hass, entity_ids)

        if service.service == SERVICE_JOIN:
            all_entities = _get_target_entities(hass, "all")
            master = [
                entity
                for entity in all_entities
                if entity.entity_id == service.data[ATTR_MASTER]
            ]
            if master:
                client_entities = [entity for entity in entities if entity.entity_id != master[0].entity_id]
                await master[0].async_join(client_entities)

        elif service.service == SERVICE_UNJOIN:
            masters = [entity for entity in entities if entity.is_master]
            if masters:
                for master in masters:
                    await master.async_unjoin_all()
            else:
                for entity in entities:
                    await entity.async_unjoin_me()

        elif service.service == SERVICE_PRESET:
            preset = service.data.get(ATTR_PRESET)
            for entity in entities:
                await entity.async_preset_button(preset)

        elif service.service == SERVICE_CMD:
            command = service.data.get(ATTR_CMD)
            notify = service.data.get(ATTR_NOTIF)
            for entity in entities:
                await entity.async_execute_command(command, notify)

        elif service.service == SERVICE_SNAP:
            switchinput = service.data.get(ATTR_SNAP)
            for entity in entities:
                await entity.async_snapshot(switchinput)

        elif service.service == SERVICE_REST:
            for entity in entities:
                await entity.async_restore()

        elif service.service == SERVICE_PLAY:
            track = service.data.get(ATTR_TRACK)
            for entity in entities:
                await entity.async_play_track(track)

        elif service.service == SERVICE_SOUND:
            settings = {
                key: service.data.get(key)
                for key in [
                    ATTR_SOUND,
                    ATTR_SUB,
                    ATTR_SURROUND,
                    ATTR_VOICE,
                    ATTR_BASS,
                    ATTR_POWER_SAVING,
                    ATTR_MUTE,
                ]
            }
            for entity in entities:
                await entity.async_set_sound(settings)

    hass.services.async_register(DOMAIN, SERVICE_JOIN, async_service_handle, schema=JOIN_SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_UNJOIN, async_service_handle, schema=SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_PRESET, async_service_handle, schema=PRESET_BUTTON_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CMD, async_service_handle, schema=CMND_SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SNAP, async_service_handle, schema=SNAP_SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REST, async_service_handle, schema=REST_SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_PLAY, async_service_handle, schema=PLYTRK_SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SOUND, async_service_handle, schema=SOUND_SERVICE_SCHEMA)

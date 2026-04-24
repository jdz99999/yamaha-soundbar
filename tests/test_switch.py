"""Tests for the Clear Voice switch entity."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.yamaha_soundbar.coordinator import YamahaCoordinator
from custom_components.yamaha_soundbar.switch import ClearVoiceSwitch


def _coordinator_with(data, mock_client) -> YamahaCoordinator:
    coord = MagicMock(spec=YamahaCoordinator)
    coord.data = data
    coord.client = mock_client
    coord.async_request_refresh = AsyncMock()
    coord.last_update_success = True
    return coord


def test_clear_voice_is_on_when_value_is_one(mock_client) -> None:
    coord = _coordinator_with({"yamaha": {"clear voice": "1"}}, mock_client)
    entity = ClearVoiceSwitch(coord, "uuid-123")
    assert entity.is_on is True


def test_clear_voice_is_off_when_value_is_zero(mock_client) -> None:
    coord = _coordinator_with({"yamaha": {"clear voice": "0"}}, mock_client)
    entity = ClearVoiceSwitch(coord, "uuid-123")
    assert entity.is_on is False


def test_clear_voice_is_none_when_key_missing(mock_client) -> None:
    coord = _coordinator_with({"yamaha": {}}, mock_client)
    entity = ClearVoiceSwitch(coord, "uuid-123")
    assert entity.is_on is None


def test_clear_voice_is_none_when_data_missing(mock_client) -> None:
    coord = _coordinator_with(None, mock_client)
    entity = ClearVoiceSwitch(coord, "uuid-123")
    assert entity.is_on is None


def test_clear_voice_unique_id_composes_from_uuid(mock_client) -> None:
    coord = _coordinator_with({}, mock_client)
    entity = ClearVoiceSwitch(coord, "uuid-ABC")
    assert entity.unique_id == "uuid-ABC_clear_voice"


@pytest.mark.asyncio
async def test_clear_voice_turn_on_sends_raw_command(mock_client) -> None:
    coord = _coordinator_with({"yamaha": {"clear voice": "0"}}, mock_client)
    entity = ClearVoiceSwitch(coord, "uuid-123")

    await entity.async_turn_on()

    mock_client.raw_command.assert_awaited_once()
    call_args = mock_client.raw_command.await_args.args[0]
    assert call_args == 'YAMAHA_DATA_SET:{"clear voice":"1"}'
    coord.async_request_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_clear_voice_turn_off_sends_raw_command(mock_client) -> None:
    coord = _coordinator_with({"yamaha": {"clear voice": "1"}}, mock_client)
    entity = ClearVoiceSwitch(coord, "uuid-123")

    await entity.async_turn_off()

    mock_client.raw_command.assert_awaited_once()
    call_args = mock_client.raw_command.await_args.args[0]
    assert call_args == 'YAMAHA_DATA_SET:{"clear voice":"0"}'
    coord.async_request_refresh.assert_awaited_once()


def test_clear_voice_has_translation_key(mock_client) -> None:
    coord = _coordinator_with({}, mock_client)
    entity = ClearVoiceSwitch(coord, "uuid")
    assert entity._attr_translation_key == "clear_voice"
    assert entity._attr_has_entity_name is True

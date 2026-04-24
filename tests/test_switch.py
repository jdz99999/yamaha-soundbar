"""Tests for the Yamaha switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.yamaha_soundbar.coordinator import YamahaCoordinator
from custom_components.yamaha_soundbar.switch import (
    SWITCHES,
    YamahaSwitch,
    _build_set_payload,
)


def _coordinator_with(data, mock_client) -> YamahaCoordinator:
    coord = MagicMock(spec=YamahaCoordinator)
    coord.data = data
    coord.client = mock_client
    coord.async_request_refresh = AsyncMock()
    coord.last_update_success = True
    return coord


def test_eight_switches_are_registered() -> None:
    """Guard against accidental removal of entries in SWITCHES."""
    assert len(SWITCHES) == 8
    keys = {d.key for d in SWITCHES}
    assert keys == {
        "clear_voice",
        "surround_3d",
        "bass_extension",
        "voice_control",
        "power_saving",
        "auto_power_stby",
        "hdmi_control",
        "net_standby",
    }


def test_net_standby_is_disabled_by_default() -> None:
    """Net Standby must not auto-enable — toggling it off can soft-brick the integration."""
    net_standby = next(d for d in SWITCHES if d.key == "net_standby")
    assert net_standby.entity_registry_enabled_default is False
    for description in SWITCHES:
        if description.key != "net_standby":
            # Other switches default to enabled (the SwitchEntityDescription default).
            assert description.entity_registry_enabled_default is True


@pytest.mark.parametrize(
    ("api_key", "value", "expected"),
    [
        ("clear voice", "1", "YAMAHA_DATA_SET:{%22clear%20voice%22:%221%22}"),
        ("3D surround", "0", "YAMAHA_DATA_SET:{%223D%20surround%22:%220%22}"),
        ("HDMI Control", "1", "YAMAHA_DATA_SET:{%22HDMI%20Control%22:%221%22}"),
    ],
)
def test_build_set_payload_produces_half_encoded_string(
    api_key: str, value: str, expected: str
) -> None:
    assert _build_set_payload(api_key, value) == expected


@pytest.mark.parametrize("description", SWITCHES, ids=lambda d: d.key)
def test_unique_id_composes_from_uuid_and_key(description, mock_client) -> None:
    coord = _coordinator_with({}, mock_client)
    entity = YamahaSwitch(coord, "uuid-ABC", description)
    assert entity.unique_id == f"uuid-ABC_{description.key}"


@pytest.mark.parametrize("description", SWITCHES, ids=lambda d: d.key)
def test_is_on_reads_api_key_from_coordinator(description, mock_client) -> None:
    coord = _coordinator_with({"yamaha": {description.api_key: "1"}}, mock_client)
    on_entity = YamahaSwitch(coord, "uuid", description)
    assert on_entity.is_on is True

    coord_off = _coordinator_with({"yamaha": {description.api_key: "0"}}, mock_client)
    off_entity = YamahaSwitch(coord_off, "uuid", description)
    assert off_entity.is_on is False

    coord_missing = _coordinator_with({"yamaha": {}}, mock_client)
    missing_entity = YamahaSwitch(coord_missing, "uuid", description)
    assert missing_entity.is_on is None


def test_is_on_returns_none_when_coordinator_data_is_none(mock_client) -> None:
    description = SWITCHES[0]
    coord = _coordinator_with(None, mock_client)
    entity = YamahaSwitch(coord, "uuid", description)
    assert entity.is_on is None


@pytest.mark.asyncio
@pytest.mark.parametrize("description", SWITCHES, ids=lambda d: d.key)
async def test_turn_on_sends_half_encoded_payload(description, mock_client) -> None:
    coord = _coordinator_with({"yamaha": {description.api_key: "0"}}, mock_client)
    entity = YamahaSwitch(coord, "uuid", description)

    await entity.async_turn_on()

    mock_client.raw_command.assert_awaited_once()
    sent = mock_client.raw_command.await_args.args[0]
    assert sent == _build_set_payload(description.api_key, "1")
    assert sent.startswith("YAMAHA_DATA_SET:{%22")
    assert sent.endswith(':%221%22}')
    coord.async_request_refresh.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("description", SWITCHES, ids=lambda d: d.key)
async def test_turn_off_sends_half_encoded_payload(description, mock_client) -> None:
    coord = _coordinator_with({"yamaha": {description.api_key: "1"}}, mock_client)
    entity = YamahaSwitch(coord, "uuid", description)

    await entity.async_turn_off()

    mock_client.raw_command.assert_awaited_once()
    sent = mock_client.raw_command.await_args.args[0]
    assert sent == _build_set_payload(description.api_key, "0")
    assert sent.endswith(':%220%22}')
    coord.async_request_refresh.assert_awaited_once()


@pytest.mark.parametrize("description", SWITCHES, ids=lambda d: d.key)
def test_translation_key_matches_description(description, mock_client) -> None:
    coord = _coordinator_with({}, mock_client)
    entity = YamahaSwitch(coord, "uuid", description)
    assert entity.entity_description.translation_key == description.key
    assert entity._attr_has_entity_name is True

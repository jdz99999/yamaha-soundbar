"""Tests for the Yamaha select platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.yamaha_soundbar.coordinator import YamahaCoordinator
from custom_components.yamaha_soundbar.select import (
    SELECTS,
    YamahaSelect,
    YamahaSelectDescription,
)


def _coordinator_with(data, mock_client) -> YamahaCoordinator:
    coord = MagicMock(spec=YamahaCoordinator)
    coord.data = data
    coord.client = mock_client
    coord.async_request_refresh = AsyncMock()
    coord.last_update_success = True
    return coord


@pytest.fixture
def input_source_description() -> YamahaSelectDescription:
    return next(d for d in SELECTS if d.key == "input_source")


def test_one_select_is_registered() -> None:
    """Guard against accidental removal/addition. This session ships exactly one select."""
    assert len(SELECTS) == 1
    assert SELECTS[0].key == "input_source"


def test_input_source_mode_map_matches_yas209_probe(
    input_source_description: YamahaSelectDescription,
) -> None:
    """Lock the verified YAS-209 mode integers so a future edit can't silently regress them."""
    assert input_source_description.read_field == "mode"
    assert input_source_description.mode_map == {
        41: ("Bluetooth", "bluetooth"),
        43: ("TV", "optical"),
        49: ("HDMI", "HDMI"),
        31: ("Net", "wifi"),
    }


def test_options_lists_labels_in_map_order(
    input_source_description, mock_client
) -> None:
    coord = _coordinator_with({"player": {}}, mock_client)
    entity = YamahaSelect(coord, "uuid", input_source_description)
    assert entity.options == ["Bluetooth", "TV", "HDMI", "Net"]


@pytest.mark.parametrize(
    ("mode_value", "expected_label"),
    [
        ("41", "Bluetooth"),
        ("43", "TV"),
        ("49", "HDMI"),
        ("31", "Net"),
        (41, "Bluetooth"),  # int form too
        (49, "HDMI"),
    ],
)
def test_current_option_maps_known_modes(
    mode_value, expected_label, input_source_description, mock_client
) -> None:
    coord = _coordinator_with({"player": {"mode": mode_value}}, mock_client)
    entity = YamahaSelect(coord, "uuid", input_source_description)
    assert entity.current_option == expected_label


@pytest.mark.parametrize("mode_value", ["99", "0", "-1", 99, 0])
def test_current_option_returns_none_for_unknown_mode(
    mode_value, input_source_description, mock_client
) -> None:
    coord = _coordinator_with({"player": {"mode": mode_value}}, mock_client)
    entity = YamahaSelect(coord, "uuid", input_source_description)
    assert entity.current_option is None


def test_current_option_none_when_player_missing(
    input_source_description, mock_client
) -> None:
    coord = _coordinator_with({}, mock_client)
    entity = YamahaSelect(coord, "uuid", input_source_description)
    assert entity.current_option is None


def test_current_option_none_when_data_none(
    input_source_description, mock_client
) -> None:
    coord = _coordinator_with(None, mock_client)
    entity = YamahaSelect(coord, "uuid", input_source_description)
    assert entity.current_option is None


def test_current_option_none_when_mode_field_missing(
    input_source_description, mock_client
) -> None:
    coord = _coordinator_with({"player": {"status": "play"}}, mock_client)
    entity = YamahaSelect(coord, "uuid", input_source_description)
    assert entity.current_option is None


def test_current_option_none_when_mode_unparsable(
    input_source_description, mock_client
) -> None:
    coord = _coordinator_with({"player": {"mode": "garbage"}}, mock_client)
    entity = YamahaSelect(coord, "uuid", input_source_description)
    assert entity.current_option is None


def test_unique_id_composes_from_uuid_and_key(
    input_source_description, mock_client
) -> None:
    coord = _coordinator_with({"player": {}}, mock_client)
    entity = YamahaSelect(coord, "uuid-XYZ", input_source_description)
    assert entity.unique_id == "uuid-XYZ_input_source"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("option", "expected_subcommand"),
    [
        ("Bluetooth", "switchmode:bluetooth"),
        ("TV", "switchmode:optical"),
        ("HDMI", "switchmode:HDMI"),
        ("Net", "switchmode:wifi"),
    ],
)
async def test_select_option_sends_set_player_cmd(
    option, expected_subcommand, input_source_description, mock_client
) -> None:
    coord = _coordinator_with({"player": {"mode": "31"}}, mock_client)
    entity = YamahaSelect(coord, "uuid", input_source_description)

    await entity.async_select_option(option)

    mock_client.set_player_cmd.assert_awaited_once_with(expected_subcommand)
    coord.async_request_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_select_option_unknown_label_raises_value_error(
    input_source_description, mock_client
) -> None:
    """Picked behavior: raise ValueError for unknown options.

    HA's SelectEntity already validates via the entity registry / UI, so an unknown
    option only arrives via a misuse of the service call API. Failing loud is more
    debuggable than silently no-op'ing.
    """
    coord = _coordinator_with({"player": {"mode": "31"}}, mock_client)
    entity = YamahaSelect(coord, "uuid", input_source_description)

    with pytest.raises(ValueError):
        await entity.async_select_option("AUX")

    mock_client.set_player_cmd.assert_not_awaited()
    coord.async_request_refresh.assert_not_awaited()


def test_translation_key_matches_description(
    input_source_description, mock_client
) -> None:
    coord = _coordinator_with({"player": {}}, mock_client)
    entity = YamahaSelect(coord, "uuid", input_source_description)
    assert entity.entity_description.translation_key == "input_source"
    assert entity._attr_has_entity_name is True

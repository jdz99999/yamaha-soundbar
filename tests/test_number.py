"""Tests for the Yamaha number platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.yamaha_soundbar._yamaha_codec import _build_set_payload
from custom_components.yamaha_soundbar.coordinator import YamahaCoordinator
from custom_components.yamaha_soundbar.number import (
    NUMBERS,
    PLAYER_NUMBERS,
    YamahaNumber,
    YamahaNumberDescription,
    YamahaPlayerNumber,
    YamahaPlayerNumberDescription,
)


def _coordinator_with(data, mock_client) -> YamahaCoordinator:
    coord = MagicMock(spec=YamahaCoordinator)
    coord.data = data
    coord.client = mock_client
    coord.async_request_refresh = AsyncMock()
    coord.last_update_success = True
    return coord


@pytest.fixture
def subwoofer_description() -> YamahaNumberDescription:
    return next(d for d in NUMBERS if d.key == "subwoofer_volume")


def test_one_number_is_registered() -> None:
    """Pin the NUMBERS tuple shape — a future addition should fail this loudly."""
    assert len(NUMBERS) == 1
    assert NUMBERS[0].key == "subwoofer_volume"


def test_subwoofer_description_pins_yas209_range(
    subwoofer_description: YamahaNumberDescription,
) -> None:
    """Lock the verified -4..+4 range against accidental edits."""
    assert subwoofer_description.api_key == "subwoofer volume"
    assert subwoofer_description.native_min_value == -4
    assert subwoofer_description.native_max_value == 4
    assert subwoofer_description.native_step == 1


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("0", 0), ("-4", -4), ("4", 4), ("1", 1), ("-2", -2)],
)
def test_native_value_parses_string_int(
    raw, expected, subwoofer_description, mock_client
) -> None:
    coord = _coordinator_with(
        {"yamaha": {subwoofer_description.api_key: raw}}, mock_client
    )
    entity = YamahaNumber(coord, "uuid", subwoofer_description)
    assert entity.native_value == expected


def test_native_value_returns_none_when_key_missing(
    subwoofer_description, mock_client
) -> None:
    coord = _coordinator_with({"yamaha": {}}, mock_client)
    entity = YamahaNumber(coord, "uuid", subwoofer_description)
    assert entity.native_value is None


def test_native_value_returns_none_when_data_none(
    subwoofer_description, mock_client
) -> None:
    coord = _coordinator_with(None, mock_client)
    entity = YamahaNumber(coord, "uuid", subwoofer_description)
    assert entity.native_value is None


def test_native_value_returns_none_when_unparsable(
    subwoofer_description, mock_client
) -> None:
    coord = _coordinator_with(
        {"yamaha": {subwoofer_description.api_key: "not a number"}}, mock_client
    )
    entity = YamahaNumber(coord, "uuid", subwoofer_description)
    assert entity.native_value is None


def test_unique_id_composes_from_uuid_and_key(
    subwoofer_description, mock_client
) -> None:
    coord = _coordinator_with({"yamaha": {}}, mock_client)
    entity = YamahaNumber(coord, "uuid-XYZ", subwoofer_description)
    assert entity.unique_id == "uuid-XYZ_subwoofer_volume"


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [0, -4, 4])
async def test_set_native_value_sends_half_encoded_payload(
    value, subwoofer_description, mock_client
) -> None:
    coord = _coordinator_with(
        {"yamaha": {subwoofer_description.api_key: "0"}}, mock_client
    )
    entity = YamahaNumber(coord, "uuid", subwoofer_description)

    await entity.async_set_native_value(value)

    mock_client.raw_command.assert_awaited_once()
    sent = mock_client.raw_command.await_args.args[0]
    assert sent == _build_set_payload(
        subwoofer_description.api_key, str(value)
    )
    coord.async_request_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_native_value_for_two_is_exact_string(
    subwoofer_description, mock_client
) -> None:
    """Pin the byte-exact wire format — guards both the codec and the description glue."""
    coord = _coordinator_with(
        {"yamaha": {subwoofer_description.api_key: "0"}}, mock_client
    )
    entity = YamahaNumber(coord, "uuid", subwoofer_description)

    await entity.async_set_native_value(2)

    sent = mock_client.raw_command.await_args.args[0]
    assert sent == "YAMAHA_DATA_SET:{%22subwoofer%20volume%22:%222%22}"


@pytest.mark.asyncio
async def test_set_native_value_for_negative_three_is_exact_string(
    subwoofer_description, mock_client
) -> None:
    """The minus sign stays literal — explicitly verified."""
    coord = _coordinator_with(
        {"yamaha": {subwoofer_description.api_key: "0"}}, mock_client
    )
    entity = YamahaNumber(coord, "uuid", subwoofer_description)

    await entity.async_set_native_value(-3)

    sent = mock_client.raw_command.await_args.args[0]
    assert sent == "YAMAHA_DATA_SET:{%22subwoofer%20volume%22:%22-3%22}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("input_value", "expected_int"),
    [(-99, -4), (-5, -4), (5, 4), (99, 4), (1000, 4)],
)
async def test_set_native_value_clamps_out_of_range(
    input_value, expected_int, subwoofer_description, mock_client
) -> None:
    coord = _coordinator_with(
        {"yamaha": {subwoofer_description.api_key: "0"}}, mock_client
    )
    entity = YamahaNumber(coord, "uuid", subwoofer_description)

    await entity.async_set_native_value(input_value)

    sent = mock_client.raw_command.await_args.args[0]
    assert sent == _build_set_payload(
        subwoofer_description.api_key, str(expected_int)
    )


def test_translation_key_matches_description(
    subwoofer_description, mock_client
) -> None:
    coord = _coordinator_with({"yamaha": {}}, mock_client)
    entity = YamahaNumber(coord, "uuid", subwoofer_description)
    assert entity.entity_description.translation_key == "subwoofer_volume"
    assert entity._attr_has_entity_name is True


# ---------------------------------------------------------------------------
# Volume player number (YamahaPlayerNumber)
# ---------------------------------------------------------------------------


@pytest.fixture
def volume_description() -> YamahaPlayerNumberDescription:
    return next(d for d in PLAYER_NUMBERS if d.key == "volume")


def test_one_player_number_is_registered() -> None:
    assert len(PLAYER_NUMBERS) == 1
    assert PLAYER_NUMBERS[0].key == "volume"


def test_volume_description_pins_yas209_range(
    volume_description: YamahaPlayerNumberDescription,
) -> None:
    """Lock the verified 0..100 range and the read/set field names."""
    assert volume_description.read_field == "vol"
    assert volume_description.set_subcommand == "vol"
    assert volume_description.native_min_value == 0
    assert volume_description.native_max_value == 100
    assert volume_description.native_step == 1


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("0", 0), ("50", 50), ("100", 100), ("23", 23)],
)
def test_volume_native_value_parses_string_int(
    raw, expected, volume_description, mock_client
) -> None:
    coord = _coordinator_with(
        {"player": {volume_description.read_field: raw}}, mock_client
    )
    entity = YamahaPlayerNumber(coord, "uuid", volume_description)
    assert entity.native_value == expected


def test_volume_native_value_returns_none_when_key_missing(
    volume_description, mock_client
) -> None:
    coord = _coordinator_with({"player": {}}, mock_client)
    entity = YamahaPlayerNumber(coord, "uuid", volume_description)
    assert entity.native_value is None


def test_volume_native_value_returns_none_when_data_none(
    volume_description, mock_client
) -> None:
    coord = _coordinator_with(None, mock_client)
    entity = YamahaPlayerNumber(coord, "uuid", volume_description)
    assert entity.native_value is None


def test_volume_native_value_returns_none_when_unparsable(
    volume_description, mock_client
) -> None:
    coord = _coordinator_with(
        {"player": {volume_description.read_field: "not a number"}}, mock_client
    )
    entity = YamahaPlayerNumber(coord, "uuid", volume_description)
    assert entity.native_value is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("input_value", "expected_subcommand"),
    [
        (0, "vol:0"),
        (50.0, "vol:50"),
        (42, "vol:42"),
        (100, "vol:100"),
    ],
)
async def test_volume_set_native_value_sends_set_player_cmd(
    input_value, expected_subcommand, volume_description, mock_client
) -> None:
    coord = _coordinator_with(
        {"player": {volume_description.read_field: "0"}}, mock_client
    )
    entity = YamahaPlayerNumber(coord, "uuid", volume_description)

    await entity.async_set_native_value(input_value)

    mock_client.set_player_cmd.assert_awaited_once_with(expected_subcommand)
    coord.async_request_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_volume_set_native_value_for_42_is_exact_string(
    volume_description, mock_client
) -> None:
    """Pin: a value of 42 produces literally 'vol:42' on the wire."""
    coord = _coordinator_with(
        {"player": {volume_description.read_field: "0"}}, mock_client
    )
    entity = YamahaPlayerNumber(coord, "uuid", volume_description)

    await entity.async_set_native_value(42)

    assert mock_client.set_player_cmd.await_args.args[0] == "vol:42"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("input_value", "expected_subcommand"),
    [
        (-50, "vol:0"),
        (-1, "vol:0"),
        (101, "vol:100"),
        (200, "vol:100"),
        (999.9, "vol:100"),
    ],
)
async def test_volume_set_native_value_clamps_out_of_range(
    input_value, expected_subcommand, volume_description, mock_client
) -> None:
    coord = _coordinator_with(
        {"player": {volume_description.read_field: "50"}}, mock_client
    )
    entity = YamahaPlayerNumber(coord, "uuid", volume_description)

    await entity.async_set_native_value(input_value)

    mock_client.set_player_cmd.assert_awaited_once_with(expected_subcommand)


def test_volume_unique_id(volume_description, mock_client) -> None:
    coord = _coordinator_with({"player": {}}, mock_client)
    entity = YamahaPlayerNumber(coord, "uuid-XYZ", volume_description)
    assert entity.unique_id == "uuid-XYZ_volume"


def test_volume_translation_key_matches(volume_description, mock_client) -> None:
    coord = _coordinator_with({"player": {}}, mock_client)
    entity = YamahaPlayerNumber(coord, "uuid", volume_description)
    assert entity.entity_description.translation_key == "volume"
    assert entity._attr_has_entity_name is True

"""Tests for the Yamaha sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import EntityCategory

from custom_components.yamaha_soundbar.coordinator import YamahaCoordinator
from custom_components.yamaha_soundbar.sensor import (
    PLAYER_MAPPED_SENSORS,
    STATUS_SENSORS,
    YAMAHA_SENSORS,
    YamahaPlayerMappedSensor,
    YamahaStatusSensor,
    YamahaYamahaSensor,
)


def _coordinator_with(data, mock_client) -> YamahaCoordinator:
    coord = MagicMock(spec=YamahaCoordinator)
    coord.data = data
    coord.client = mock_client
    coord.async_request_refresh = AsyncMock()
    coord.last_update_success = True
    return coord


@pytest.fixture
def audio_stream_description():
    return next(d for d in YAMAHA_SENSORS if d.key == "audio_stream")


@pytest.fixture
def rssi_description():
    return next(d for d in STATUS_SENSORS if d.key == "rssi")


@pytest.fixture
def firmware_system_description():
    return next(d for d in YAMAHA_SENSORS if d.key == "firmware_system")


# ---------------------------------------------------------------------------
# Inventory pins
# ---------------------------------------------------------------------------


def test_yamaha_sensor_keys() -> None:
    """Pin: 1 audio_stream + 5 firmware sensors."""
    assert {d.key for d in YAMAHA_SENSORS} == {
        "audio_stream",
        "firmware_system",
        "firmware_a118",
        "firmware_mcu",
        "firmware_dsp",
        "firmware_hdmi",
    }


def test_status_sensor_keys() -> None:
    """Pin: only RSSI for now."""
    assert {d.key for d in STATUS_SENSORS} == {"rssi"}


def test_audio_stream_is_not_diagnostic(audio_stream_description) -> None:
    """Audio Stream should be enabled-by-default and user-visible (not diagnostic)."""
    assert audio_stream_description.entity_category is None
    assert audio_stream_description.entity_registry_enabled_default is True
    assert audio_stream_description.api_key == "Audio Stream"


@pytest.mark.parametrize(
    "key",
    [
        "firmware_system",
        "firmware_a118",
        "firmware_mcu",
        "firmware_dsp",
        "firmware_hdmi",
    ],
)
def test_firmware_sensors_are_diagnostic_and_disabled(key) -> None:
    description = next(d for d in YAMAHA_SENSORS if d.key == key)
    assert description.entity_category == EntityCategory.DIAGNOSTIC
    assert description.entity_registry_enabled_default is False


def test_firmware_api_keys_match_yas209_yamaha_data_blob() -> None:
    """Pin the literal api_key spellings — these are how the bar emits them."""
    by_key = {d.key: d.api_key for d in YAMAHA_SENSORS}
    assert by_key["firmware_system"] == "System Version"
    assert by_key["firmware_a118"] == "A118"
    assert by_key["firmware_mcu"] == "MCU"
    assert by_key["firmware_dsp"] == "DSP(FW)"
    assert by_key["firmware_hdmi"] == "HDMI"


def test_rssi_description_metadata(rssi_description) -> None:
    assert rssi_description.read_field == "RSSI"
    assert rssi_description.native_unit_of_measurement == "dBm"
    assert rssi_description.device_class == SensorDeviceClass.SIGNAL_STRENGTH
    assert rssi_description.state_class == SensorStateClass.MEASUREMENT
    assert rssi_description.entity_category == EntityCategory.DIAGNOSTIC


# ---------------------------------------------------------------------------
# YAMAHA_DATA_GET-sourced sensors (audio_stream + firmware blob)
# ---------------------------------------------------------------------------


def test_audio_stream_returns_off_string(
    audio_stream_description, mock_client
) -> None:
    coord = _coordinator_with(
        {"yamaha": {"Audio Stream": "OFF"}}, mock_client
    )
    entity = YamahaYamahaSensor(coord, "uuid", audio_stream_description)
    assert entity.native_value == "OFF"


@pytest.mark.parametrize("value", ["PCM", "Dolby Digital", "DTS", "OFF"])
def test_audio_stream_passes_through_arbitrary_strings(
    value, audio_stream_description, mock_client
) -> None:
    """Audio Stream is a freeform string sensor — no enum validation."""
    coord = _coordinator_with({"yamaha": {"Audio Stream": value}}, mock_client)
    entity = YamahaYamahaSensor(coord, "uuid", audio_stream_description)
    assert entity.native_value == value


def test_audio_stream_returns_none_when_key_missing(
    audio_stream_description, mock_client
) -> None:
    coord = _coordinator_with({"yamaha": {}}, mock_client)
    entity = YamahaYamahaSensor(coord, "uuid", audio_stream_description)
    assert entity.native_value is None


def test_audio_stream_returns_none_when_data_none(
    audio_stream_description, mock_client
) -> None:
    coord = _coordinator_with(None, mock_client)
    entity = YamahaYamahaSensor(coord, "uuid", audio_stream_description)
    assert entity.native_value is None


def test_firmware_system_returns_string_value(
    firmware_system_description, mock_client
) -> None:
    coord = _coordinator_with(
        {"yamaha": {"System Version": "05.31"}}, mock_client
    )
    entity = YamahaYamahaSensor(coord, "uuid", firmware_system_description)
    assert entity.native_value == "05.31"


def test_firmware_system_returns_none_when_key_missing(
    firmware_system_description, mock_client
) -> None:
    coord = _coordinator_with({"yamaha": {}}, mock_client)
    entity = YamahaYamahaSensor(coord, "uuid", firmware_system_description)
    assert entity.native_value is None


def test_yamaha_yamaha_sensor_unique_id(
    audio_stream_description, mock_client
) -> None:
    coord = _coordinator_with({"yamaha": {}}, mock_client)
    entity = YamahaYamahaSensor(coord, "uuid-XYZ", audio_stream_description)
    assert entity.unique_id == "uuid-XYZ_audio_stream"


# ---------------------------------------------------------------------------
# getStatusEx-sourced sensors (RSSI)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("-21", -21), ("-90", -90), ("0", 0), ("-1", -1)],
)
def test_rssi_native_value_int_coerces(
    raw, expected, rssi_description, mock_client
) -> None:
    coord = _coordinator_with({"status": {"RSSI": raw}}, mock_client)
    entity = YamahaStatusSensor(coord, "uuid", rssi_description)
    assert entity.native_value == expected
    assert isinstance(entity.native_value, int)


def test_rssi_native_value_none_when_unparsable(
    rssi_description, mock_client
) -> None:
    coord = _coordinator_with({"status": {"RSSI": "not a number"}}, mock_client)
    entity = YamahaStatusSensor(coord, "uuid", rssi_description)
    assert entity.native_value is None


def test_rssi_native_value_none_when_key_missing(
    rssi_description, mock_client
) -> None:
    coord = _coordinator_with({"status": {}}, mock_client)
    entity = YamahaStatusSensor(coord, "uuid", rssi_description)
    assert entity.native_value is None


def test_rssi_native_value_none_when_data_none(
    rssi_description, mock_client
) -> None:
    coord = _coordinator_with(None, mock_client)
    entity = YamahaStatusSensor(coord, "uuid", rssi_description)
    assert entity.native_value is None


def test_rssi_unique_id(rssi_description, mock_client) -> None:
    coord = _coordinator_with({"status": {}}, mock_client)
    entity = YamahaStatusSensor(coord, "uuid-XYZ", rssi_description)
    assert entity.unique_id == "uuid-XYZ_rssi"


def test_rssi_has_entity_name(rssi_description, mock_client) -> None:
    coord = _coordinator_with({"status": {}}, mock_client)
    entity = YamahaStatusSensor(coord, "uuid", rssi_description)
    assert entity._attr_has_entity_name is True
    assert entity.entity_description.translation_key == "rssi"


# ---------------------------------------------------------------------------
# Player mapped sensor (input_mode)
# ---------------------------------------------------------------------------


@pytest.fixture
def input_mode_description():
    return next(d for d in PLAYER_MAPPED_SENSORS if d.key == "input_mode")


def test_one_player_mapped_sensor_is_registered() -> None:
    assert len(PLAYER_MAPPED_SENSORS) == 1
    assert PLAYER_MAPPED_SENSORS[0].key == "input_mode"


def test_input_mode_options_match_yas209_probe(input_mode_description) -> None:
    """Pin the four labels exactly — these must stay in sync with select.py."""
    assert input_mode_description.options == ["Bluetooth", "TV", "HDMI", "Net"]
    assert input_mode_description.read_field == "mode"


def test_input_mode_device_class_is_enum(input_mode_description) -> None:
    assert input_mode_description.device_class == SensorDeviceClass.ENUM


def test_input_mode_mode_map_pinned(input_mode_description) -> None:
    """Lock the 4 mode_int → label mappings against accidental edits."""
    assert input_mode_description.mode_map == {
        41: "Bluetooth",
        43: "TV",
        49: "HDMI",
        31: "Net",
    }


@pytest.mark.parametrize(
    ("raw_mode", "expected_label"),
    [
        ("41", "Bluetooth"),
        ("43", "TV"),
        ("49", "HDMI"),
        ("31", "Net"),
        (41, "Bluetooth"),
        (43, "TV"),
        (49, "HDMI"),
        (31, "Net"),
    ],
)
def test_input_mode_native_value_for_known_modes(
    raw_mode, expected_label, input_mode_description, mock_client
) -> None:
    coord = _coordinator_with({"player": {"mode": raw_mode}}, mock_client)
    entity = YamahaPlayerMappedSensor(coord, "uuid", input_mode_description)
    assert entity.native_value == expected_label


def test_input_mode_native_value_none_for_unknown_int(
    input_mode_description, mock_client
) -> None:
    coord = _coordinator_with({"player": {"mode": "99"}}, mock_client)
    entity = YamahaPlayerMappedSensor(coord, "uuid", input_mode_description)
    assert entity.native_value is None


def test_input_mode_native_value_none_for_unparsable(
    input_mode_description, mock_client
) -> None:
    coord = _coordinator_with(
        {"player": {"mode": "not a number"}}, mock_client
    )
    entity = YamahaPlayerMappedSensor(coord, "uuid", input_mode_description)
    assert entity.native_value is None


def test_input_mode_native_value_none_when_mode_key_missing(
    input_mode_description, mock_client
) -> None:
    coord = _coordinator_with({"player": {"vol": "50"}}, mock_client)
    entity = YamahaPlayerMappedSensor(coord, "uuid", input_mode_description)
    assert entity.native_value is None


def test_input_mode_native_value_none_when_player_missing(
    input_mode_description, mock_client
) -> None:
    coord = _coordinator_with({}, mock_client)
    entity = YamahaPlayerMappedSensor(coord, "uuid", input_mode_description)
    assert entity.native_value is None


def test_input_mode_native_value_none_when_data_none(
    input_mode_description, mock_client
) -> None:
    coord = _coordinator_with(None, mock_client)
    entity = YamahaPlayerMappedSensor(coord, "uuid", input_mode_description)
    assert entity.native_value is None


def test_input_mode_unique_id(input_mode_description, mock_client) -> None:
    coord = _coordinator_with({"player": {}}, mock_client)
    entity = YamahaPlayerMappedSensor(coord, "uuid-XYZ", input_mode_description)
    assert entity.unique_id == "uuid-XYZ_input_mode"


def test_input_mode_translation_key(input_mode_description, mock_client) -> None:
    coord = _coordinator_with({"player": {}}, mock_client)
    entity = YamahaPlayerMappedSensor(coord, "uuid", input_mode_description)
    assert entity._attr_has_entity_name is True
    assert entity.entity_description.translation_key == "input_mode"

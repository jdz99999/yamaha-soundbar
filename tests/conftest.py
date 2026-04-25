"""Shared fixtures for Yamaha Soundbar tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.yamaha_soundbar.api import YamahaClient, YamahaClientConfig


@pytest.fixture
def mock_client() -> Generator[MagicMock, None, None]:
    """Return a MagicMock shaped like YamahaClient.

    Methods are AsyncMocks by default; tests configure per-case return values.
    """
    client = MagicMock(spec=YamahaClient)
    client.get_status_ex = AsyncMock()
    client.get_player_status = AsyncMock()
    client.get_yamaha_data = AsyncMock()
    client.raw_command = AsyncMock(return_value="OK")
    client.set_player_cmd = AsyncMock(return_value="OK")
    client.close = AsyncMock()
    yield client


@pytest.fixture
def sample_status_ex() -> dict:
    """A plausible subset of getStatusEx response payload."""
    return {
        "uuid": "FF31F09E0123ABCD",
        "DeviceName": "Soundbar Living Room",
        "firmware": "4.6.415145",
        "hardware": "A118",
        "project": "YAS-209",
        "MAC": "AA:BB:CC:DD:EE:FF",
    }


@pytest.fixture
def sample_yamaha_data() -> dict:
    """A plausible YAMAHA_DATA_GET response payload."""
    return {
        "clear voice": "0",
        "bass extension": "0",
        "surround": "0",
        "sound program": "stereo",
        "subwoofer": "50",
    }


@pytest.fixture
def client_config(tmp_path) -> YamahaClientConfig:
    """Return a YamahaClientConfig pointed at a temp dir (no cert files)."""
    return YamahaClientConfig(host="10.0.0.99", cert_dir=str(tmp_path), timeout=5)

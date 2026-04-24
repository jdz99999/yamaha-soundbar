"""Tests for YamahaCoordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.yamaha_soundbar.coordinator import YamahaCoordinator


@pytest.mark.asyncio
async def test_coordinator_merges_status_and_yamaha_payloads(
    hass, mock_client, sample_status_ex, sample_yamaha_data
) -> None:
    """_async_update_data should return {'status': ..., 'yamaha': ...}."""
    mock_client.get_status_ex.return_value = sample_status_ex
    mock_client.get_yamaha_data.return_value = sample_yamaha_data

    coordinator = YamahaCoordinator(hass, mock_client, name="test")
    data = await coordinator._async_update_data()

    assert data["status"] == sample_status_ex
    assert data["yamaha"] == sample_yamaha_data
    assert mock_client.get_status_ex.await_count == 1
    assert mock_client.get_yamaha_data.await_count == 1


@pytest.mark.asyncio
async def test_coordinator_wraps_exceptions_in_update_failed(
    hass, mock_client
) -> None:
    """Any client exception should be wrapped in UpdateFailed."""
    mock_client.get_status_ex = AsyncMock(side_effect=RuntimeError("boom"))

    coordinator = YamahaCoordinator(hass, mock_client, name="test")
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_update_interval_is_ten_seconds(hass, mock_client) -> None:
    """Default polling interval should be 10s per the v4 design."""
    coordinator = YamahaCoordinator(hass, mock_client, name="test")
    assert coordinator.update_interval.total_seconds() == 10

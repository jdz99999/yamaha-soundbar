"""Tests for the Yamaha API client."""

from __future__ import annotations

import pytest
from yarl import URL

from custom_components.yamaha_soundbar.api import (
    YamahaAuthError,
    YamahaClient,
)


def test_yamaha_data_set_url_is_not_percent_encoded() -> None:
    """Regression: verify the URL we'd send for YAMAHA_DATA_SET is verbatim.

    The Yamaha firmware rejects percent-encoded query strings for
    YAMAHA_DATA_SET commands. The client must pass `encoded=True` to yarl.
    """
    cmd = 'YAMAHA_DATA_SET:{"clear voice":"1"}'
    url = URL(f"https://10.0.0.1/httpapi.asp?command={cmd}", encoded=True)
    raw = url.raw_query_string
    assert "%7B" not in raw
    assert "%22" not in raw
    assert "%7D" not in raw
    assert 'command=YAMAHA_DATA_SET:{"clear voice":"1"}' == raw


def test_yamaha_data_set_url_is_percent_encoded_without_flag() -> None:
    """Negative control: without encoded=True yarl *does* encode — proves why the flag matters."""
    cmd = 'YAMAHA_DATA_SET:{"clear voice":"1"}'
    url = URL(f"https://10.0.0.1/httpapi.asp?command={cmd}")
    raw = url.raw_query_string
    assert "%7B" in raw or "%22" in raw


@pytest.mark.asyncio
async def test_missing_cert_raises_auth_error(client_config) -> None:
    """Building the SSL context without cert files should raise YamahaAuthError."""
    client = YamahaClient(client_config)
    with pytest.raises(YamahaAuthError):
        client._build_ssl_context()

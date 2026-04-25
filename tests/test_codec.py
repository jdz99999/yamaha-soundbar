"""Direct tests for the YAMAHA_DATA_SET payload codec."""

from __future__ import annotations

import pytest

from custom_components.yamaha_soundbar._yamaha_codec import _build_set_payload


@pytest.mark.parametrize(
    ("api_key", "value", "expected"),
    [
        (
            "clear voice",
            "1",
            "YAMAHA_DATA_SET:{%22clear%20voice%22:%221%22}",
        ),
        (
            "subwoofer volume",
            "-3",
            "YAMAHA_DATA_SET:{%22subwoofer%20volume%22:%22-3%22}",
        ),
        (
            "sound program",
            "tv program",
            "YAMAHA_DATA_SET:{%22sound%20program%22:%22tv%20program%22}",
        ),
    ],
)
def test_build_set_payload_half_encodes_key_and_value(
    api_key: str, value: str, expected: str
) -> None:
    """Spaces in either argument become %20; other chars (incl. minus) stay literal."""
    assert _build_set_payload(api_key, value) == expected


def test_minus_sign_is_not_encoded() -> None:
    """Negative integer values must keep the literal '-' so the firmware parses them."""
    payload = _build_set_payload("subwoofer volume", "-4")
    assert "-4" in payload
    assert "%2D" not in payload  # explicit guard against future percent-encoding regression

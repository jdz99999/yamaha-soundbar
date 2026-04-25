"""Internal helpers for encoding Yamaha HTTP API payloads.

The Yamaha A118 firmware accepts a half-encoded YAMAHA_DATA_SET payload —
quotes as %22, spaces as %20, but braces, colon, and the value's other chars
left literal. Fully-encoded URLs and fully-literal URLs both produce HTTP 400
from the device's parser. Verified against YAS-209 firmware on 2026-04-24.

Lives in its own module so switch / select / number platforms can share it
without circular imports.
"""

from __future__ import annotations


def _build_set_payload(api_key: str, value: str) -> str:
    """Build a half-encoded YAMAHA_DATA_SET payload.

    Spaces in the api_key and the value are %20-encoded; everything else
    (including the leading minus on negative integers) stays literal.
    """
    encoded_key = api_key.replace(" ", "%20")
    encoded_value = value.replace(" ", "%20")
    return f"YAMAHA_DATA_SET:{{%22{encoded_key}%22:%22{encoded_value}%22}}"

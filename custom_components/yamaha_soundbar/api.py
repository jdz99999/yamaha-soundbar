"""Yamaha HTTP API client."""

from __future__ import annotations

import asyncio
import logging
import os
import ssl
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

import aiohttp
from yarl import URL

_LOGGER = logging.getLogger(__name__)


class YamahaAuthError(Exception):
    """Raised when mTLS auth material is missing or invalid."""


@dataclass(slots=True)
class YamahaClientConfig:
    """Connection configuration for Yamaha soundbar."""

    host: str
    cert_dir: str
    timeout: int = 10


class YamahaClient:
    """Small async client for Yamaha Linkplay endpoints."""

    def __init__(self, config: YamahaClientConfig) -> None:
        self._config = config
        self._timeout = aiohttp.ClientTimeout(total=config.timeout)
        self._ssl_ctx: ssl.SSLContext | None = None
        self._session: aiohttp.ClientSession | None = None

    def _build_ssl_context(self) -> ssl.SSLContext:
        crt_path = os.path.join(self._config.cert_dir, "yamaha_client.crt")
        key_path = os.path.join(self._config.cert_dir, "yamaha_client.key")
        pem_path = os.path.join(self._config.cert_dir, "client.pem")

        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        if os.path.exists(crt_path) and os.path.exists(key_path):
            ctx.load_cert_chain(crt_path, key_path)
        elif os.path.exists(pem_path):
            ctx.load_cert_chain(pem_path)
        else:
            raise YamahaAuthError("Missing Yamaha client certificate")

        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session and not self._session.closed:
            return self._session

        if self._ssl_ctx is None:
            self._ssl_ctx = await asyncio.get_running_loop().run_in_executor(None, self._build_ssl_context)
            _LOGGER.debug("SSL context built")

        connector = aiohttp.TCPConnector(ssl_context=self._ssl_ctx)
        self._session = aiohttp.ClientSession(connector=connector, timeout=self._timeout)
        return self._session

    async def close(self) -> None:
        """Close reused aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(self, command: str, expect_json: bool = False) -> Any:
        session = await self._ensure_session()
        # Yamaha firmware requires YAMAHA_DATA_SET payloads verbatim.
        # yarl would otherwise percent-encode '{', '}', '"' and turn space into '+'.
        url = URL(
            f"https://{self._config.host}/httpapi.asp?command={command}",
            encoded=True,
        )
        async with session.get(url) as response:
            if response.status != HTTPStatus.OK:
                raise aiohttp.ClientError(f"Unexpected status code {response.status}")
            if expect_json:
                return await response.json(content_type=None)
            return await response.text()

    async def get_status_ex(self) -> dict[str, Any]:
        """Return parsed `getStatusEx` payload."""
        data = await self._request("getStatusEx", expect_json=True)
        if not isinstance(data, dict):
            raise ValueError("Invalid status response payload")
        return data

    async def get_player_status(self) -> dict[str, Any]:
        """Return parsed `getPlayerStatus` payload."""
        data = await self._request("getPlayerStatus", expect_json=True)
        if not isinstance(data, dict):
            raise ValueError("Invalid player status payload")
        return data

    async def get_yamaha_data(self) -> dict[str, Any]:
        """Return parsed `YAMAHA_DATA_GET` payload."""
        data = await self._request("YAMAHA_DATA_GET", expect_json=True)
        if not isinstance(data, dict):
            raise ValueError("Invalid Yamaha data payload")
        return data

    async def raw_command(self, cmd: str) -> str:
        """Execute raw command string and return response body."""
        response = await self._request(cmd, expect_json=False)
        return response.strip()

    async def set_player_cmd(self, subcommand: str) -> str:
        """Send a setPlayerCmd:<subcommand> request.

        These are plain commands (no half-encoding) per the Linkplay HTTP API.
        Examples: switchmode:wifi, vol:30, pause, play, next.
        """
        return await self.raw_command(f"setPlayerCmd:{subcommand}")

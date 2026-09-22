"""Async client for Brain.fm's unofficial API."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

BRAINFM_API_BASE = "https://api.brain.fm/api/v1"
BRAINFM_STREAM_BASE = "https://stream.brain.fm"


class BrainfmError(Exception):
    """Base exception for Brain.fm API errors."""


class LoginFailed(BrainfmError):
    """Raised when authentication fails."""


class TokenError(BrainfmError):
    """Raised when stream token request fails."""


class APIError(BrainfmError):
    """Raised for unexpected API responses."""


class BrainfmClient:
    """Async wrapper around Brain.fm's unofficial HTTP API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def login(self, email: str, password: str) -> str:
        """Authenticate and return session token.

        Raises LoginFailed on invalid credentials.
        """
        url = f"{BRAINFM_API_BASE}/login"
        payload = {"email": email, "password": password}
        async with self._session.post(url, json=payload) as resp:
            if resp.status == 401 or resp.status == 403:
                raise LoginFailed("Invalid email or password")
            if resp.status != 200:
                raise APIError(f"Login failed with status {resp.status}")
            data: dict[str, Any] = await resp.json()
            token = data.get("token")
            if not token:
                raise APIError("Login response missing token")
            return token

    async def get_stations(self, session_token: str) -> list[dict[str, Any]]:
        """Fetch available stations from the API.

        Returns a list of station dicts with at least 'id' and 'name' keys.
        """
        url = f"{BRAINFM_API_BASE}/stations"
        headers = {"Authorization": f"Bearer {session_token}"}
        async with self._session.get(url, headers=headers) as resp:
            if resp.status != 200:
                raise APIError(f"Station list failed with status {resp.status}")
            data: dict[str, Any] = await resp.json()
            return data.get("stations", [])

    async def get_stream_token(self, session_token: str, station_id: int) -> str:
        """Get a short-lived stream token for a station.

        Raises TokenError on failure.
        """
        url = f"{BRAINFM_API_BASE}/get-token"
        headers = {"Authorization": f"Bearer {session_token}"}
        payload = {"stationId": station_id}
        async with self._session.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                raise TokenError(f"Token request failed with status {resp.status}")
            data: dict[str, Any] = await resp.json()
            token = data.get("token")
            if not token:
                raise TokenError("Token response missing token")
            return token

    def make_stream_url(self, stream_token: str) -> str:
        """Build the HTTP stream URL from a token."""
        return f"{BRAINFM_STREAM_BASE}/?tkn={stream_token}"

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        await self._session.close()

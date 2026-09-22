"""Async client for Brain.fm's unofficial API."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

BRAINFM_API_BASE = "https://api.brain.fm/v2"
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
        self._cf_bm: str | None = None
    async def login(self, email: str, password: str, *, cf_bm: str | None = None) -> str:
        """Authenticate and return session token.

        Raises LoginFailed on invalid credentials.
        """
        self._cf_bm = cf_bm
        url = f"{BRAINFM_API_BASE}/auth/email-login"
        payload = {"email": email, "password": password}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://my.brain.fm",
            "Referer": "https://my.brain.fm/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }
        if cf_bm:
            headers["Cookie"] = f"__cf_bm={cf_bm}"
        logger.debug("Brain.fm login request to %s (cf_bm=%s)", url, bool(cf_bm))
        last_exc: Exception | None = None
        for attempt in range(4):
            if attempt > 0:
                delay = min(2 ** attempt * 2, 30)
                logger.debug("Retrying login in %ds (attempt %d/4)", delay, attempt + 1)
                await asyncio.sleep(delay)
            async with self._session.post(url, json=payload, headers=headers) as resp:
                body_text = await resp.text()
                logger.debug("Brain.fm login response: status=%d body=%s", resp.status, body_text[:200])
                if resp.status == 200:
                    try:
                        data: dict[str, Any] = await resp.json()
                    except Exception:
                        data = {}
                    token = data.get("token")
                    if not token:
                        raise APIError(f"Login response missing token: {body_text[:200]}")
                    return token
                error_msg = body_text.lower()
                if "incorrect" in error_msg or "invalid" in error_msg or "password" in error_msg:
                    raise LoginFailed(f"Invalid email or password: {body_text[:200]}")
                if resp.status == 429:
                    last_exc = APIError("Rate limited by Cloudflare (429)")
                    continue
                if resp.status in (400, 401, 403):
                    raise LoginFailed(f"Login rejected ({resp.status}): {body_text[:200]}")
                raise APIError(f"Login failed with status {resp.status}: {body_text[:200]}")
        raise last_exc  # type: ignore[misc]

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
        url = f"{BRAINFM_API_BASE}/tokens"
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

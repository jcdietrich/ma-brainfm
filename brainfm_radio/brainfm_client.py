"""Async client for Brain.fm's unofficial API (v3)."""
from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

BRAINFM_API_BASE = "https://api.brain.fm/v2"
BRAINFM_API_V3 = "https://api.brain.fm/v3"


class BrainfmError(Exception):
    """Base exception for Brain.fm API errors."""


class LoginFailed(BrainfmError):
    """Raised when authentication fails."""


class TokenError(BrainfmError):
    """Raised when stream token request fails."""


class APIError(BrainfmError):
    """Raised for unexpected API responses."""


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    """Decode JWT payload (no signature verification — we just need the user ID)."""
    parts = token.split(".")
    if len(parts) < 2:
        raise ValueError("Invalid JWT format")
    payload_b64 = parts[1]
    # Add padding
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding
    decoded = base64.urlsafe_b64decode(payload_b64)
    return json.loads(decoded)


class BrainfmClient:
    """Async wrapper around Brain.fm's unofficial HTTP API (v3)."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._cf_bm: str | None = None

    def _headers(self, token: str | None = None) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://my.brain.fm",
            "Referer": "https://my.brain.fm/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/137.0.0.0 Safari/537.36",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if self._cf_bm:
            headers["Cookie"] = f"__cf_bm={self._cf_bm}"
        return headers

    async def login(self, email: str, password: str, *, cf_bm: str | None = None) -> str:
        """Authenticate and return session token.

        Raises LoginFailed on invalid credentials.
        """
        self._cf_bm = cf_bm
        url = f"{BRAINFM_API_BASE}/auth/email-login"
        payload = {"email": email, "password": password}
        headers = self._headers()
        headers["Content-Type"] = "application/json"

        logger.debug("Brain.fm login request to %s (cf_bm=%s)", url, bool(cf_bm))
        async with self._session.post(url, json=payload, headers=headers) as resp:
            body_text = await resp.text()
            logger.debug("Brain.fm login response: status=%d body=%s", resp.status, body_text[:200])
            if resp.status == 200:
                try:
                    data: dict[str, Any] = await resp.json()
                except Exception:
                    data = {}
                token = data.get("token") or data.get("result")
                if not token:
                    raise APIError(f"Login response missing token: {body_text[:200]}")
                return token
            error_msg = body_text.lower()
            if "incorrect" in error_msg or "invalid" in error_msg or "password" in error_msg:
                raise LoginFailed(f"Invalid email or password: {body_text[:200]}")
            if resp.status == 429:
                raise APIError(
                    "Rate limited by Cloudflare (429). "
                    "Wait 5-10 minutes before trying again. "
                    "If this keeps happening, copy the __cf_bm cookie from your browser "
                    "(DevTools → Application → Cookies → api.brain.fm) into the provider config."
                )
            if resp.status in (400, 401, 403):
                raise LoginFailed(f"Login rejected ({resp.status}): {body_text[:200]}")
            raise APIError(f"Login failed with status {resp.status}: {body_text[:200]}")

    def get_user_id(self, token: str) -> str:
        """Extract user ID from JWT token."""
        payload = _decode_jwt_payload(token)
        user_id = payload.get("_id") or payload.get("sub") or payload.get("userId")
        if not user_id:
            raise APIError(f"Could not extract user ID from token: {list(payload.keys())}")
        return user_id

    async def get_activities(self, token: str, mode: str) -> list[dict[str, Any]]:
        """Fetch activities for a mode (focus, relax, sleep).

        Returns list of activity dicts with id, displayValue, description, etc.
        """
        url = f"{BRAINFM_API_V3}/mentalStates/dynamic/{mode}/activities"
        headers = self._headers(token)
        async with self._session.get(url, headers=headers) as resp:
            body_text = await resp.text()
            logger.debug("Brain.fm activities response: status=%d body=%s", resp.status, body_text[:300])
            if resp.status != 200:
                raise APIError(f"Activities request failed with status {resp.status}: {body_text[:200]}")
            data: dict[str, Any] = await resp.json()
            return data.get("activities", data.get("result", []))

    async def create_session(
        self,
        token: str,
        user_id: str,
        activity_id: str,
        *,
        genre_names: list[str] | None = None,
        neural_effect_level: str = "High",
    ) -> dict[str, Any]:
        """Create a listening session and return session info with stream URL.

        Returns dict with keys: tokenedUrl, cdnUrl, lengthInSeconds, etc.
        """
        url = f"{BRAINFM_API_V3}/users/{user_id}/sessions?platform=web"
        headers = self._headers(token)
        headers["Content-Type"] = "application/json"
        payload: dict[str, Any] = {
            "dynamicActivityId": activity_id,
            "version": 3,
            "genreNames": genre_names or [],
            "neuralEffectLevels": [neural_effect_level],
        }
        async with self._session.post(url, json=payload, headers=headers) as resp:
            body_text = await resp.text()
            logger.debug("Brain.fm session response: status=%d body=%s", resp.status, body_text[:500])
            if resp.status != 200:
                raise APIError(f"Session creation failed with status {resp.status}: {body_text[:200]}")
            data: dict[str, Any] = await resp.json()
            result = data.get("result", data)
            track_variation = result.get("trackVariation", result)
            return track_variation

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        await self._session.close()

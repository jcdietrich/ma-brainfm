"""Interactive setup flow for Brain.fm credentials."""
from __future__ import annotations
from typing import Any, TYPE_CHECKING
import logging

from music_assistant_models.config_entries import ConfigEntry
from music_assistant_models.enums import ConfigEntryType

from music_assistant.models.setup_flow import SetupSession

from .brainfm_client import BrainfmClient, BrainfmError, LoginFailed, APIError

import aiohttp

logger = logging.getLogger(__name__)


ENTRIES = [
    ConfigEntry(
        key="email",
        type=ConfigEntryType.STRING,
        label="Email",
        required=True,
    ),
    ConfigEntry(
        key="password",
        type=ConfigEntryType.SECURE_STRING,
        label="Password",
        required=True,
    ),
    ConfigEntry(
        key="cookie",
        type=ConfigEntryType.SECURE_STRING,
        label="Cloudflare Cookie (__cf_bm)",
        description="From browser DevTools → Application → Cookies → api.brain.fm → __cf_bm",
        required=False,
    ),
]


async def run_setup(session: SetupSession) -> None:
    """Run the interactive setup for Brain.fm credentials."""
    errors: dict[str, str] | None = None
    error_detail: str | None = None
    while True:
        kwargs: dict[str, Any] = {
            "entries": ENTRIES,
            "step_id": "credentials",
            "last_step": True,
        }
        if errors:
            kwargs["errors"] = errors
        if error_detail:
            kwargs["translation_params"] = [error_detail]
        values = await session.form(**kwargs)
        email = str(values["email"])
        password = str(values["password"])
        cookie = str(values.get("cookie", "")) or None
        errors = None
        error_detail = None
        try:
            async with aiohttp.ClientSession() as http_session:
                client = BrainfmClient(http_session)
                token = await client.login(email, password, cf_bm=cookie)
        except LoginFailed as err:
            logger.warning("Brain.fm login failed (invalid credentials): %s", err)
            errors = {"base": "invalid_credentials"}
            error_detail = str(err)
            continue
        except APIError as err:
            logger.warning("Brain.fm login API error: %s", err)
            msg = str(err).lower()
            if "429" in str(err) or "rate limit" in msg:
                errors = {"base": "rate_limited"}
            else:
                errors = {"base": "api_error"}
            error_detail = str(err)
            continue
        except BrainfmError as err:
            logger.warning("Brain.fm login connection error: %s", err)
            errors = {"base": "connection_error"}
            error_detail = str(err)
            continue
        await session.finish({"email": email, "password": password, "cookie": cookie})
        return
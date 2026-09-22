"""Interactive setup flow for Brain.fm credentials."""
from __future__ import annotations

from music_assistant_models.config_entries import ConfigEntry
from music_assistant_models.enums import ConfigEntryType

from music_assistant.models.setup_flow import SetupSession

from .brainfm_client import BrainfmClient, BrainfmError, LoginFailed, APIError

import aiohttp


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
]


async def run_setup(session: SetupSession) -> None:
    """Run the interactive setup for Brain.fm credentials."""
    errors: dict[str, str] | None = None
    while True:
        values = await session.form(
            ENTRIES, step_id="credentials", errors=errors, last_step=True
        )
        email = str(values["email"])
        password = str(values["password"])
        try:
            async with aiohttp.ClientSession() as http_session:
                client = BrainfmClient(http_session)
                token = await client.login(email, password)
        except LoginFailed:
            errors = {"base": "invalid_credentials"}
            continue
        except APIError as err:
            if "429" in str(err):
                errors = {"base": "rate_limited"}
            else:
                errors = {"base": "api_error"}
            continue
        except BrainfmError as err:
            errors = {"base": "connection_error"}
            continue
        await session.finish({"email": email, "password": password})
        return
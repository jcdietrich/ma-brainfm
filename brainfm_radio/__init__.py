"""Brain.fm Radio provider for Music Assistant."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator, Sequence
from typing import TYPE_CHECKING

from music_assistant_models.enums import ContentType, MediaType, ProviderFeature, StreamType
from music_assistant_models.media_items import (
    AudioFormat,
    BrowseFolder,
    ItemMapping,
    MediaItemType,
    Radio,
    ProviderMapping,
)
from music_assistant_models.streamdetails import StreamDetails

from music_assistant.models.music_provider import MusicProvider

from .brainfm_client import BrainfmClient, BrainfmError
from .constants import CATEGORIES, MODES

if TYPE_CHECKING:
    from music_assistant_models.config_entries import ConfigEntry, ProviderConfig
    from music_assistant_models.provider import ProviderManifest
    from music_assistant.mass import MusicAssistant
    from music_assistant.models import ProviderInstanceType

import aiohttp

logger = logging.getLogger(__name__)

SUPPORTED_FEATURES = {
    ProviderFeature.BROWSE,
}


async def setup(
    mass: MusicAssistant, manifest: ProviderManifest, config: ProviderConfig
) -> ProviderInstanceType:
    """Initialize provider(instance) with given configuration."""
    return BrainfmRadioProvider(mass, manifest, config, SUPPORTED_FEATURES)


class BrainfmRadioProvider(MusicProvider):
    """Brain.fm Radio provider — streams focus, relax, and sleep stations."""

    _client: BrainfmClient | None = None
    _session_token: str | None = None
    _user_id: str | None = None
    _activities: dict[str, list[dict]] | None = None

    async def loaded_in_mass(self) -> None:
        """Authenticate and fetch activities for all modes."""
        email = self.get_setup_value("email")
        password = self.get_setup_value("password")
        cookie = self.get_setup_value("cookie")

        if not email or not password:
            logger.error("Brain.fm credentials not configured")
            return

        http_session = aiohttp.ClientSession()
        self._client = BrainfmClient(http_session)

        try:
            self._session_token = await self._client.login(email, password, cf_bm=cookie)
            self._user_id = self._client.get_user_id(self._session_token)
            logger.info("Brain.fm logged in as user %s", self._user_id)

            # Fetch activities for all modes
            self._activities = {}
            for i, mode in enumerate(MODES):
                try:
                    activities = await self._client.get_activities(self._session_token, mode)
                    self._activities[mode] = activities
                    logger.info("Brain.fm %s mode: %d activities", mode, len(activities))
                except BrainfmError as err:
                    logger.warning("Failed to fetch %s activities: %s", mode, err)
                    self._activities[mode] = []
                if i < len(MODES) - 1:
                    await asyncio.sleep(0.5)

        except BrainfmError as err:
            logger.error("Failed to authenticate with Brain.fm: %s", err)

    async def unload(self, is_removed: bool = False) -> None:
        """Clean up resources."""
        if self._client:
            await self._client.close()

    @property
    def is_streaming_provider(self) -> bool:
        """Brain.fm is a streaming provider."""
        return True

    async def browse(self, path: str) -> Sequence[MediaItemType | ItemMapping | BrowseFolder]:
        """Browse Brain.fm stations grouped by category."""
        logger.debug("Brain.fm browse called with path=%r, activities=%s", path, bool(self._activities))
        if path == "" or path == "brainfm://":
            # Return top-level categories
            return [
                BrowseFolder(
                    item_id=f"brainfm://{cat}",
                    provider=self.instance_id,
                    name=cat,
                )
                for cat in CATEGORIES
            ]

        if path.startswith("brainfm://"):
            category = path.replace("brainfm://", "")
            activities = self._get_activities_for_category(category)
            logger.debug(
                "Brain.fm browse category=%r found %d activities", category, len(activities)
            )
            return [
                Radio(
                    item_id=a["id"],
                    provider=self.instance_id,
                    name=a.get("displayValue", a.get("name", "Unknown")),
                    provider_mappings={
                        ProviderMapping(
                            item_id=a["id"],
                            provider_domain=self.domain,
                            provider_instance=self.instance_id,
                            available=True,
                            audio_format=AudioFormat(
                                content_type=ContentType.MPEG,
                            ),
                        )
                    },
                )
                for a in activities
            ]
        return []

    def _get_activities_for_category(self, category: str) -> list[dict]:
        """Get activities filtered by category, using live data or fallback."""
        mode = category.lower()
        if self._activities and mode in self._activities:
            return self._activities[mode]
        return []

    async def get_stream_details(self, item_id: str, media_type: MediaType) -> StreamDetails:
        """Get stream details for a Brain.fm activity."""
        if not self._client or not self._session_token or not self._user_id:
            raise BrainfmError("Provider not initialized — check credentials")

        session_info = await self._client.create_session(
            self._session_token,
            self._user_id,
            item_id,
        )
        stream_url = session_info.get("tokenedUrl") or session_info.get("cdnUrl", "")
        if not stream_url:
            raise BrainfmError("No stream URL in session response")

        return StreamDetails(
            provider=self.instance_id,
            item_id=item_id,
            audio_format=AudioFormat(
                content_type=ContentType.MPEG,
            ),
            media_type=MediaType.RADIO,
            stream_type=StreamType.HTTP,
            path=stream_url,
            allow_seek=False,
            can_seek=False,
        )

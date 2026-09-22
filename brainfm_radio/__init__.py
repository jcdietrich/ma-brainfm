"""Brain.fm Radio provider for Music Assistant."""
from __future__ import annotations

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
from .constants import CATEGORIES, STATIONS

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
    _stations: list[dict] | None = None

    async def loaded_in_mass(self) -> None:
        """Authenticate and fetch station list."""
        email = self.get_config_value("email")
        password = self.get_config_value("password")

        if not email or not password:
            logger.error("Brain.fm credentials not configured")
            return

        http_session = aiohttp.ClientSession()
        self._client = BrainfmClient(http_session)

        try:
            self._session_token = await self._client.login(email, password)
            self._stations = await self._client.get_stations(self._session_token)
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
            stations = self._get_stations_for_category(category)
            return [
                Radio(
                    item_id=str(s["id"]),
                    provider=self.instance_id,
                    name=s["name"],
                    provider_mappings={
                        ProviderMapping(
                            item_id=str(s["id"]),
                            provider_domain=self.domain,
                            provider_instance=self.instance_id,
                            available=True,
                            audio_format=AudioFormat(
                                content_type=ContentType.MPEG,
                            ),
                        )
                    },
                )
                for s in stations
            ]

        return []

    def _get_stations_for_category(self, category: str) -> list[dict]:
        """Get stations filtered by category, using live data or fallback."""
        if self._stations:
            return [s for s in self._stations if s.get("category") == category]
        return [s for s in STATIONS if s["category"] == category]

    async def get_stream_details(self, item_id: str, media_type: MediaType) -> StreamDetails:
        """Get stream details for a Brain.fm station."""
        if not self._client or not self._session_token:
            raise BrainfmError("Provider not initialized — check credentials")

        station_id = int(item_id)
        stream_token = await self._client.get_stream_token(self._session_token, station_id)
        stream_url = self._client.make_stream_url(stream_token)

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

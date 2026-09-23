"""Tests for BrainfmRadioProvider (v3 API)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from brainfm_radio.brainfm_client import BrainfmClient, BrainfmError


@pytest.fixture
def mock_mass():
    mass = MagicMock()
    mass.config = MagicMock()
    return mass


@pytest.fixture
def mock_manifest():
    manifest = MagicMock()
    manifest.domain = "brainfm_radio"
    return manifest


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.get_value = MagicMock(side_effect=lambda key, default=None: {
        "email": "user@example.com",
        "password": "testpass",
        "token": "test-token",
    }.get(key, default))
    return config


@pytest.fixture
def provider(mock_mass, mock_manifest, mock_config):
    from brainfm_radio import BrainfmRadioProvider, SUPPORTED_FEATURES
    p = BrainfmRadioProvider(mock_mass, mock_manifest, mock_config, SUPPORTED_FEATURES)
    return p


def test_supported_features():
    from brainfm_radio import BrainfmRadioProvider, SUPPORTED_FEATURES
    from music_assistant_models.enums import ProviderFeature
    assert ProviderFeature.BROWSE in SUPPORTED_FEATURES


def test_is_streaming_provider(provider):
    assert provider.is_streaming_provider is True


@pytest.mark.asyncio
async def test_browse_root_returns_categories(provider):
    result = await provider.browse("brainfm://")
    assert len(result) == 3  # Focus, Relax, Sleep
    names = [f.name for f in result]
    assert "Focus" in names
    assert "Relax" in names
    assert "Sleep" in names


@pytest.mark.asyncio
async def test_browse_empty_path_returns_categories(provider):
    result = await provider.browse("")
    assert len(result) == 3


@pytest.mark.asyncio
async def test_browse_focus_category(provider):
    # Set up mock activities
    provider._activities = {
        "focus": [
            {"id": "act_1", "displayValue": "Deep Work"},
            {"id": "act_2", "displayValue": "Creativity"},
            {"id": "act_3", "displayValue": "Motivation"},
        ]
    }
    result = await provider.browse("brainfm_radio://brainfm://Focus")
    assert len(result) == 3
    names = [r.name for r in result]
    assert "Deep Work" in names
    assert "Creativity" in names


@pytest.mark.asyncio
async def test_browse_unknown_category(provider):
    result = await provider.browse("brainfm://Unknown")
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_stream_details(provider):
    mock_client = AsyncMock(spec=BrainfmClient)
    mock_client.create_session = AsyncMock(return_value={
        "tokenedUrl": "https://audio2.brain.fm/track.mp3?token=stream-token-123",
        "lengthInSeconds": 1200,
    })
    provider._client = mock_client
    provider._session_token = "session-token"
    provider._user_id = "user123"

    from music_assistant_models.enums import MediaType
    result = await provider.get_stream_details("act_1", MediaType.RADIO)

    assert result.stream_type.value == "HTTP"
    assert "stream-token-123" in result.path
    mock_client.create_session.assert_called_once_with("session-token", "user123", "act_1")


@pytest.mark.asyncio
async def test_get_stream_details_no_client(provider):
    from music_assistant_models.enums import MediaType
    with pytest.raises(BrainfmError):
        await provider.get_stream_details("act_1", MediaType.RADIO)


@pytest.mark.asyncio
async def test_get_stream_details_no_url(provider):
    """Session returns no tokenedUrl — should raise."""
    mock_client = AsyncMock(spec=BrainfmClient)
    mock_client.create_session = AsyncMock(return_value={"lengthInSeconds": 600})
    provider._client = mock_client
    provider._session_token = "session-token"
    provider._user_id = "user123"

    from music_assistant_models.enums import MediaType
    with pytest.raises(BrainfmError, match="No stream URL"):
        await provider.get_stream_details("act_1", MediaType.RADIO)

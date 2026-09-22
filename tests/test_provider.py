"""Tests for BrainfmRadioProvider."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from brainfm_radio.brainfm_client import BrainfmClient


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


def test_supported_features():
    from brainfm_radio import BrainfmRadioProvider, SUPPORTED_FEATURES
    from music_assistant_models.enums import ProviderFeature
    assert ProviderFeature.BROWSE in SUPPORTED_FEATURES


def test_is_streaming_provider():
    from brainfm_radio import BrainfmRadioProvider
    assert BrainfmRadioProvider.is_streaming_provider.fget is not None

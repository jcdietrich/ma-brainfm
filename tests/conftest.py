"""Test configuration with mocks for music_assistant_models."""
import sys
from enum import Enum
from types import ModuleType
from dataclasses import dataclass, field
from typing import Any


class ConfigEntryType(Enum):
    STRING = "string"
    SECURE_STRING = "secure_string"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    ACTION = "action"


@dataclass
class ConfigEntry:
    key: str
    type: ConfigEntryType
    label: str = ""
    required: bool = False
    default_value: Any = None
    description: str = ""
    range: tuple[int, int] | None = None
    hidden: bool = False


def _create_mock_module(name: str) -> ModuleType:
    """Create a mock module with the needed submodules."""
    mod = ModuleType(name)
    return mod


# Create mock modules for music_assistant_models
if "music_assistant_models" not in sys.modules:
    ma_models = _create_mock_module("music_assistant_models")
    sys.modules["music_assistant_models"] = ma_models

    config_entries = _create_mock_module("music_assistant_models.config_entries")
    config_entries.ConfigEntry = ConfigEntry
    config_entries.ConfigEntryType = ConfigEntryType
    sys.modules["music_assistant_models.config_entries"] = config_entries

    enums = _create_mock_module("music_assistant_models.enums")
    enums.ConfigEntryType = ConfigEntryType
    enums.ContentType = Enum("ContentType", {"MPEG": "MPEG"})
    enums.MediaType = Enum("MediaType", {"RADIO": "RADIO"})
    enums.ProviderFeature = Enum("ProviderFeature", {"BROWSE": "BROWSE"})
    enums.StreamType = Enum("StreamType", {"HTTP": "HTTP"})
    sys.modules["music_assistant_models.enums"] = enums

    media_items = _create_mock_module("music_assistant_models.media_items")

    def _make_dataclass_like(cls_name):
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        return type(cls_name, (), {"__init__": __init__})

    media_items.BrowseFolder = _make_dataclass_like("BrowseFolder")
    media_items.ItemMapping = _make_dataclass_like("ItemMapping")
    media_items.MediaItemType = Enum("MediaItemType", {"RADIO": "RADIO"})
    media_items.Radio = _make_dataclass_like("Radio")
    media_items.ProviderMapping = _make_dataclass_like("ProviderMapping")
    media_items.AudioFormat = _make_dataclass_like("AudioFormat")
    sys.modules["music_assistant_models.media_items"] = media_items

    streamdetails = _create_mock_module("music_assistant_models.streamdetails")
    streamdetails.StreamDetails = _make_dataclass_like("StreamDetails")
    sys.modules["music_assistant_models.streamdetails"] = streamdetails

# Create mock module for music_assistant (server)
if "music_assistant" not in sys.modules:
    ma_server = _create_mock_module("music_assistant")
    sys.modules["music_assistant"] = ma_server

if "music_assistant.models" not in sys.modules:
    ma_models_pkg = _create_mock_module("music_assistant.models")
    sys.modules["music_assistant.models"] = ma_models_pkg

if "music_assistant.models.setup_flow" not in sys.modules:
    setup_flow_mod = _create_mock_module("music_assistant.models.setup_flow")

    class MockSetupSession:
        """Mock SetupSession for testing."""

        def __init__(self):
            self._result = None

        async def form(
            self,
            entries: list,
            step_id: str = "",
            errors: dict | None = None,
            last_step: bool = False,
        ) -> dict:
            """Return mock form values."""
            return {"email": "test@example.com", "password": "testpass123"}

        async def finish(self, data: dict) -> None:
            """Store the result data."""
            self._result = data

    setup_flow_mod.SetupSession = MockSetupSession
    sys.modules["music_assistant.models.setup_flow"] = setup_flow_mod

if "music_assistant.models.music_provider" not in sys.modules:
    music_provider_mod = _create_mock_module("music_assistant.models.music_provider")

    class MockMusicProvider:
        def __init__(self, mass, manifest, config, supported_features):
            self.mass = mass
            self.manifest = manifest
            self.config = config
            self._supported_features = supported_features

        def get_config_value(self, key, default=None):
            return self.config.get_value(key, default)

        @property
        def is_streaming_provider(self):
            return True

        instance_id = "test_instance"
        domain = "brainfm_radio"

    music_provider_mod.MusicProvider = MockMusicProvider
    sys.modules["music_assistant.models.music_provider"] = music_provider_mod
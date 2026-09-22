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
    media_items.BrowseFolder = type("BrowseFolder", (), {"__init__": lambda self, **kwargs: None})
    media_items.ItemMapping = type("ItemMapping", (), {"__init__": lambda self, **kwargs: None})
    media_items.MediaItemType = Enum("MediaItemType", {"RADIO": "RADIO"})
    media_items.Radio = type("Radio", (), {"__init__": lambda self, **kwargs: None})
    media_items.ProviderMapping = type("ProviderMapping", (), {"__init__": lambda self, **kwargs: None})
    media_items.AudioFormat = type("AudioFormat", (), {"__init__": lambda self, **kwargs: None})
    sys.modules["music_assistant_models.media_items"] = media_items

    streamdetails = _create_mock_module("music_assistant_models.streamdetails")
    streamdetails.StreamDetails = type("StreamDetails", (), {"__init__": lambda self, **kwargs: None})
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
    music_provider_mod.MusicProvider = type("MusicProvider", (), {
        "get_config_value": lambda self, key, default=None: None,
        "is_streaming_provider": property(lambda self: True),
        "instance_id": "test_instance",
        "domain": "brainfm_radio",
    })
    sys.modules["music_assistant.models.music_provider"] = music_provider_mod

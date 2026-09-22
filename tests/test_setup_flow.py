"""Tests for setup flow."""
import pytest
from unittest.mock import AsyncMock, patch
from music_assistant_models.config_entries import ConfigEntry
from music_assistant_models.enums import ConfigEntryType


def test_setup_entries_have_required_keys():
    from brainfm_radio.setup_flow import ENTRIES

    keys = [e.key for e in ENTRIES]
    assert "email" in keys
    assert "password" in keys

    password_entry = next(e for e in ENTRIES if e.key == "password")
    assert password_entry.type == ConfigEntryType.SECURE_STRING

    email_entry = next(e for e in ENTRIES if e.key == "email")
    assert email_entry.type == ConfigEntryType.STRING

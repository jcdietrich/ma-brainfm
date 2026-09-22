"""Hardcoded Brain.fm station list — used as fallback when API is unreachable."""

from __future__ import annotations

STATIONS: list[dict[str, str | int]] = [
    # Focus
    {"id": 35, "name": "Focus", "category": "Focus"},
    {"id": 541, "name": "LoFi Focus", "category": "Focus"},
    {"id": 302, "name": "Piano Focus", "category": "Focus"},
    {"id": 55, "name": "Electronic Music Focus", "category": "Focus"},
    {"id": 300, "name": "Cinematic Music Focus", "category": "Focus"},
    {"id": 53, "name": "Beach Focus", "category": "Focus"},
    {"id": 57, "name": "Nightsounds Focus", "category": "Focus"},
    {"id": 34, "name": "Relaxed Focus", "category": "Focus"},
    {"id": 540, "name": "Study Focus", "category": "Focus"},
    # Relax
    {"id": 285, "name": "Quick Relax", "category": "Relax"},
    {"id": 299, "name": "Unguided Meditation", "category": "Relax"},
    {"id": 100, "name": "Guided Meditation", "category": "Relax"},
    # Sleep
    {"id": 42, "name": "Nighttime Sleep", "category": "Sleep"},
    {"id": 36, "name": "Sleep", "category": "Sleep"},
]

CATEGORIES = ["Focus", "Relax", "Sleep"]

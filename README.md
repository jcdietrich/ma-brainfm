# Music Assistant Brain.fm Radio Provider

Play focus, relaxation, and sleep music from Brain.fm through Music Assistant.

## Installation

```bash
pip install music-assistant-provider-brainfm
```

Requires [music-assistant-plugin-manager](https://pypi.org/project/music-assistant-plugin-manager/) to be installed and running.

## Setup

1. In Music Assistant, go to **Settings → Music Providers → Add Provider**
2. Select **Brain.fm Radio**
3. Enter your Brain.fm email and password
4. Browse stations under **Brain.fm Radio** in the browse view

## Available Stations

**Focus:** Focus, LoFi Focus, Piano Focus, Electronic Music Focus, Cinematic Music Focus, Beach Focus, Nightsounds Focus, Relaxed Focus, Study Focus

**Relax:** Quick Relax, Unguided Meditation, Guided Meditation

**Sleep:** Nighttime Sleep, Sleep

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Run tests with coverage
pytest --cov=brainfm_radio -v
```

## Limitations

- Uses Brain.fm's unofficial API — may break if endpoints change
- Station list fetched live from API; hardcoded fallback for reliability
- No search or library sync (Brain.fm streams are continuous, not track-based)

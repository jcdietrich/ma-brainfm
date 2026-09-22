# Music Assistant Brain.fm Radio Provider

Play focus, relaxation, and sleep music from Brain.fm through Music Assistant.

## Installation

### Home Assistant OS (recommended)

One-line install from SSH with Docker access:

```bash
curl -fsSL https://raw.githubusercontent.com/jcd/ma-brainfm/main/scripts/install_provider.sh | sh
```

This copies the provider into the Music Assistant container and restarts it.

**To survive HA/MA updates**, run the deploy script after each update:

```bash
bash /path/to/ma-brainfm/scripts/deploy_to_ha.sh
```

Or one-liner from the repo root:

```bash
git clone https://github.com/jcdietrich/ma-brainfm.git && cd ma-brainfm && bash scripts/deploy_to_ha.sh
```

The provider files are also stored persistently at:
`/config/custom_components/mass/providers/brainfm_radio/`

### Standalone (pip)

```bash
pip install music-assistant-provider-brainfm
```

Requires [music-assistant-plugin-manager](https://pypi.org/project/music-assistant-plugin-manager/).

## Setup

1. In Music Assistant, go to **Settings → Music Providers → Add Provider**
2. Select **Brain.fm Radio**
3. Enter your Brain.fm email and password
4. Browse stations under **Brain.fm Radio** in the browse view

## Available Stations

| Category | Stations |
|----------|----------|
| **Focus** | Focus, LoFi Focus, Piano Focus, Electronic Music Focus, Cinematic Music Focus, Beach Focus, Nightsounds Focus, Relaxed Focus, Study Focus |
| **Relax** | Quick Relax, Unguided Meditation, Guided Meditation |
| **Sleep** | Nighttime Sleep, Sleep |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v
```

## Limitations

- Uses Brain.fm's unofficial API — may break if endpoints change
- Station list fetched live from API; hardcoded fallback for reliability
- No search or library sync (Brain.fm streams are continuous, not track-based)

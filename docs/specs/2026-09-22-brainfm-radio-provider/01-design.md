# Brain.fm Radio Provider for Music Assistant

## Overview

A Music Assistant Music Provider that exposes Brain.fm's focus, relaxation, and sleep music stations as browsable Radio items. Users authenticate with their Brain.fm account, browse available stations grouped by category, and stream them through any Music Assistant player.

## Goals

- Expose all Brain.fm stations as Radio items in Music Assistant
- Simple email/password authentication via MA's setup flow
- Direct HTTP streaming — MA handles playback natively via ffmpeg
- Distributed as a standalone pip package (no PR to MA core required)

## Non-Goals

- Track-level browsing or search (Brain.fm streams are continuous, not track-based)
- Library sync (no favorites/history to sync)
- Recommendations or personalized content
- Multiple Brain.fm account support per instance

## Architecture

```
music-assistant-provider-brainfm/
├── pyproject.toml
├── README.md
├── brainfm_radio/
│   ├── __init__.py           # MusicProvider subclass + setup()
│   ├── setup_flow.py         # Credential collection flow
│   ├── brainfm_client.py     # Async Brain.fm API client
│   ├── manifest.json         # MA provider manifest
│   ├── strings.json          # UI translations
│   ├── constants.py          # Station IDs, categories, metadata
│   └── icon.svg              # Provider icon (optional)
```

## Components

### 1. `brainfm_client.py` — Brain.fm API Client

Async wrapper around Brain.fm's unofficial HTTP API.

**API Flow:**
1. `POST https://api.brain.fm/api/v1/login` with email/password → session token
2. `GET https://api.brain.fm/api/v1/stations` → list of available stations
3. `POST https://api.brain.fm/api/v1/get-token` with station ID → stream token
4. Stream URL: `https://stream.brain.fm/?tkn=<stream_token>`

> **Note:** These endpoints are reverse-engineered from Brain.fm's web client and may
> change without notice. Exact URLs and payload formats will be verified during
> implementation by inspecting network traffic from the Brain.fm web app.

**Class: `BrainfmClient`**
```python
class BrainfmClient:
    def __init__(self, session: aiohttp.ClientSession) -> None: ...

    async def login(self, email: str, password: str) -> str:
        """Authenticate and return session token."""

    async def get_stations(self, session_token: str) -> list[dict]:
        """Fetch available stations."""

    async def get_stream_token(self, session_token: str, station_id: int) -> str:
        """Get a short-lived stream token for a station."""

    def make_stream_url(self, stream_token: str) -> str:
        """Build the HTTP stream URL from a token."""
```

**Error handling:**
- `LoginFailed` — raised on 401/403 from login endpoint
- `TokenError` — raised when stream token request fails
- `APIError` — generic wrapper for unexpected responses

**Notes:**
- The unofficial API endpoints are reverse-engineered from Brain.fm's web client
- Session tokens may expire; re-login is attempted once before failing
- Stream tokens are short-lived (minutes) and fetched fresh per playback

### 2. `setup_flow.py` — Credential Collection

Uses MA's `SetupSession` API to collect Brain.fm credentials.

**Flow:**
1. Show form with email (string) and password (secure_string) fields
2. Validate credentials by attempting login via `BrainfmClient`
3. On success: persist email and session token to `setup_data`
4. On failure: show error, allow retry

**Config entries collected:**
| Key | Type | Description |
|-----|------|-------------|
| `email` | STRING | Brain.fm account email |
| `password` | SECURE_STRING | Brain.fm account password |

**Translations (`strings.json`):**
```json
{
  "setup_flow": {
    "credentials": {
      "title": "Connect your Brain.fm account",
      "description": "Enter your Brain.fm email and password."
    }
  },
  "errors": {
    "invalid_credentials": "Invalid Brain.fm email or password."
  }
}
```

### 3. `__init__.py` — Music Provider

**Class: `BrainfmRadioProvider(MusicProvider)`**

**Supported features:**
```python
SUPPORTED_FEATURES = {
    ProviderFeature.BROWSE,
}
```

**Key methods:**

#### `setup()` (module-level)
```python
async def setup(mass, manifest, config) -> ProviderInstanceType:
    return BrainfmRadioProvider(mass, manifest, config, SUPPORTED_FEATURES)
```

#### `loaded_in_mass()`
- Validate stored session token by attempting a lightweight API call
- If token expired, re-login using stored credentials
- Cache the valid session token for the session lifetime

#### `browse(path: str)`
Returns Radio items organized by category.

**Station list strategy:** Fetch stations live from the Brain.fm API via `client.get_stations()`. If the API is unreachable, fall back to a hardcoded list in `constants.py` (based on known stations from the unofficial client). The hardcoded list serves as a safety net — the live API is always preferred.

```
brainfm://
├── Focus/
│   ├── Focus
│   ├── Lo-Fi Focus
│   ├── Piano Focus
│   ├── Electronic Music Focus
│   ├── Cinematic Music Focus
│   ├── Beach Focus
│   ├── Nightsounds Focus
│   ├── Relaxed Focus
│   └── Study Focus
├── Relax/
│   ├── Quick Relax
│   └── Unguided Meditation
└── Sleep/
    ├── Nighttime Sleep
    └── Guided Meditation
```

Each station becomes a `Radio` item with:
- `item_id`: Brain.fm station ID (e.g., `35`)
- `name`: Station name (e.g., "Focus")
- `image`: Category-based icon or Brain.fm station artwork (if available)
- `provider_mappings`: Provider-specific metadata

#### `get_stream_details(item_id: str, media_type: MediaType)`
1. Fetch a fresh stream token: `client.get_stream_token(session_token, int(item_id))`
2. Build stream URL: `client.make_stream_url(token)`
3. Return `StreamDetails`:
```python
StreamDetails(
    provider=self.instance_id,
    item_id=item_id,
    audio_format=AudioFormat(
        content_type=ContentType.MPEG,  # Brain.fm streams MP3
    ),
    media_type=MediaType.RADIO,
    stream_type=StreamType.HTTP,
    path=stream_url,
    allow_seek=False,   # Live-style stream
    can_seek=False,
)
```

#### `resolve_image(path: str)`
- For station images, proxy through Brain.fm's CDN if available
- Fallback to category-based default images

### 4. `manifest.json` — Provider Metadata

```json
{
  "type": "music",
  "domain": "brainfm_radio",
  "name": "Brain.fm Radio",
  "description": "Play focus, relaxation, and sleep music from Brain.fm",
  "codeowners": ["@jcd"],
  "requirements": ["aiohttp>=3.9"],
  "documentation": "https://github.com/jcd/ma-brainfm",
  "multi_instances": false
}
```

### 5. `pyproject.toml` — Package Configuration

```toml
[project]
name = "music-assistant-provider-brainfm"
version = "0.1.0"
description = "Brain.fm Radio provider for Music Assistant"
requires-python = ">=3.12"
dependencies = [
    "music-assistant>=2.4",
    "aiohttp>=3.9",
]

[project.entry-points."music_assistant.provider"]
brainfm_radio = "brainfm_radio"
```

## Data Flow

```
User selects Brain.fm station in MA UI
    ↓
MA calls get_stream_details(station_id)
    ↓
Provider fetches fresh stream token from Brain.fm API
    ↓
Provider returns StreamDetails with HTTP stream URL
    ↓
MA's audio controller opens HTTP stream via ffmpeg
    ↓
Audio plays on the target player
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| Invalid credentials at setup | Show error in setup flow, allow retry |
| Session token expired at play | Re-login silently using stored credentials |
| Stream token expired | Fetch fresh token (tokens are short-lived) |
| Brain.fm API unreachable | Surface error to MA, player shows unavailable |
| Invalid station ID | Log warning, return error to MA |

## Testing Strategy

- **Unit tests**: Mock `aiohttp` responses for API client
- **Integration test**: Manual testing with real Brain.fm account
- **MA compatibility**: Test with MA's provider test harness if available

## Installation

```bash
pip install music-assistant-provider-brainfm
```

Then in MA: Settings → Music Providers → Add Provider → Brain.fm Radio → Enter credentials.

## Limitations

- Brain.fm has no official API — endpoints may change without notice
- Stream tokens are short-lived; each playback requires a fresh token fetch
- Station list fetched live from API, with hardcoded fallback for reliability
- No search capability (Brain.fm doesn't support track queries)
- No library sync or favorites persistence

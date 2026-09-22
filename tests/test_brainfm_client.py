"""Tests for BrainfmClient."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from aiohttp import ClientResponse

from brainfm_radio.brainfm_client import BrainfmClient, LoginFailed, TokenError, APIError


def _make_response(status: int, payload: dict | None = None, text: str | None = None) -> MagicMock:
    """Create a mock aiohttp ClientResponse."""
    resp = MagicMock(spec=ClientResponse)
    resp.status = status
    body = json.dumps(payload or {})
    resp.text = AsyncMock(return_value=text if text is not None else body)
    resp.json = AsyncMock(return_value=payload or {})

    # Support `async with` context manager
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=resp)
    cm.__aexit__ = AsyncMock(return_value=False)
    resp.__aenter__ = cm.__aenter__
    resp.__aexit__ = cm.__aexit__
    return resp


@pytest_asyncio.fixture
async def client():
    import aiohttp
    session = aiohttp.ClientSession()
    yield BrainfmClient(session)
    await session.close()


@pytest.mark.asyncio
async def test_login_success(client):
    mock_resp = _make_response(200, {"token": "test-session-token"})
    with patch.object(client._session, "post", return_value=mock_resp):
        token = await client.login("user@example.com", "password123")
        assert token == "test-session-token"


@pytest.mark.asyncio
async def test_login_failure(client):
    mock_resp = _make_response(401, {"error": "Invalid credentials"})
    with patch.object(client._session, "post", return_value=mock_resp):
        with pytest.raises(LoginFailed):
            await client.login("user@example.com", "wrong")


@pytest.mark.asyncio
async def test_login_api_error(client):
    mock_resp = _make_response(500, {"error": "Internal server error"})
    with patch.object(client._session, "post", return_value=mock_resp):
        with pytest.raises(APIError, match="Login failed with status 500"):
            await client.login("user@example.com", "password123")


@pytest.mark.asyncio
async def test_get_stations(client):
    mock_resp = _make_response(200, {
        "stations": [
            {"id": 35, "name": "Focus", "category": "Focus"},
            {"id": 42, "name": "Nighttime Sleep", "category": "Sleep"},
        ]
    })
    with patch.object(client._session, "get", return_value=mock_resp):
        stations = await client.get_stations("test-token")
        assert len(stations) == 2
        assert stations[0]["name"] == "Focus"


@pytest.mark.asyncio
async def test_get_stream_token(client):
    mock_resp = _make_response(200, {"token": "stream-token-abc"})
    with patch.object(client._session, "post", return_value=mock_resp):
        token = await client.get_stream_token("test-token", 35)
        assert token == "stream-token-abc"


@pytest.mark.asyncio
async def test_get_stream_token_error(client):
    mock_resp = _make_response(502, {"error": "Bad gateway"})
    with patch.object(client._session, "post", return_value=mock_resp):
        with pytest.raises(TokenError, match="Token request failed with status 502"):
            await client.get_stream_token("test-token", 35)


def test_make_stream_url(client):
    url = client.make_stream_url("stream-token-abc")
    assert url == "https://stream.brain.fm/?tkn=stream-token-abc"



@pytest.mark.asyncio
async def test_login_429_retry_then_success(client):
    mock_429 = _make_response(429, {"error": "rate limited"})
    mock_200 = _make_response(200, {"token": "recovered-token"})
    with patch.object(client._session, "post", side_effect=[mock_429, mock_429, mock_200]):
        with patch("brainfm_radio.brainfm_client.asyncio.sleep", new_callable=AsyncMock):
            token = await client.login("user@example.com", "password123")
            assert token == "recovered-token"


@pytest.mark.asyncio
async def test_login_429_exhausted(client):
    mock_429 = _make_response(429, {"error": "rate limited"})
    with patch.object(client._session, "post", return_value=mock_429):
        with patch("brainfm_radio.brainfm_client.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(APIError, match="Rate limited"):
                await client.login("user@example.com", "password123")


@pytest.mark.asyncio
async def test_login_with_cookie(client):
    mock_resp = _make_response(200, {"token": "cookie-token"})
    with patch.object(client._session, "post", return_value=mock_resp) as mock_post:
        token = await client.login("user@example.com", "pass", cf_bm="test-cf-bm-value")
        assert token == "cookie-token"
        # Verify Cookie header was set
        _, kwargs = mock_post.call_args
        assert "__cf_bm=test-cf-bm-value" in kwargs["headers"]["Cookie"]
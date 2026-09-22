"""Tests for BrainfmClient (v3 API)."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from aiohttp import ClientResponse

from brainfm_radio.brainfm_client import (
    BrainfmClient,
    LoginFailed,
    TokenError,
    APIError,
    _decode_jwt_payload,
)


def _make_response(status: int, payload: dict | None = None, text: str | None = None) -> MagicMock:
    """Create a mock aiohttp ClientResponse."""
    resp = MagicMock(spec=ClientResponse)
    resp.status = status
    body = json.dumps(payload or {})
    resp.text = AsyncMock(return_value=text if text is not None else body)
    resp.json = AsyncMock(return_value=payload or {})

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=resp)
    cm.__aexit__ = AsyncMock(return_value=False)
    resp.__aenter__ = cm.__aenter__
    resp.__aexit__ = cm.__aexit__
    return resp


# --- JWT helpers ---

def _make_jwt(payload: dict) -> str:
    """Create a minimal JWT with the given payload."""
    import base64
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256"}).encode()).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    sig = "signature"
    return f"{header}.{body}.{sig}"


def test_decode_jwt_payload():
    payload = {"_id": "user123", "email": "test@example.com"}
    token = _make_jwt(payload)
    result = _decode_jwt_payload(token)
    assert result["_id"] == "user123"
    assert result["email"] == "test@example.com"


# --- Fixtures ---

@pytest_asyncio.fixture
async def client():
    import aiohttp
    session = aiohttp.ClientSession()
    yield BrainfmClient(session)
    await session.close()


# --- Login tests ---

@pytest.mark.asyncio
async def test_login_success(client):
    mock_resp = _make_response(200, {"token": "test-session-token"})
    with patch.object(client._session, "post", return_value=mock_resp):
        token = await client.login("user@example.com", "password123")
        assert token == "test-session-token"


@pytest.mark.asyncio
async def test_login_success_result_field(client):
    """Login response may use 'result' instead of 'token'."""
    mock_resp = _make_response(200, {"result": "jwt-from-result"})
    with patch.object(client._session, "post", return_value=mock_resp):
        token = await client.login("user@example.com", "password123")
        assert token == "jwt-from-result"


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
        _, kwargs = mock_post.call_args
        assert "__cf_bm=test-cf-bm-value" in kwargs["headers"]["Cookie"]


# --- User ID tests ---

def test_get_user_id():
    token = _make_jwt({"_id": "user_abc123"})
    session = MagicMock()
    client = BrainfmClient(session)
    assert client.get_user_id(token) == "user_abc123"


def test_get_user_id_sub_field():
    token = _make_jwt({"sub": "sub_field_id"})
    session = MagicMock()
    client = BrainfmClient(session)
    assert client.get_user_id(token) == "sub_field_id"


def test_get_user_id_missing():
    token = _make_jwt({"email": "test@example.com"})
    session = MagicMock()
    client = BrainfmClient(session)
    with pytest.raises(APIError, match="Could not extract user ID"):
        client.get_user_id(token)


# --- Activities tests ---

@pytest.mark.asyncio
async def test_get_activities(client):
    mock_resp = _make_response(200, {
        "activities": [
            {"id": "act_1", "displayValue": "Deep Work", "description": "Deep focus"},
            {"id": "act_2", "displayValue": "Creativity", "description": "Creative flow"},
        ]
    })
    with patch.object(client._session, "get", return_value=mock_resp):
        activities = await client.get_activities("test-token", "focus")
        assert len(activities) == 2
        assert activities[0]["displayValue"] == "Deep Work"


@pytest.mark.asyncio
async def test_get_activities_error(client):
    mock_resp = _make_response(404, {"error": "Not found"})
    with patch.object(client._session, "get", return_value=mock_resp):
        with pytest.raises(APIError, match="Activities request failed"):
            await client.get_activities("test-token", "unknown_mode")


# --- Session creation tests ---

@pytest.mark.asyncio
async def test_create_session(client):
    mock_resp = _make_response(200, {
        "result": {
            "trackVariation": {
                "tokenedUrl": "https://audio2.brain.fm/track.mp3?token=abc",
                "cdnUrl": "https://cdn.brain.fm/track.mp3",
                "lengthInSeconds": 1200,
            }
        }
    })
    with patch.object(client._session, "post", return_value=mock_resp):
        result = await client.create_session("token", "user123", "act_1")
        assert result["tokenedUrl"] == "https://audio2.brain.fm/track.mp3?token=abc"
        assert result["lengthInSeconds"] == 1200


@pytest.mark.asyncio
async def test_create_session_with_genres(client):
    mock_resp = _make_response(200, {
        "result": {
            "trackVariation": {
                "tokenedUrl": "https://audio2.brain.fm/track.mp3",
            }
        }
    })
    with patch.object(client._session, "post", return_value=mock_resp) as mock_post:
        await client.create_session("token", "user123", "act_1", genre_names=["classical"])
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["genreNames"] == ["classical"]


@pytest.mark.asyncio
async def test_create_session_error(client):
    mock_resp = _make_response(500, {"error": "Internal error"})
    with patch.object(client._session, "post", return_value=mock_resp):
        with pytest.raises(APIError, match="Session creation failed"):
            await client.create_session("token", "user123", "act_1")

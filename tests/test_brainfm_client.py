"""Tests for BrainfmClient."""
import pytest
import pytest_asyncio
from aioresponses import aioresponses
from brainfm_radio.brainfm_client import BrainfmClient, LoginFailed, APIError


@pytest_asyncio.fixture
async def client():
    import aiohttp
    session = aiohttp.ClientSession()
    yield BrainfmClient(session)
    await session.close()


@pytest.mark.asyncio
async def test_login_success(client):
    with aioresponses() as m:
        m.post(
            "https://api.brain.fm/api/v1/login",
            payload={"token": "test-session-token"},
            status=200,
        )
        token = await client.login("user@example.com", "password123")
        assert token == "test-session-token"


@pytest.mark.asyncio
async def test_login_failure(client):
    with aioresponses() as m:
        m.post(
            "https://api.brain.fm/api/v1/login",
            payload={"error": "Invalid credentials"},
            status=401,
        )
        with pytest.raises(LoginFailed):
            await client.login("user@example.com", "wrong")


@pytest.mark.asyncio
async def test_get_stations(client):
    with aioresponses() as m:
        m.get(
            "https://api.brain.fm/api/v1/stations",
            payload={
                "stations": [
                    {"id": 35, "name": "Focus", "category": "Focus"},
                    {"id": 42, "name": "Nighttime Sleep", "category": "Sleep"},
                ]
            },
            status=200,
        )
        stations = await client.get_stations("test-token")
        assert len(stations) == 2
        assert stations[0]["name"] == "Focus"


@pytest.mark.asyncio
async def test_get_stream_token(client):
    with aioresponses() as m:
        m.post(
            "https://api.brain.fm/api/v1/get-token",
            payload={"token": "stream-token-abc"},
            status=200,
        )
        token = await client.get_stream_token("test-token", 35)
        assert token == "stream-token-abc"


def test_make_stream_url(client):
    url = client.make_stream_url("stream-token-abc")
    assert url == "https://stream.brain.fm/?tkn=stream-token-abc"

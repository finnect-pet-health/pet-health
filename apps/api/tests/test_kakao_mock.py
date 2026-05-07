"""Tests for MockKakaoOAuthClient."""
from __future__ import annotations

import pytest

from app.integrations.kakao import KakaoExchangeError, KakaoUser
from app.integrations.kakao.mock import MockKakaoOAuthClient


@pytest.fixture
def client() -> MockKakaoOAuthClient:
    return MockKakaoOAuthClient()


@pytest.mark.asyncio
async def test_mock_exchange_returns_deterministic_user(client):
    user = await client.exchange_code("mock-user-1", "http://localhost/callback")
    assert isinstance(user, KakaoUser)
    assert user.kakao_id == "mock_1"
    assert user.name == "테스트유저1"
    assert user.email == "mock1@example.test"
    assert user.profile_image is None


@pytest.mark.asyncio
async def test_mock_exchange_is_deterministic(client):
    """Same code must produce identical KakaoUser every time."""
    user_a = await client.exchange_code("mock-user-42", "http://any")
    user_b = await client.exchange_code("mock-user-42", "http://any")
    assert user_a == user_b


@pytest.mark.asyncio
async def test_mock_exchange_different_n(client):
    user1 = await client.exchange_code("mock-user-1", "http://any")
    user2 = await client.exchange_code("mock-user-2", "http://any")
    assert user1.kakao_id != user2.kakao_id
    assert user1.email != user2.email


@pytest.mark.asyncio
async def test_mock_exchange_invalid_code_raises(client):
    with pytest.raises(KakaoExchangeError, match="invalid_code"):
        await client.exchange_code("bad-code", "http://any")


@pytest.mark.asyncio
async def test_mock_exchange_empty_code_raises(client):
    with pytest.raises(KakaoExchangeError, match="invalid_code"):
        await client.exchange_code("", "http://any")


@pytest.mark.asyncio
async def test_mock_exchange_wrong_prefix_raises(client):
    with pytest.raises(KakaoExchangeError):
        await client.exchange_code("user-mock-1", "http://any")


@pytest.mark.asyncio
async def test_mock_exchange_non_numeric_suffix_raises(client):
    with pytest.raises(KakaoExchangeError):
        await client.exchange_code("mock-user-abc", "http://any")

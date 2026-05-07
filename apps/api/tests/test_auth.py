"""Tests for auth service + /v1/auth router (AC2/3/4) + upsert idempotency."""
from __future__ import annotations

import pytest

from app.integrations.kakao import KakaoUser
from app.services.auth import upsert_kakao_user

# ---------------------------------------------------------------------------
# Service: upsert_kakao_user idempotency
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_kakao_user_idempotent(db_session):
    payload = KakaoUser(
        kakao_id="mock_42",
        name="테스트유저42",
        email="mock42@example.test",
        profile_image=None,
    )
    user1 = await upsert_kakao_user(db_session, payload)
    user2 = await upsert_kakao_user(db_session, payload)
    assert user1.id == user2.id
    assert user2.name == "테스트유저42"


@pytest.mark.asyncio
async def test_upsert_kakao_user_updates_profile(db_session):
    initial = KakaoUser(kakao_id="mock_7", name="이름A", email=None, profile_image=None)
    updated = KakaoUser(
        kakao_id="mock_7", name="이름B", email="b@x", profile_image="http://img"
    )
    u1 = await upsert_kakao_user(db_session, initial)
    u2 = await upsert_kakao_user(db_session, updated)
    assert u1.id == u2.id
    assert u2.name == "이름B"
    assert u2.email == "b@x"
    assert u2.profile_image == "http://img"


# ---------------------------------------------------------------------------
# Router: AC2/3/4
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_kakao_login_happy_path(app_client):
    """AC2: mock-user-1 로그인 → access/refresh + user 반환."""
    res = await app_client.post(
        "/v1/auth/kakao",
        json={"auth_code": "mock-user-1", "redirect_uri": "http://localhost"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert "access" in body
    assert "refresh" in body
    assert body["user"]["name"] == "테스트유저1"
    assert body["user"]["profile_image"] is None
    assert "id" in body["user"]


@pytest.mark.asyncio
async def test_kakao_login_invalid_code(app_client):
    res = await app_client.post(
        "/v1/auth/kakao",
        json={"auth_code": "bad-code", "redirect_uri": "http://localhost"},
    )
    assert res.status_code == 400
    body = res.json()
    assert body["detail"]["error"]["code"] == "INVALID_CODE"


@pytest.mark.asyncio
async def test_refresh_rotates_tokens(app_client):
    """AC3: refresh → new access + new refresh, 이전 refresh는 무효."""
    login = await app_client.post(
        "/v1/auth/kakao",
        json={"auth_code": "mock-user-1", "redirect_uri": "http://localhost"},
    )
    refresh = login.json()["refresh"]

    res = await app_client.post("/v1/auth/refresh", json={"refresh": refresh})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["access"]
    assert body["refresh"] != refresh

    # Old refresh is now invalid
    res2 = await app_client.post("/v1/auth/refresh", json={"refresh": refresh})
    assert res2.status_code == 401


@pytest.mark.asyncio
async def test_refresh_unknown_token_401(app_client):
    res = await app_client.post("/v1/auth/refresh", json={"refresh": "ghost"})
    assert res.status_code == 401
    assert res.json()["detail"]["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_logout_idempotent_204(app_client):
    """AC4: logout은 정상/중복 호출 모두 204."""
    login = await app_client.post(
        "/v1/auth/kakao",
        json={"auth_code": "mock-user-2", "redirect_uri": "http://localhost"},
    )
    refresh = login.json()["refresh"]

    res = await app_client.post("/v1/auth/logout", json={"refresh": refresh})
    assert res.status_code == 204

    # Second call must still be 204 (idempotent)
    res2 = await app_client.post("/v1/auth/logout", json={"refresh": refresh})
    assert res2.status_code == 204


# ---------------------------------------------------------------------------
# AC5: /v1/me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_me_returns_user_and_empty_families(app_client):
    login = await app_client.post(
        "/v1/auth/kakao",
        json={"auth_code": "mock-user-3", "redirect_uri": "http://localhost"},
    )
    access = login.json()["access"]
    res = await app_client.get(
        "/v1/me", headers={"Authorization": f"Bearer {access}"}
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["name"] == "테스트유저3"
    assert body["profile_image"] is None
    assert body["families"] == []


@pytest.mark.asyncio
async def test_me_requires_bearer(app_client):
    res = await app_client.get("/v1/me")
    assert res.status_code == 401

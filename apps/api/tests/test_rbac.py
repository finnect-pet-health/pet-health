"""RBAC edge cases for ``require_family`` + ``current_user`` dependencies.

Covers gaps not exercised by ``test_families.py`` / ``test_pets.py``:

- ``require_family`` returns 404 (not 403) when the path family is unknown
  or the caller has no membership at all — we do not leak existence.
- ``require_family`` returns 403 when the caller is a member but lacks the
  ``owner`` role required by the endpoint.
- ``require_family`` returns 200 on the owner happy path.
- ``current_user`` rejects requests with no/garbage/orphaned tokens (401).
- Invalid (non-UUID) ``family_id`` path components return 404 — same policy
  applied for ``/v1/pets/{pet_id}`` in test_pets.
"""
from __future__ import annotations

import uuid

import pytest

from app.models import User


async def _login(app_client, code: str) -> dict:
    res = await app_client.post(
        "/v1/auth/kakao",
        json={"auth_code": code, "redirect_uri": "http://localhost"},
    )
    assert res.status_code == 200, res.text
    return res.json()


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# require_family — membership / role / family_id edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_require_family_no_membership_returns_404(app_client):
    """User A asking for User B's family members → 404 (no leak)."""
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    fam = await app_client.post("/v1/families", json={"name": "보리네"}, headers=owner_h)
    family_id = fam.json()["family"]["id"]

    outsider = await _login(app_client, "mock-user-2")
    res = await app_client.get(
        f"/v1/families/{family_id}/members",
        headers=_bearer(outsider["access"]),
    )
    assert res.status_code == 404
    assert res.json()["detail"]["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_require_family_unknown_family_id_returns_404(app_client):
    """Random UUID that does not exist → 404."""
    sess = await _login(app_client, "mock-user-1")
    random_id = uuid.uuid4()
    res = await app_client.get(
        f"/v1/families/{random_id}/members",
        headers=_bearer(sess["access"]),
    )
    assert res.status_code == 404
    assert res.json()["detail"]["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_require_family_invalid_family_uuid_returns_404(app_client):
    """Non-UUID path component → 404 (matches /v1/pets/{pet_id} policy)."""
    sess = await _login(app_client, "mock-user-1")
    res = await app_client.get(
        "/v1/families/not-a-uuid/members",
        headers=_bearer(sess["access"]),
    )
    assert res.status_code == 404
    assert res.json()["detail"]["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_require_family_member_calls_owner_endpoint_returns_403(app_client):
    """Member (non-owner) hitting an owner-only endpoint → 403 FORBIDDEN."""
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    fam = await app_client.post("/v1/families", json={"name": "보리네"}, headers=owner_h)
    family_id = fam.json()["family"]["id"]

    invite = await app_client.post(
        f"/v1/families/{family_id}/invite", headers=owner_h
    )
    invite_code = invite.json()["invite_code"]

    member = await _login(app_client, "mock-user-2")
    member_h = _bearer(member["access"])
    join = await app_client.post(
        "/v1/families/join", json={"invite_code": invite_code}, headers=member_h
    )
    assert join.status_code == 200, join.text

    # Re-login so the access token reflects the freshly granted membership;
    # require_family will see role=member and refuse the owner endpoint.
    member = await _login(app_client, "mock-user-2")
    member_h = _bearer(member["access"])

    res = await app_client.post(
        f"/v1/families/{family_id}/invite", headers=member_h
    )
    assert res.status_code == 403
    assert res.json()["detail"]["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_require_family_owner_calls_owner_endpoint_ok(app_client):
    """Owner happy path on an owner-only endpoint → 200."""
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    fam = await app_client.post("/v1/families", json={"name": "보리네"}, headers=owner_h)
    family_id = fam.json()["family"]["id"]

    res = await app_client.post(
        f"/v1/families/{family_id}/invite", headers=owner_h
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert "invite_code" in body
    assert "expires_at" in body


# ---------------------------------------------------------------------------
# current_user — token presence / validity / staleness
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_current_user_no_token_returns_401(app_client):
    res = await app_client.get("/v1/me")
    assert res.status_code == 401
    assert res.json()["detail"]["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_current_user_invalid_token_returns_401(app_client):
    res = await app_client.get(
        "/v1/me", headers={"Authorization": "Bearer garbage"}
    )
    assert res.status_code == 401
    assert res.json()["detail"]["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_current_user_token_for_deleted_user_returns_401(
    app_client, db_session
):
    """Token still cryptographically valid, but the user row is gone → 401."""
    sess = await _login(app_client, "mock-user-9")
    user_id = uuid.UUID(sess["user"]["id"])
    headers = _bearer(sess["access"])

    # Sanity: token works before deletion.
    pre = await app_client.get("/v1/me", headers=headers)
    assert pre.status_code == 200

    db_user = await db_session.get(User, user_id)
    assert db_user is not None
    await db_session.delete(db_user)
    await db_session.commit()

    res = await app_client.get("/v1/me", headers=headers)
    assert res.status_code == 401
    assert res.json()["detail"]["error"]["code"] == "UNAUTHORIZED"

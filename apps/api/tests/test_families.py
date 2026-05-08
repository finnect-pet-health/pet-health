"""Family router tests — AC6/AC7 + happy path through invite/join/members."""
from __future__ import annotations

from datetime import UTC

import pytest


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
# AC6: create family + list + /me reflects new family
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_family_and_list(app_client):
    sess = await _login(app_client, "mock-user-1")
    headers = _bearer(sess["access"])

    res = await app_client.post("/v1/families", json={"name": "보리네"}, headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["family"]["name"] == "보리네"
    assert body["member"]["role"] == "owner"
    family_id = body["family"]["id"]

    # GET /v1/families
    res = await app_client.get("/v1/families", headers=headers)
    assert res.status_code == 200
    fams = res.json()
    assert len(fams) == 1
    assert fams[0]["id"] == family_id
    assert fams[0]["name"] == "보리네"
    assert fams[0]["role"] == "owner"
    assert fams[0]["member_count"] == 1

    # /me must also include the new family
    res = await app_client.get("/v1/me", headers=headers)
    assert res.status_code == 200
    me = res.json()
    assert len(me["families"]) == 1
    assert me["families"][0]["member_count"] == 1


@pytest.mark.asyncio
async def test_create_family_requires_auth(app_client):
    res = await app_client.post("/v1/families", json={"name": "X"})
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# AC7: invite/join lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_owner_invites_and_member_joins(app_client):
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])

    # owner creates family
    res = await app_client.post("/v1/families", json={"name": "보리네"}, headers=owner_h)
    family_id = res.json()["family"]["id"]

    # owner issues invite
    res = await app_client.post(
        f"/v1/families/{family_id}/invite", json={"ttl_hours": 24}, headers=owner_h
    )
    assert res.status_code == 200, res.text
    invite_body = res.json()
    assert "invite_code" in invite_body
    assert "expires_at" in invite_body
    invite_code = invite_body["invite_code"]
    assert len(invite_code) == 8  # base32, 5 bytes → 8 chars

    # member logs in
    member = await _login(app_client, "mock-user-2")
    member_h = _bearer(member["access"])

    # member joins
    res = await app_client.post(
        "/v1/families/join", json={"invite_code": invite_code}, headers=member_h
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["family"]["id"] == family_id
    assert body["role"] == "member"

    # member_count rises to 2 in member's /me
    res = await app_client.get("/v1/me", headers=member_h)
    fams = res.json()["families"]
    assert fams[0]["member_count"] == 2

    # member listing visible to both
    res = await app_client.get(f"/v1/families/{family_id}/members", headers=owner_h)
    assert res.status_code == 200
    members = res.json()
    assert len(members) == 2
    roles = {m["role"] for m in members}
    assert roles == {"owner", "member"}


@pytest.mark.asyncio
async def test_invite_owner_only(app_client):
    """Non-owner cannot mint invites (403 FORBIDDEN)."""
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    fam_res = await app_client.post(
        "/v1/families", json={"name": "보리네"}, headers=owner_h
    )
    family_id = fam_res.json()["family"]["id"]
    invite = await app_client.post(
        f"/v1/families/{family_id}/invite", headers=owner_h
    )
    invite_code = invite.json()["invite_code"]

    member = await _login(app_client, "mock-user-2")
    member_h = _bearer(member["access"])
    await app_client.post(
        "/v1/families/join", json={"invite_code": invite_code}, headers=member_h
    )

    # member (non-owner) tries to mint a new invite
    res = await app_client.post(
        f"/v1/families/{family_id}/invite", headers=member_h
    )
    assert res.status_code == 403
    assert res.json()["detail"]["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_join_unknown_invite_code_404(app_client):
    sess = await _login(app_client, "mock-user-1")
    res = await app_client.post(
        "/v1/families/join",
        json={"invite_code": "NOPE0000"},
        headers=_bearer(sess["access"]),
    )
    assert res.status_code == 404
    assert res.json()["detail"]["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_join_already_member_409(app_client):
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    fam = await app_client.post(
        "/v1/families", json={"name": "보리네"}, headers=owner_h
    )
    family_id = fam.json()["family"]["id"]
    invite = await app_client.post(
        f"/v1/families/{family_id}/invite", headers=owner_h
    )
    code = invite.json()["invite_code"]

    # owner tries to join their own family via invite — already member (owner)
    res = await app_client.post(
        "/v1/families/join", json={"invite_code": code}, headers=owner_h
    )
    assert res.status_code == 409
    assert res.json()["detail"]["error"]["code"] == "ALREADY_MEMBER"


@pytest.mark.asyncio
async def test_join_expired_invite_410(app_client, db_session):
    """V9: family_invite.expires_at 을 backdate 해 410 검증."""
    from datetime import datetime, timedelta

    from sqlalchemy import select

    from app.models import FamilyInvite

    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    fam = await app_client.post(
        "/v1/families", json={"name": "보리네"}, headers=owner_h
    )
    family_id = fam.json()["family"]["id"]
    invite = await app_client.post(
        f"/v1/families/{family_id}/invite", headers=owner_h
    )
    code = invite.json()["invite_code"]

    # Backdate the FamilyInvite row directly.
    invite_row = (
        await db_session.execute(
            select(FamilyInvite).where(FamilyInvite.code == code)
        )
    ).scalar_one()
    invite_row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await db_session.commit()

    member = await _login(app_client, "mock-user-2")
    res = await app_client.post(
        "/v1/families/join",
        json={"invite_code": code},
        headers=_bearer(member["access"]),
    )
    assert res.status_code == 410
    assert res.json()["detail"]["error"]["code"] == "INVITE_EXPIRED"


# ---------------------------------------------------------------------------
# require_family RBAC edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_members_endpoint_403_for_outsider(app_client):
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    fam = await app_client.post(
        "/v1/families", json={"name": "보리네"}, headers=owner_h
    )
    family_id = fam.json()["family"]["id"]

    outsider = await _login(app_client, "mock-user-3")
    res = await app_client.get(
        f"/v1/families/{family_id}/members",
        headers=_bearer(outsider["access"]),
    )
    # outsider has no token claim and no DB membership → 404
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_members_endpoint_404_for_unknown_family(app_client):
    sess = await _login(app_client, "mock-user-1")
    res = await app_client.get(
        "/v1/families/00000000-0000-0000-0000-000000000000/members",
        headers=_bearer(sess["access"]),
    )
    assert res.status_code == 404

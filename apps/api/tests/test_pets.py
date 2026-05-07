"""Pet router tests — POST/GET /v1/families/{id}/pets and GET /v1/pets/{id}."""
from __future__ import annotations

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


async def _create_family(app_client, headers: dict, name: str = "보리네") -> str:
    res = await app_client.post("/v1/families", json={"name": name}, headers=headers)
    assert res.status_code == 200, res.text
    return res.json()["family"]["id"]


async def _invite_join(app_client, owner_h: dict, family_id: str, member_h: dict) -> None:
    inv = await app_client.post(
        f"/v1/families/{family_id}/invite", headers=owner_h
    )
    assert inv.status_code == 200, inv.text
    code = inv.json()["invite_code"]
    join = await app_client.post(
        "/v1/families/join", json={"invite_code": code}, headers=member_h
    )
    assert join.status_code == 200, join.text


# ---------------------------------------------------------------------------
# POST /v1/families/{id}/pets
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_pet_owner_ok(app_client):
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    family_id = await _create_family(app_client, owner_h)

    # Re-login so the access token includes the new family with owner role
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])

    res = await app_client.post(
        f"/v1/families/{family_id}/pets",
        json={
            "breed": "shiba",
            "dob": "2022-01-15",
            "weight": 8.5,
            "neutered": True,
            "conditions": ["allergy"],
        },
        headers=owner_h,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["family_id"] == family_id
    assert body["species"] == "dog"
    assert body["breed"] == "shiba"
    assert body["dob"] == "2022-01-15"
    assert body["weight"] == 8.5
    assert body["neutered"] is True
    assert body["conditions"] == ["allergy"]
    assert "id" in body and len(body["id"]) == 36


@pytest.mark.asyncio
async def test_create_pet_minimal_body_ok(app_client):
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    family_id = await _create_family(app_client, owner_h)
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])

    res = await app_client.post(
        f"/v1/families/{family_id}/pets", json={}, headers=owner_h
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["species"] == "dog"
    assert body["breed"] is None
    assert body["dob"] is None
    assert body["weight"] is None
    assert body["neutered"] is False
    assert body["conditions"] == []


@pytest.mark.asyncio
async def test_create_pet_member_403(app_client):
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    family_id = await _create_family(app_client, owner_h)

    member = await _login(app_client, "mock-user-2")
    member_h = _bearer(member["access"])
    await _invite_join(app_client, owner_h, family_id, member_h)

    # Member re-login to refresh roles map
    member = await _login(app_client, "mock-user-2")
    member_h = _bearer(member["access"])

    res = await app_client.post(
        f"/v1/families/{family_id}/pets",
        json={"breed": "shiba"},
        headers=member_h,
    )
    assert res.status_code == 403
    assert res.json()["detail"]["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_create_pet_other_family_404(app_client):
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    family_id = await _create_family(app_client, owner_h)

    outsider = await _login(app_client, "mock-user-2")
    outsider_h = _bearer(outsider["access"])

    res = await app_client.post(
        f"/v1/families/{family_id}/pets",
        json={"breed": "shiba"},
        headers=outsider_h,
    )
    assert res.status_code == 404
    assert res.json()["detail"]["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# GET /v1/families/{id}/pets
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_pets_member_ok(app_client):
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    family_id = await _create_family(app_client, owner_h)
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])

    # Owner creates 2 pets
    await app_client.post(
        f"/v1/families/{family_id}/pets",
        json={"breed": "shiba"},
        headers=owner_h,
    )
    await app_client.post(
        f"/v1/families/{family_id}/pets",
        json={"breed": "poodle"},
        headers=owner_h,
    )

    # Member joins
    member = await _login(app_client, "mock-user-2")
    member_h = _bearer(member["access"])
    await _invite_join(app_client, owner_h, family_id, member_h)

    res = await app_client.get(
        f"/v1/families/{family_id}/pets", headers=member_h
    )
    assert res.status_code == 200, res.text
    pets = res.json()
    assert len(pets) == 2
    breeds = {p["breed"] for p in pets}
    assert breeds == {"shiba", "poodle"}


# ---------------------------------------------------------------------------
# GET /v1/pets/{pet_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_pet_by_id_member_ok(app_client):
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    family_id = await _create_family(app_client, owner_h)
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])

    create_res = await app_client.post(
        f"/v1/families/{family_id}/pets",
        json={"breed": "shiba", "weight": 9.0},
        headers=owner_h,
    )
    pet_id = create_res.json()["id"]

    member = await _login(app_client, "mock-user-2")
    member_h = _bearer(member["access"])
    await _invite_join(app_client, owner_h, family_id, member_h)

    res = await app_client.get(f"/v1/pets/{pet_id}", headers=member_h)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["id"] == pet_id
    assert body["family_id"] == family_id
    assert body["breed"] == "shiba"
    assert body["weight"] == 9.0


@pytest.mark.asyncio
async def test_get_pet_other_family_403_or_404(app_client):
    """Policy: foreign pet ID returns 404 (do not leak existence)."""
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    family_id = await _create_family(app_client, owner_h)
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])

    create_res = await app_client.post(
        f"/v1/families/{family_id}/pets",
        json={"breed": "shiba"},
        headers=owner_h,
    )
    pet_id = create_res.json()["id"]

    outsider = await _login(app_client, "mock-user-2")
    outsider_h = _bearer(outsider["access"])

    res = await app_client.get(f"/v1/pets/{pet_id}", headers=outsider_h)
    assert res.status_code == 404
    assert res.json()["detail"]["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_get_pet_unknown_id_404(app_client):
    sess = await _login(app_client, "mock-user-1")
    res = await app_client.get(
        "/v1/pets/00000000-0000-0000-0000-000000000000",
        headers=_bearer(sess["access"]),
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_get_pet_invalid_uuid_404(app_client):
    sess = await _login(app_client, "mock-user-1")
    res = await app_client.get(
        "/v1/pets/not-a-uuid",
        headers=_bearer(sess["access"]),
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_create_pet_invalid_weight_422(app_client):
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    family_id = await _create_family(app_client, owner_h)
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])

    res = await app_client.post(
        f"/v1/families/{family_id}/pets",
        json={"weight": -1.0},
        headers=owner_h,
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_pet_breed_too_long_422(app_client):
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    family_id = await _create_family(app_client, owner_h)
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])

    res = await app_client.post(
        f"/v1/families/{family_id}/pets",
        json={"breed": "x" * 51},
        headers=owner_h,
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_pet_invalid_dob_422(app_client):
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])
    family_id = await _create_family(app_client, owner_h)
    owner = await _login(app_client, "mock-user-1")
    owner_h = _bearer(owner["access"])

    res = await app_client.post(
        f"/v1/families/{family_id}/pets",
        json={"dob": "not-a-date"},
        headers=owner_h,
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_pet_unauth_401(app_client):
    res = await app_client.post(
        "/v1/families/00000000-0000-0000-0000-000000000000/pets",
        json={},
    )
    assert res.status_code == 401

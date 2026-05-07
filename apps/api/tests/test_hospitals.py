"""W3-v2 head-start: `/v1/hospitals/nearby` PostGIS ST_DWithin smoke."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text


async def _seed_hospital(
    db_session,
    *,
    name: str,
    lng: float | None,
    lat: float | None,
    mgmt_no: str | None = None,
) -> str:
    hid = str(uuid.uuid4())
    await db_session.execute(
        text(
            """
            INSERT INTO hospital (id, mgmt_no, name, location, updated_at)
            VALUES (
                CAST(:id AS uuid),
                :mgmt_no,
                :name,
                CASE
                    WHEN CAST(:lng AS double precision) IS NULL
                      OR CAST(:lat AS double precision) IS NULL
                    THEN NULL
                    ELSE ST_SetSRID(
                        ST_MakePoint(
                            CAST(:lng AS double precision),
                            CAST(:lat AS double precision)
                        ),
                        4326
                    )
                END,
                now()
            )
            """
        ),
        {
            "id": hid,
            "mgmt_no": mgmt_no or hid,
            "name": name,
            "lng": lng,
            "lat": lat,
        },
    )
    await db_session.commit()
    return hid


@pytest.mark.asyncio
async def test_nearby_orders_by_distance_and_respects_radius(app_client, db_session):
    # Seoul City Hall: 37.5665, 126.9780
    near_a = await _seed_hospital(db_session, name="가까운병원A", lng=126.9785, lat=37.5670)
    near_b = await _seed_hospital(db_session, name="가까운병원B", lng=126.9800, lat=37.5680)
    far = await _seed_hospital(db_session, name="먼병원", lng=127.5000, lat=37.5670)
    no_loc = await _seed_hospital(db_session, name="좌표없는병원", lng=None, lat=None)

    resp = await app_client.get(
        "/v1/hospitals/nearby",
        params={"lat": 37.5665, "lng": 126.9780, "radius_m": 3000, "limit": 5},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    ids = [h["id"] for h in data]
    assert near_a in ids
    assert near_b in ids
    assert far not in ids
    assert no_loc not in ids

    # ASC by distance
    distances = [h["distance_m"] for h in data]
    assert distances == sorted(distances)


@pytest.mark.asyncio
async def test_nearby_limit_and_specialty_param_ignored(app_client, db_session):
    for i in range(5):
        # 모두 1km 내
        await _seed_hospital(
            db_session,
            name=f"H{i}",
            lng=126.9780 + i * 0.001,
            lat=37.5665,
        )

    resp = await app_client.get(
        "/v1/hospitals/nearby",
        params={
            "lat": 37.5665,
            "lng": 126.9780,
            "radius_m": 5000,
            "limit": 3,
            "specialty": "dermatology",  # W3-v2 무시, 200 유지가 AC12
        },
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 3


@pytest.mark.asyncio
async def test_nearby_validates_inputs(app_client):
    resp = await app_client.get(
        "/v1/hospitals/nearby",
        params={"lat": 999, "lng": 0, "radius_m": 1000},
    )
    assert resp.status_code == 422

    resp = await app_client.get(
        "/v1/hospitals/nearby",
        params={"lat": 37.5, "lng": 127.0, "radius_m": 999999},
    )
    assert resp.status_code == 422

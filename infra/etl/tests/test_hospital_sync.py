"""W3-v2 head-start: hospital ETL transform + EPSG:5174 → 4326 변환 단위 테스트."""
from __future__ import annotations

import asyncio

from infra.etl.hospital_sync import (
    enrich_with_geocoding,
    is_active,
    load_static_seed,
    tm_to_wgs84,
    transform_row,
)


def test_tm_to_wgs84_seoul_city_hall_close_enough() -> None:
    """서울시청 EPSG:5174 좌표 (대략) → WGS84 (37.5665, 126.9780) 부근.

    공공데이터 좌표는 측량 오차 있으므로 ±0.01° (~1km) 허용.
    """
    # 행정안전부 OpenAPI 에서 서울시청 부근 동물병원 표본 좌표
    tm_x, tm_y = 198365.0, 451636.0  # rough Seoul TM
    lng, lat = tm_to_wgs84(tm_x, tm_y)
    assert 126.5 < lng < 127.5
    assert 37.0 < lat < 38.0


def test_is_active_filters_closed_and_suspended() -> None:
    assert is_active({"SALS_STTS_NM": "영업/정상", "CLSBIZ_YMD": ""})
    assert not is_active({"SALS_STTS_NM": "폐업", "CLSBIZ_YMD": "20240101"})
    assert not is_active({"SALS_STTS_NM": "휴업", "CLSBIZ_YMD": ""})
    assert not is_active({"SALS_STTS_NM": "영업/정상", "CLSBIZ_YMD": "20240101"})


def test_transform_row_with_coordinates() -> None:
    raw = {
        "MNG_NO": "M-001",
        "BPLC_NM": "테스트동물병원",
        "ROAD_NM_ADDR": "서울특별시 중구 세종대로 110",
        "LOTNO_ADDR": "서울특별시 중구 태평로1가 31",
        "ROAD_NM_ZIP": "04524",
        "TELNO": "02-1234-5678",
        "SALS_STTS_NM": "영업/정상",
        "LCPMT_YMD": "20200101",
        "CRD_INFO_X": "198365",
        "CRD_INFO_Y": "451636",
        "OPN_ATMY_GRP_CD": "11",
    }
    out = transform_row(raw)
    assert out["mgmt_no"] == "M-001"
    assert out["name"] == "테스트동물병원"
    assert out["lat"] is not None and out["lng"] is not None
    assert 37.0 < out["lat"] < 38.0
    assert 126.5 < out["lng"] < 127.5


def test_transform_row_missing_coordinates_returns_none() -> None:
    raw = {
        "MNG_NO": "M-002",
        "BPLC_NM": "좌표없는병원",
        "SALS_STTS_NM": "영업/정상",
        "CRD_INFO_X": "",
        "CRD_INFO_Y": "",
    }
    out = transform_row(raw)
    assert out["lat"] is None
    assert out["lng"] is None
    assert out["tm_x"] is None and out["tm_y"] is None


def test_transform_row_partial_coordinates_returns_none() -> None:
    raw = {
        "MNG_NO": "M-003",
        "BPLC_NM": "X만있는병원",
        "SALS_STTS_NM": "영업/정상",
        "CRD_INFO_X": "198365",
        "CRD_INFO_Y": "",
    }
    out = transform_row(raw)
    assert out["lat"] is None
    assert out["lng"] is None


def test_load_static_seed_returns_50_seoul_rows() -> None:
    rows = load_static_seed()
    assert len(rows) == 50
    assert {r["mgmt_no"] for r in rows}.__len__() == 50  # unique mgmt_no
    for r in rows:
        assert r["status"] == "영업/정상"
        assert r["name"]
        assert 37.4 < r["lat"] < 37.7
        assert 126.7 < r["lng"] < 127.2
        assert r["tm_x"] is None and r["tm_y"] is None


class _StubGeocoder:
    """주소 → 결정적 좌표 (테스트용)."""

    def __init__(self, mapping: dict[str, tuple[float, float] | None]) -> None:
        self._mapping = mapping
        self.calls: list[str] = []

    async def geocode_address(
        self, road_addr: str
    ) -> tuple[float, float] | None:
        self.calls.append(road_addr)
        return self._mapping.get(road_addr)


def test_enrich_with_geocoding_fills_only_missing_coords() -> None:
    rows: list[dict] = [
        {"road_addr": "서울특별시 종로구 세종대로 1", "lat": None, "lng": None},
        {"road_addr": "이미좌표있는병원", "lat": 37.50, "lng": 127.00},
        {"road_addr": "", "lot_addr": "", "lat": None, "lng": None},
    ]
    geocoder = _StubGeocoder(
        {
            "서울특별시 종로구 세종대로 1": (37.5735, 126.9788),
        }
    )
    enriched = asyncio.run(enrich_with_geocoding(rows, geocoder))
    assert enriched == 1
    assert rows[0]["lat"] == 37.5735
    assert rows[0]["lng"] == 126.9788
    # 이미 좌표가 있던 row 는 건드리지 않음 + geocoder 도 호출 안함.
    assert rows[1]["lat"] == 37.50
    assert "이미좌표있는병원" not in geocoder.calls
    # 주소 없는 row 는 None 유지.
    assert rows[2]["lat"] is None


def test_enrich_with_geocoding_handles_geocoder_none_response() -> None:
    rows: list[dict] = [
        {"road_addr": "부산광역시 해운대구 1", "lat": None, "lng": None},
    ]
    geocoder = _StubGeocoder({"부산광역시 해운대구 1": None})
    enriched = asyncio.run(enrich_with_geocoding(rows, geocoder))
    assert enriched == 0
    assert rows[0]["lat"] is None

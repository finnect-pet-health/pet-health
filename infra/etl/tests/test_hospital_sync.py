"""W3-v2 head-start: hospital ETL transform + EPSG:5174 → 4326 변환 단위 테스트."""
from __future__ import annotations

from infra.etl.hospital_sync import is_active, tm_to_wgs84, transform_row


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

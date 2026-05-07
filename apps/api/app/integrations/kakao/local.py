"""카카오 로컬 API — 도로명 주소 → WGS84 lat/lng 지오코딩.

W3-v2: 동물병원 OpenAPI 가 좌표 결측 row 를 반환할 때 fallback.
실 endpoint: `https://dapi.kakao.com/v2/local/search/address.json`
헤더: `Authorization: KakaoAK {KAKAO_REST_API_KEY}`

W3-v2 head-start: mock-first. 실 구현은 실제 ETL 운영 시점에 RUNTIME 추가.
"""
from __future__ import annotations

import hashlib
import os
import warnings
from typing import Protocol

# 서울시 박스 (37.413~37.715, 126.764~127.184). 서울 외 주소는 None 반환.
_SEOUL_LAT_RANGE = (37.413, 37.715)
_SEOUL_LNG_RANGE = (126.764, 127.184)


class KakaoLocalClient(Protocol):
    async def geocode_address(
        self, road_addr: str
    ) -> tuple[float, float] | None: ...


class MockKakaoLocalClient:
    """결정적 mock: 주소 sha256 → 서울 박스 내 균등 분포 lat/lng.

    "서울" 키워드가 없는 주소는 None (서울 외 주소 시뮬레이션).
    """

    async def geocode_address(
        self, road_addr: str
    ) -> tuple[float, float] | None:
        if "서울" not in road_addr:
            return None
        h = hashlib.sha256(road_addr.encode("utf-8")).digest()
        lat_frac = int.from_bytes(h[:4], "big") / 0xFFFFFFFF
        lng_frac = int.from_bytes(h[4:8], "big") / 0xFFFFFFFF
        lat = _SEOUL_LAT_RANGE[0] + lat_frac * (
            _SEOUL_LAT_RANGE[1] - _SEOUL_LAT_RANGE[0]
        )
        lng = _SEOUL_LNG_RANGE[0] + lng_frac * (
            _SEOUL_LNG_RANGE[1] - _SEOUL_LNG_RANGE[0]
        )
        return round(lat, 6), round(lng, 6)


def get_kakao_local_client() -> KakaoLocalClient:
    """`KAKAO_LOCAL_USE_MOCK=1` 또는 KAKAO_REST_API_KEY 미설정 → mock."""
    use_mock = (
        os.getenv("KAKAO_LOCAL_USE_MOCK", "") == "1"
        or not os.getenv("KAKAO_REST_API_KEY", "")
    )
    if not use_mock:
        warnings.warn(
            "real KakaoLocalClient (REST geocoding) not yet implemented — "
            "falling back to mock; set KAKAO_LOCAL_USE_MOCK=1 to silence",
            RuntimeWarning,
            stacklevel=2,
        )
    return MockKakaoLocalClient()

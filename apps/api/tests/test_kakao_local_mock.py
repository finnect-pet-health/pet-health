"""W3-v2 head-start: MockKakaoLocalClient 결정성 + 서울 박스 검증."""
from __future__ import annotations

import pytest

from app.integrations.kakao.local import MockKakaoLocalClient


@pytest.mark.asyncio
async def test_mock_geocode_in_seoul_bbox():
    client = MockKakaoLocalClient()
    result = await client.geocode_address("서울특별시 종로구 세종대로 1")
    assert result is not None
    lat, lng = result
    assert 37.413 <= lat <= 37.715
    assert 126.764 <= lng <= 127.184


@pytest.mark.asyncio
async def test_mock_geocode_returns_none_for_non_seoul():
    client = MockKakaoLocalClient()
    assert await client.geocode_address("부산광역시 해운대구 1") is None
    assert await client.geocode_address("") is None


@pytest.mark.asyncio
async def test_mock_geocode_is_deterministic():
    client = MockKakaoLocalClient()
    a = await client.geocode_address("서울특별시 강남구 테헤란로 152")
    b = await client.geocode_address("서울특별시 강남구 테헤란로 152")
    assert a == b


@pytest.mark.asyncio
async def test_mock_geocode_distinguishes_addresses():
    client = MockKakaoLocalClient()
    a = await client.geocode_address("서울특별시 종로구 1")
    b = await client.geocode_address("서울특별시 종로구 2")
    assert a != b

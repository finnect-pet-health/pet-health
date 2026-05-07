"""Tests for MockHealthProvider."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.integrations.health import HealthSnapshot, HealthSource
from app.integrations.health.mock import _ANOMALY_DAYS, _DAYS, MockHealthProvider


@pytest.fixture
def provider() -> MockHealthProvider:
    return MockHealthProvider()


@pytest.fixture
def pet_id() -> uuid.UUID:
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.mark.asyncio
async def test_deterministic_same_pet_id(provider, pet_id):
    """Same pet_id must return identical snapshots across two calls."""
    since = datetime.now(UTC) - timedelta(days=_DAYS)
    snapshots_a = await provider.fetch_window(pet_id, since)
    snapshots_b = await provider.fetch_window(pet_id, since)
    assert len(snapshots_a) == len(snapshots_b)
    for a, b in zip(snapshots_a, snapshots_b, strict=False):
        assert a.activity_min == b.activity_min
        assert a.hr_avg == b.hr_avg
        assert a.sleep_state == b.sleep_state


@pytest.mark.asyncio
async def test_different_pet_ids_differ(provider):
    """Different pet_ids should generally produce different data."""
    since = datetime.now(UTC) - timedelta(days=_DAYS)
    pet_a = uuid.uuid4()
    pet_b = uuid.uuid4()
    snaps_a = await provider.fetch_window(pet_a, since)
    snaps_b = await provider.fetch_window(pet_b, since)
    # At least one activity value should differ (astronomically unlikely to be identical)
    activities_a = [s.activity_min for s in snaps_a]
    activities_b = [s.activity_min for s in snaps_b]
    assert activities_a != activities_b


@pytest.mark.asyncio
async def test_returns_expected_day_count(provider, pet_id):
    since = datetime.now(UTC) - timedelta(days=_DAYS)
    snapshots = await provider.fetch_window(pet_id, since)
    assert len(snapshots) == _DAYS


@pytest.mark.asyncio
async def test_source_is_mock(provider, pet_id):
    since = datetime.now(UTC) - timedelta(days=_DAYS)
    snapshots = await provider.fetch_window(pet_id, since)
    assert all(s.source == HealthSource.mock for s in snapshots)


@pytest.mark.asyncio
async def test_quality_is_one(provider, pet_id):
    since = datetime.now(UTC) - timedelta(days=_DAYS)
    snapshots = await provider.fetch_window(pet_id, since)
    assert all(s.quality == 1.0 for s in snapshots)


@pytest.mark.asyncio
async def test_anomaly_last_3_days_lower_activity(provider, pet_id):
    """Last 3 days must have lower average activity_min than first 11 days."""
    since = datetime.now(UTC) - timedelta(days=_DAYS)
    snapshots = await provider.fetch_window(pet_id, since)

    # snapshots are ordered oldest→newest (day_offset 13 down to 0)
    normal_days = snapshots[: _DAYS - _ANOMALY_DAYS]   # first 11 days
    anomaly_days = snapshots[_DAYS - _ANOMALY_DAYS :]  # last 3 days

    assert len(normal_days) == _DAYS - _ANOMALY_DAYS
    assert len(anomaly_days) == _ANOMALY_DAYS

    avg_normal = sum(s.activity_min for s in normal_days) / len(normal_days)
    avg_anomaly = sum(s.activity_min for s in anomaly_days) / len(anomaly_days)
    assert avg_anomaly < avg_normal, (
        f"Anomaly avg activity {avg_anomaly:.1f} should be < normal {avg_normal:.1f}"
    )


@pytest.mark.asyncio
async def test_since_filter_applied(provider, pet_id):
    """since=today should return only today's snapshot."""
    since = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    snapshots = await provider.fetch_window(pet_id, since)
    assert len(snapshots) == 1


@pytest.mark.asyncio
async def test_all_snapshots_have_pet_id(provider, pet_id):
    since = datetime.now(UTC) - timedelta(days=_DAYS)
    snapshots = await provider.fetch_window(pet_id, since)
    assert all(s.pet_id == pet_id for s in snapshots)


@pytest.mark.asyncio
async def test_snapshot_schema(provider, pet_id):
    since = datetime.now(UTC) - timedelta(days=_DAYS)
    snapshots = await provider.fetch_window(pet_id, since)
    for snap in snapshots:
        assert isinstance(snap, HealthSnapshot)
        assert snap.activity_min >= 0
        assert snap.hr_avg is not None and snap.hr_avg >= 40

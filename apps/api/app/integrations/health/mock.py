from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime, timedelta

from app.integrations.health import HealthSnapshot, HealthSource, SleepState

_DAYS = 14
_ANOMALY_DAYS = 3  # last N days are anomalous


class MockHealthProvider:
    """Returns deterministic 14-day daily health snapshots seeded by pet_id hash.

    Last 3 days show anomaly pattern:
      - activity_min: -30% vs 11-day average
      - hr_avg: +10% vs 11-day average
      - sleep_state deep ratio: lower (more 'light' instead of 'deep')
    """

    async def fetch_window(
        self, pet_id: uuid.UUID, since: datetime
    ) -> list[HealthSnapshot]:
        seed = int(uuid.UUID(str(pet_id)).int % (2**31))
        rng = random.Random(seed)  # noqa: S311

        now = datetime.now(UTC).replace(hour=12, minute=0, second=0, microsecond=0)

        # Generate baseline parameters deterministically (always consumed first)
        base_activity = rng.uniform(45.0, 75.0)
        base_hr = rng.uniform(80.0, 110.0)
        base_weight = rng.uniform(6.0, 12.0)

        # Generate ALL _DAYS records unconditionally so RNG state is stable;
        # filter afterward so 'since' does not affect per-day values.
        all_snapshots: list[HealthSnapshot] = []
        for i in range(_DAYS):
            day_offset = _DAYS - 1 - i  # 13 = oldest, 0 = today
            ts = now - timedelta(days=day_offset)
            is_anomaly = day_offset < _ANOMALY_DAYS

            if is_anomaly:
                activity_min = base_activity * 0.70 + rng.uniform(-3.0, 3.0)
                hr_avg = base_hr * 1.10 + rng.uniform(-2.0, 2.0)
                # Anomaly: more light sleep, less deep
                sleep_state = rng.choice(
                    [SleepState.awake, SleepState.light, SleepState.light, SleepState.deep]
                )
            else:
                activity_min = base_activity + rng.uniform(-8.0, 8.0)
                hr_avg = base_hr + rng.uniform(-5.0, 5.0)
                sleep_state = rng.choice(
                    [SleepState.awake, SleepState.light, SleepState.deep, SleepState.deep]
                )

            hr_min = max(40.0, hr_avg - rng.uniform(5.0, 15.0))
            hr_max = hr_avg + rng.uniform(5.0, 20.0)
            weight = base_weight + rng.uniform(-0.2, 0.2)

            all_snapshots.append(
                HealthSnapshot(
                    pet_id=pet_id,
                    ts=ts,
                    ingest_ts=ts + timedelta(minutes=5),
                    source=HealthSource.mock,
                    activity_min=max(0.0, activity_min),
                    hr_avg=max(40.0, hr_avg),
                    hr_min=hr_min,
                    hr_max=hr_max,
                    sleep_state=sleep_state,
                    weight=weight,
                    quality=1.0,
                )
            )

        return [s for s in all_snapshots if s.ts >= since]

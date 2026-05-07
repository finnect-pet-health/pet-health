from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field


class HealthSource(StrEnum):
    caretail = "caretail"
    manual = "manual"
    mock = "mock"


class SleepState(StrEnum):
    awake = "awake"
    light = "light"
    deep = "deep"


class HealthSnapshot(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    pet_id: uuid.UUID
    ts: datetime                    # data timestamp (UTC)
    ingest_ts: datetime             # ingestion timestamp
    source: HealthSource
    activity_min: float             # active minutes in window
    hr_avg: float | None = None     # avg heart rate (bpm)
    hr_min: float | None = None
    hr_max: float | None = None
    sleep_state: SleepState | None = None
    weight: float | None = None     # kg, ~once per day
    raw_blob_ref: str | None = None
    quality: float = 1.0            # 0–1


class HealthProvider(Protocol):
    async def fetch_window(
        self, pet_id: uuid.UUID, since: datetime
    ) -> list[HealthSnapshot]:
        ...

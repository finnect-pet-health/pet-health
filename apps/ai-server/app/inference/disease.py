"""Stage 1 (anomaly) + Stage 2 (disease classifier) 추론.

MVP: 룰 기반 anomaly + placeholder 질병 후보. 본선 전 fine-tuned 모델로 교체.
"""
from __future__ import annotations

import statistics

from app.schemas import ActionEnum, DiseaseCandidate, DiseaseInferIn, DiseaseInferOut


def _rolling_anomaly(snapshots) -> tuple[float, dict[str, float]]:
    if not snapshots:
        return 0.0, {}
    activities = [s.activity_min for s in snapshots if s.activity_min is not None]
    hrs = [s.hr_avg for s in snapshots if s.hr_avg is not None]

    contributions: dict[str, float] = {}
    score = 0.0

    if len(activities) >= 3:
        recent = statistics.mean(activities[-3:])
        baseline = statistics.mean(activities[:-3]) if len(activities) > 3 else recent
        if baseline > 0:
            drop = max(0.0, (baseline - recent) / baseline)
            score = max(score, drop)
            contributions["activity_drop"] = drop

    if len(hrs) >= 5:
        z = (hrs[-1] - statistics.mean(hrs)) / (statistics.stdev(hrs) + 1e-6)
        score = max(score, min(abs(z) / 4.0, 1.0))
        contributions["hr_zscore"] = float(abs(z))

    return min(score, 1.0), contributions


def infer_disease(payload: DiseaseInferIn) -> DiseaseInferOut:
    anomaly_score, contributions = _rolling_anomaly(payload.snapshots)

    top: list[DiseaseCandidate] = []
    if anomaly_score >= 0.5:
        top = [
            DiseaseCandidate(label="위장 트러블", prob=0.18, confidence_band=(0.10, 0.28)),
            DiseaseCandidate(label="관절 통증", prob=0.10, confidence_band=(0.05, 0.18)),
            DiseaseCandidate(label="감염성 발열", prob=0.06, confidence_band=(0.02, 0.12)),
        ]

    action: ActionEnum
    if anomaly_score >= 0.7 or any(c.prob >= 0.4 for c in top):
        action = "immediate"
    elif anomaly_score >= 0.4:
        action = "schedule"
    else:
        action = "observe"

    return DiseaseInferOut(
        anomaly_score=anomaly_score,
        feature_contributions=contributions,
        top_diseases=top,
        action=action,
    )

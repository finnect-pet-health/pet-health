#!/usr/bin/env bash
# Audio 데이터셋 다운로드: Kaggle dog cough + ESC-50 dog 라벨 추출.
#
# Kaggle dog cough 슬러그는 Day 1 검수 후 확정. 환경변수 DOG_COUGH_SLUG override 가능.
# ESC-50 은 BSD-3 (대부분의 클립) + CC BY-NC 3.0 (일부) — 학술 사용 한정.
#   본선 후 자체 녹음 + 라이선스 명확한 데이터로 swap 의무.

set -euo pipefail

DOG_COUGH_SLUG="${DOG_COUGH_SLUG:-mahdialnaeb/dog-cough}"
ESC50_REPO="${ESC50_REPO:-https://github.com/karolpiczak/ESC-50.git}"
DEST="${1:-apps/ai-server/data/audio}"

mkdir -p "${DEST}/dog_cough" "${DEST}/esc50_dog"

# --- Kaggle dog cough ---
if command -v kaggle >/dev/null 2>&1; then
  echo "[audio] downloading ${DOG_COUGH_SLUG} → ${DEST}/dog_cough"
  kaggle datasets download -d "${DOG_COUGH_SLUG}" -p "${DEST}/dog_cough" --unzip
else
  echo "[audio] kaggle CLI 미설치 — Kaggle dog cough 단계 skip" >&2
fi

# --- ESC-50 ---
ESC50_TMP="${DEST}/.esc50_repo"
if [ ! -d "${ESC50_TMP}" ]; then
  echo "[audio] cloning ESC-50"
  git clone --depth 1 "${ESC50_REPO}" "${ESC50_TMP}"
fi

python <<PY
from __future__ import annotations
import csv, shutil
from pathlib import Path

repo = Path("${ESC50_TMP}")
out = Path("${DEST}/esc50_dog")
out.mkdir(parents=True, exist_ok=True)

with (repo / "meta" / "esc50.csv").open() as f:
    reader = csv.DictReader(f)
    n = 0
    for row in reader:
        if row["category"] != "dog":
            continue
        src = repo / "audio" / row["filename"]
        if src.exists():
            shutil.copy2(src, out / row["filename"])
            n += 1
    print(f"[audio] ESC-50 dog 클립 {n}건 추출 → {out}")
PY

echo "[audio] done. NOTE: ESC-50 은 비상업 한정 — 본선 후 swap 의무 (docs/data/dataset-licenses-w3.md 참조)"

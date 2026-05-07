#!/usr/bin/env bash
# Vision 데이터셋 다운로드 + 8:2 train/val split.
#
# 전제: Kaggle CLI 설치 + ~/.kaggle/kaggle.json 토큰 셋업.
#   pip install kaggle
#   chmod 600 ~/.kaggle/kaggle.json
#
# 데이터셋 슬러그(Day 1 검수 후 확정 — 라이선스 미정 시 § 1.2 fallback 으로 swap).
# 환경변수 SKIN_DATASET_SLUG 로 override 가능.

set -euo pipefail

SLUG="${SKIN_DATASET_SLUG:-prudhvignv/dog-skin-diseases-image-dataset}"
DEST="${1:-apps/ai-server/data/skin}"
TRAIN_RATIO="${TRAIN_RATIO:-0.8}"

if ! command -v kaggle >/dev/null 2>&1; then
  echo "kaggle CLI 미설치 — 'pip install kaggle' 후 다시 시도" >&2
  exit 1
fi

mkdir -p "${DEST}/raw"
echo "[skin] downloading ${SLUG} → ${DEST}/raw"
kaggle datasets download -d "${SLUG}" -p "${DEST}/raw" --unzip

echo "[skin] splitting train/val (ratio=${TRAIN_RATIO})"
python <<PY
from __future__ import annotations
import os, random, shutil
from pathlib import Path

random.seed(42)
src = Path("${DEST}/raw")
train_dir = Path("${DEST}/train")
val_dir = Path("${DEST}/val")
train_dir.mkdir(parents=True, exist_ok=True)
val_dir.mkdir(parents=True, exist_ok=True)

# 클래스 폴더(=라벨) 단위로 split.
for cls_dir in sorted(p for p in src.iterdir() if p.is_dir()):
    files = sorted(p for p in cls_dir.iterdir() if p.is_file())
    random.shuffle(files)
    split = int(len(files) * float(${TRAIN_RATIO}))
    for i, f in enumerate(files):
        target_root = train_dir if i < split else val_dir
        out_dir = target_root / cls_dir.name
        out_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, out_dir / f.name)
    print(f"  {cls_dir.name}: {len(files)} → train {split}, val {len(files)-split}")

print("[skin] done")
PY

"""W3-v2 D2 (Track A) — AnimalCLAP encoder frozen + MLP head fine-tune.

데이터 폴더 구조:
    {data-dir}/
      정상/*.wav
      기침/*.wav
      이상호흡/*.wav
      꼬르륵/*.wav
      기타/*.wav

실행:
    python scripts/train_audio.py \\
        --encoder animalclap \\
        --data-dir data/audio_labeled \\
        --out models/audio/head.pt \\
        --epochs 1

`--encoder yamnet` 으로 fallback 1줄 swap.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

CATEGORIES = ["정상", "기침", "이상호흡", "꼬르륵", "기타"]


def _load_audio_categories() -> list[str]:
    seeds = (
        Path(__file__).resolve().parents[3]
        / "apps"
        / "api"
        / "seeds"
        / "disease_labels.json"
    )
    with seeds.open() as f:
        catalog = json.load(f)
    return [c["label"] for c in catalog["audio_categories"]]


def _resample_mono_16k(path: Path, target_sr: int = 16_000) -> Any:
    import librosa
    import numpy as np

    y, sr = librosa.load(str(path), sr=target_sr, mono=True)
    return np.asarray(y, dtype=np.float32)


def _animalclap_extract(samples: list[Any]) -> Any:
    """배치 audio → 512-dim L2-normalized embeddings. spike_animalclap.py 자산 활용."""
    import numpy as np
    import torch
    from transformers import ClapModel, ClapProcessor

    proc = ClapProcessor.from_pretrained("risashinoda/animalclap")
    model = ClapModel.from_pretrained("risashinoda/animalclap")
    model.eval()
    out = []
    with torch.no_grad():
        for audio in samples:
            inputs = proc(audios=audio, sampling_rate=16_000, return_tensors="pt")
            features = model.get_audio_features(**inputs).pooler_output
            features = features / features.norm(dim=-1, keepdim=True)
            out.append(features.squeeze(0).cpu().numpy())
    return np.stack(out)  # (N, 512)


def _yamnet_extract(_samples: list[Any]) -> Any:
    raise NotImplementedError(
        "YAMNet fallback — D2 후반에 librosa + tensorflow_hub 또는 torchaudio.pipelines 로 구현"
    )


def _build_head(in_dim: int, num_classes: int) -> Any:
    import torch.nn as nn

    return nn.Sequential(
        nn.Linear(in_dim, 128),
        nn.ReLU(inplace=True),
        nn.Dropout(0.3),
        nn.Linear(128, num_classes),
    )


def _collect(data_dir: Path) -> tuple[list[Path], list[int], list[str]]:
    classes = sorted(p.name for p in data_dir.iterdir() if p.is_dir())
    paths: list[Path] = []
    labels: list[int] = []
    for idx, cls in enumerate(classes):
        for f in sorted((data_dir / cls).iterdir()):
            if f.suffix.lower() in {".wav", ".mp3", ".m4a", ".flac"}:
                paths.append(f)
                labels.append(idx)
    return paths, labels, classes


def _run_train(args: argparse.Namespace) -> int:
    import numpy as np
    import torch
    from sklearn.model_selection import train_test_split
    from tqdm.auto import tqdm

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"[train_audio] {data_dir} 부재. audio_download.sh 실행 후 라벨링 필요.", file=sys.stderr)
        return 2

    paths, labels, classes = _collect(data_dir)
    if not paths:
        print(f"[train_audio] {data_dir} 안 클립 0개. 데이터 라벨링 필요.", file=sys.stderr)
        return 2

    expected = _load_audio_categories()
    print(f"[train_audio] classes={classes} expected={expected}")
    if set(classes) != set(expected):
        print(
            "[train_audio] WARNING — 데이터 폴더 라벨이 disease_labels.json 와 다릅니다.",
            file=sys.stderr,
        )

    print(f"[train_audio] loading {len(paths)} clips (resample 16kHz mono)")
    samples = [_resample_mono_16k(p) for p in tqdm(paths)]

    print(f"[train_audio] encoder={args.encoder}")
    if args.encoder == "animalclap":
        embeddings = _animalclap_extract(samples)
    elif args.encoder == "yamnet":
        embeddings = _yamnet_extract(samples)
    else:
        raise ValueError(f"unknown encoder: {args.encoder}")

    X_train, X_val, y_train, y_val = train_test_split(
        embeddings,
        np.array(labels),
        test_size=0.2,
        random_state=42,
        stratify=labels if len(set(labels)) > 1 else None,
    )

    device = torch.device(
        "cuda" if torch.cuda.is_available() and args.device != "cpu" else "cpu"
    )
    head = _build_head(in_dim=embeddings.shape[1], num_classes=len(classes)).to(device)
    optimizer = torch.optim.AdamW(head.parameters(), lr=args.lr, weight_decay=1e-4)
    criterion = torch.nn.CrossEntropyLoss()

    Xt = torch.tensor(X_train, dtype=torch.float32, device=device)
    yt = torch.tensor(y_train, dtype=torch.long, device=device)
    Xv = torch.tensor(X_val, dtype=torch.float32, device=device)
    yv = torch.tensor(y_val, dtype=torch.long, device=device)

    best_acc = 0.0
    for epoch in range(args.epochs):
        head.train()
        optimizer.zero_grad()
        logits = head(Xt)
        loss = criterion(logits, yt)
        loss.backward()
        optimizer.step()

        head.eval()
        with torch.no_grad():
            preds = head(Xv).argmax(dim=1)
            acc = float((preds == yv).float().mean().item())
        print(f"[train_audio] epoch={epoch + 1} loss={loss.item():.4f} val_acc={acc:.4f}")

        if acc > best_acc:
            best_acc = acc
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            torch.save(
                {
                    "head_state_dict": head.state_dict(),
                    "classes": classes,
                    "encoder": args.encoder,
                    "embedding_dim": embeddings.shape[1],
                },
                out,
            )
            print(f"[train_audio] saved → {out} (val_acc={acc:.4f})")

    print(f"[train_audio] done. best_val_acc={best_acc:.4f}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AnimalCLAP encoder frozen + MLP head fine-tune")
    parser.add_argument("--encoder", choices=["animalclap", "yamnet"], default="animalclap")
    parser.add_argument("--data-dir", required=True, help="카테고리별 폴더 (정상/기침/...)")
    parser.add_argument("--out", required=True, help="head 가중치 저장 경로 (.pt)")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    args = parser.parse_args()
    return _run_train(args)


if __name__ == "__main__":
    raise SystemExit(main())

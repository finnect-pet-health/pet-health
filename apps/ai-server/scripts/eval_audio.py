"""W3-v2 D3 — Audio holdout 평가. AC5 검증 (binary cough F1 ≥ 0.75 + 5-class macro-F1).

실행:
    python scripts/eval_audio.py \\
        --head-weights models/audio/head.pt \\
        --data-dir data/audio_labeled \\
        --out docs/ai/audio-eval-w3.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


def _resample_mono_16k(path: Path) -> Any:
    import librosa
    import numpy as np

    y, _ = librosa.load(str(path), sr=16_000, mono=True)
    return np.asarray(y, dtype=np.float32)


def _animalclap_extract(samples: list[Any]) -> Any:
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
    return np.stack(out)


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


def _format_markdown(
    classes: list[str], binary_f1: float, macro_f1: float, encoder: str
) -> str:
    return (
        f"# Audio eval — encoder={encoder} (W3-v2 D3, AC5)\n\n"
        f"- binary 기침 vs 비기침 F1: **{binary_f1:.4f}**\n"
        f"- 5-class macro F1: **{macro_f1:.4f}**\n"
        f"- target binary F1 ≥ 0.75 — **{'PASS' if binary_f1 >= 0.75 else 'FAIL'}**\n\n"
        f"## classes\n\n"
        + "\n".join(f"- {c}" for c in classes)
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Audio holdout eval (binary + 5-class F1)")
    parser.add_argument("--head-weights", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--out", default=None)
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    args = parser.parse_args()

    import numpy as np
    import torch
    from sklearn.metrics import f1_score
    from sklearn.model_selection import train_test_split

    if not Path(args.head_weights).exists():
        print(f"[eval_audio] {args.head_weights} 부재. train_audio.py 먼저 실행.", file=sys.stderr)
        return 2

    ckpt = torch.load(args.head_weights, map_location="cpu")
    classes: list[str] = ckpt["classes"]
    encoder: str = ckpt.get("encoder", "animalclap")
    in_dim: int = ckpt.get("embedding_dim", 512)

    paths, labels, found_classes = _collect(Path(args.data_dir))
    if found_classes != classes:
        print(
            f"[eval_audio] WARNING — data classes {found_classes} 와 weights {classes} 불일치",
            file=sys.stderr,
        )

    samples = [_resample_mono_16k(p) for p in paths]
    if encoder == "animalclap":
        emb = _animalclap_extract(samples)
    else:
        print(f"[eval_audio] encoder={encoder} 미구현", file=sys.stderr)
        return 2

    _, X_val, _, y_val = train_test_split(
        emb, np.array(labels), test_size=0.2, random_state=42, stratify=labels
    )

    device = torch.device(
        "cuda" if torch.cuda.is_available() and args.device != "cpu" else "cpu"
    )
    head = _build_head(in_dim=in_dim, num_classes=len(classes)).to(device)
    head.load_state_dict(ckpt["head_state_dict"])
    head.eval()

    Xv = torch.tensor(X_val, dtype=torch.float32, device=device)
    with torch.no_grad():
        preds = head(Xv).argmax(dim=1).cpu().numpy()

    cough_idx = classes.index("기침") if "기침" in classes else 1
    y_bin = (y_val == cough_idx).astype(int)
    p_bin = (preds == cough_idx).astype(int)
    binary_f1 = f1_score(y_bin, p_bin, zero_division=0.0)
    macro_f1 = f1_score(y_val, preds, average="macro", zero_division=0.0)

    md = _format_markdown(classes, binary_f1, macro_f1, encoder)
    print(md)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"[eval_audio] saved → {out}")
    return 0 if binary_f1 >= 0.75 else 1


if __name__ == "__main__":
    raise SystemExit(main())

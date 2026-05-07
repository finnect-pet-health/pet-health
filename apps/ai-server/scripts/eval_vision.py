"""W3-v2 D3 — Vision holdout 평가. AC3 검증 (top-1 ≥ 70%).

실행:
    python scripts/eval_vision.py \\
        --weights models/vision/skin.pt \\
        --data-dir data/skin \\
        --out docs/ai/vision-eval-w3.md

결과: holdout val/ 폴더 top-1 + per-class confusion + markdown 표.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


def _build_loader(data_dir: Path, batch_size: int, num_workers: int) -> tuple[Any, list[str]]:
    from torch.utils.data import DataLoader
    from torchvision import transforms
    from torchvision.datasets import ImageFolder

    tf = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    ds = ImageFolder(str(data_dir / "val"), transform=tf)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    return loader, list(ds.classes)


def _build_model(num_classes: int) -> Any:
    from torchvision.models import mobilenet_v3_small

    model = mobilenet_v3_small(weights=None)
    in_features = model.classifier[-1].in_features
    import torch.nn as nn

    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


def _format_markdown(
    classes: list[str], confusion: list[list[int]], top1: float, region: str
) -> str:
    lines = [
        f"# Vision eval — region={region} (W3-v2 D3, AC3)",
        "",
        f"- holdout top-1 accuracy: **{top1:.4f}**",
        f"- target ≥ 0.70 — **{'PASS' if top1 >= 0.70 else 'FAIL'}**",
        "",
        "## Per-class confusion (rows: true, cols: pred)",
        "",
        "| | " + " | ".join(classes) + " |",
        "|---|" + "|".join("---" for _ in classes) + "|",
    ]
    for i, cls in enumerate(classes):
        row = f"| {cls} | " + " | ".join(str(confusion[i][j]) for j in range(len(classes))) + " |"
        lines.append(row)
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Vision holdout eval (top-1 + confusion)")
    parser.add_argument("--weights", required=True, help="train_vision.py 산출물 .pt")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--out", default=None, help="결과 markdown 저장 (선택)")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    args = parser.parse_args()

    import torch

    if not Path(args.weights).exists():
        print(f"[eval_vision] {args.weights} 부재. train_vision.py 먼저 실행하세요.", file=sys.stderr)
        return 2

    ckpt = torch.load(args.weights, map_location="cpu")
    classes = ckpt.get("classes") or []
    region = ckpt.get("region", "?")

    loader, val_classes = _build_loader(
        Path(args.data_dir), args.batch_size, args.num_workers
    )
    if val_classes != classes:
        print(
            f"[eval_vision] classes mismatch: weights={classes} val={val_classes}",
            file=sys.stderr,
        )

    device = torch.device(
        "cuda" if torch.cuda.is_available() and args.device != "cpu" else "cpu"
    )
    model = _build_model(num_classes=len(classes)).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    n = len(classes)
    confusion = [[0] * n for _ in range(n)]
    correct, total = 0, 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            preds = model(x).argmax(dim=1)
            for t, p in zip(y.tolist(), preds.tolist(), strict=False):
                confusion[t][p] += 1
            correct += int((preds == y).sum().item())
            total += y.size(0)

    top1 = correct / max(total, 1)
    md = _format_markdown(classes, confusion, top1, region)
    print(md)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"[eval_vision] saved → {out}")
    return 0 if top1 >= 0.70 else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""W3-v2 D2 (Track A) — MobileNetV3-Small 의 4부위 분류 fine-tune.

전제:
- `scripts/datasets/skin_download.sh` 실행 후 train/val 폴더 존재
- 클래스 라벨은 `apps/api/seeds/disease_labels.json` 의 region 별 label 과 일치
  (폴더명 = label 문자열). 데이터셋 슬러그가 다른 경우 raw → label rename 필요.

실행:
    python scripts/train_vision.py \\
        --region skin \\
        --data-dir data/skin \\
        --out models/vision/skin.pt \\
        --epochs 3 --batch-size 32 --lr 1e-4

GPU 미가용 시 자동 CPU fallback. 1-3 epoch 권장 (small dataset).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Heavy 의존성은 main 진입 후 import (CLI --help 빠르게 응답).


_REGIONS = ("skin", "eye", "ear", "gum")


def _load_labels(region: str) -> list[str]:
    seeds = (
        Path(__file__).resolve().parents[3]
        / "apps"
        / "api"
        / "seeds"
        / "disease_labels.json"
    )
    with seeds.open() as f:
        catalog = json.load(f)
    return [r["label"] for r in catalog["regions"][region]]


def _build_model(num_classes: int) -> Any:
    from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small

    model = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.IMAGENET1K_V1)
    # 마지막 head 의 출력 차원을 num_classes 로 교체.
    in_features = model.classifier[-1].in_features
    import torch.nn as nn

    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


def _build_loaders(
    data_dir: Path, batch_size: int, num_workers: int
) -> tuple[Any, Any, list[str]]:
    from torch.utils.data import DataLoader
    from torchvision import transforms
    from torchvision.datasets import ImageFolder

    # MobileNetV3 expects 224x224 + ImageNet normalize.
    train_tf = transforms.Compose(
        [
            transforms.Resize((232, 232)),
            transforms.RandomCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(0.2, 0.2, 0.2, 0.05),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    val_tf = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    train_ds = ImageFolder(str(data_dir / "train"), transform=train_tf)
    val_ds = ImageFolder(str(data_dir / "val"), transform=val_tf)
    classes = list(train_ds.classes)
    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers
    )
    return train_loader, val_loader, classes


def _run_train(args: argparse.Namespace) -> int:
    import torch
    from tqdm.auto import tqdm

    device = torch.device(
        "cuda" if torch.cuda.is_available() and args.device != "cpu" else "cpu"
    )
    print(f"[train_vision] device={device}")

    data_dir = Path(args.data_dir)
    if not (data_dir / "train").exists() or not (data_dir / "val").exists():
        print(
            f"[train_vision] {data_dir}/train 또는 val 폴더 부재. "
            "scripts/datasets/skin_download.sh 먼저 실행하세요.",
            file=sys.stderr,
        )
        return 2

    expected = _load_labels(args.region)
    train_loader, val_loader, classes = _build_loaders(
        data_dir, args.batch_size, args.num_workers
    )
    print(f"[train_vision] classes={classes} ({len(classes)})")
    if set(classes) != set(expected):
        print(
            f"[train_vision] WARNING — 데이터 폴더 라벨 {classes} 가 "
            f"disease_labels.json {expected} 와 다릅니다. raw 폴더를 rename 하세요.",
            file=sys.stderr,
        )

    model = _build_model(num_classes=len(classes)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    criterion = torch.nn.CrossEntropyLoss()

    best_acc = 0.0
    for epoch in range(args.epochs):
        model.train()
        running = 0.0
        for x, y in tqdm(train_loader, desc=f"epoch {epoch + 1}/{args.epochs}"):
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            running += loss.item() * x.size(0)

        # Eval
        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                preds = model(x).argmax(dim=1)
                correct += int((preds == y).sum().item())
                total += y.size(0)
        acc = correct / max(total, 1)
        print(
            f"[train_vision] epoch={epoch + 1} train_loss={running / len(train_loader.dataset):.4f} "
            f"val_acc={acc:.4f}"
        )

        if acc > best_acc:
            best_acc = acc
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            torch.save(
                {"model_state_dict": model.state_dict(), "classes": classes, "region": args.region},
                out,
            )
            print(f"[train_vision] saved → {out} (val_acc={acc:.4f})")

    print(f"[train_vision] done. best_val_acc={best_acc:.4f}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="MobileNetV3-Small 4부위 분류 fine-tune")
    parser.add_argument("--region", choices=_REGIONS, default="skin")
    parser.add_argument("--data-dir", required=True, help="train/val 분할 데이터 폴더")
    parser.add_argument("--out", required=True, help="가중치 저장 경로 (.pt)")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    args = parser.parse_args()
    return _run_train(args)


if __name__ == "__main__":
    raise SystemExit(main())

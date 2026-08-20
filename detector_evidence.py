#!/usr/bin/env python3
"""Train/predict a YOLO evidence model without exposing test annotations.

The detector is trained only from train-split tiles. Its test predictions can
be passed to ``ornascout_pipeline_v2.py evaluate --detector-evidence``.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from pathlib import Path


def count_bin(n: int) -> str:
    return "0" if n == 0 else "1-5" if n <= 5 else "6-15" if n <= 15 else "16-30" if n <= 30 else ">30"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def safe_link(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        return
    os.symlink(source, target)


def resolve_device(requested: str) -> str:
    import torch

    device = "mps" if requested == "auto" and torch.backends.mps.is_available() else requested
    if device == "auto":
        device = "cpu"
    if device == "mps" and not torch.backends.mps.is_available():
        raise SystemExit(
            "MPS was requested but torch.backends.mps.is_available() is False. "
            "Run the environment check documented in README.md before continuing."
        )
    return device


def export_dataset(args: argparse.Namespace) -> None:
    records = read_csv(args.tile_index)
    for record in records:
        split = record["split"]
        safe_link(Path(record["tile_path"]), args.out_dir / "images" / split / Path(record["tile_path"]).name)
        safe_link(Path(record["label_path"]), args.out_dir / "labels" / split / Path(record["label_path"]).name)
    yaml_text = (
        f"path: {args.out_dir.resolve()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n"
        "names:\n"
        "  0: ornamental_plant\n"
    )
    (args.out_dir / "data.yaml").write_text(yaml_text, encoding="utf-8")


def train(args: argparse.Namespace) -> None:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Install ultralytics before detector training") from exc

    device = resolve_device(args.device)
    cache: bool | str = False if args.cache == "false" else args.cache
    model = YOLO(args.weights)
    print(
        f"Detector training: device={device}, imgsz={args.image_size}, "
        f"batch={args.batch}, epochs={args.epochs}, workers={args.workers}, cache={cache}"
    )
    model.train(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.image_size,
        batch=args.batch,
        device=device,
        workers=args.workers,
        cache=cache,
        patience=args.patience,
        project=str(args.project),
        name=args.name,
        seed=args.seed,
        deterministic=True,
    )


def predict(args: argparse.Namespace) -> None:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Install ultralytics before detector inference") from exc
    items = [json.loads(x) for x in args.manifest.read_text().splitlines() if x.strip()]
    items = [x for x in items if args.split == "all" or x["split"] == args.split]
    device = resolve_device(args.device)
    model = YOLO(str(args.weights))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for item in items:
            started = time.perf_counter()
            result = model.predict(
                item["image_path"], imgsz=args.image_size, conf=args.confidence,
                device=device, verbose=False,
            )[0]
            latency_ms = (time.perf_counter() - started) * 1000
            n = len(result.boxes) if result.boxes is not None else 0
            mean_confidence = float(result.boxes.conf.mean().item()) if n else 0.0
            handle.write(json.dumps({
                "tile_id": item["tile_id"],
                "plant_presence": "yes" if n else "no",
                "count_bin": count_bin(n),
                "detector_count": n,
                "detector_confidence": mean_confidence,
                "latency_ms": latency_ms,
            }) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export")
    export.add_argument("--tile-index", type=Path, required=True)
    export.add_argument("--out-dir", type=Path, required=True)
    export.set_defaults(func=export_dataset)
    training = sub.add_parser("train")
    training.add_argument("--data", type=Path, required=True)
    training.add_argument("--weights", default="yolo11n.pt")
    training.add_argument("--epochs", type=int, default=100)
    training.add_argument("--image-size", type=int, default=1024)
    training.add_argument("--batch", type=int, default=8)
    training.add_argument("--device", choices=["auto", "cpu", "mps"], default="auto")
    training.add_argument("--workers", type=int, default=2)
    training.add_argument("--cache", choices=["false", "disk", "ram"], default="false")
    training.add_argument("--patience", type=int, default=20)
    training.add_argument("--project", type=Path, required=True)
    training.add_argument("--name", default="ornamental_detector")
    training.add_argument("--seed", type=int, default=2026)
    training.set_defaults(func=train)
    prediction = sub.add_parser("predict")
    prediction.add_argument("--manifest", type=Path, required=True)
    prediction.add_argument("--weights", type=Path, required=True)
    prediction.add_argument("--out", type=Path, required=True)
    prediction.add_argument("--split", choices=["train", "val", "test", "all"], default="test")
    prediction.add_argument("--image-size", type=int, default=1024)
    prediction.add_argument("--confidence", type=float, default=0.25)
    prediction.add_argument("--device", choices=["auto", "cpu", "mps"], default="auto")
    prediction.set_defaults(func=predict)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

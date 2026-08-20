#!/usr/bin/env python3
"""Create a publication-grade, evidence-preserving detector figure.

One held-out tile per crop is selected deterministically by proximity to the
crop's median non-empty ground-truth count. Selection never uses predictions.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.patches import Patch, Rectangle
from ultralytics import YOLO


COLORS = {
    "gt": "#0072B2",
    "tp": "#009E73",
    "fp": "#E69F00",
    "fn": "#CC79A7",
}


@dataclass
class Detection:
    box: np.ndarray
    confidence: float


def read_yolo_labels(path: Path, width: int, height: int) -> list[np.ndarray]:
    boxes: list[np.ndarray] = []
    if not path.exists():
        return boxes
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) < 5:
            continue
        _, cx, cy, bw, bh = map(float, fields[:5])
        boxes.append(np.array([
            (cx - bw / 2) * width,
            (cy - bh / 2) * height,
            (cx + bw / 2) * width,
            (cy + bh / 2) * height,
        ]))
    return boxes


def count_labels(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if len(line.split()) >= 5)


def choose_representative(images: Path, labels: Path, crop: str) -> Path:
    candidates = [
        path for path in sorted(images.glob(f"{crop}_*.jpg"))
        if not path.name.startswith("._") and count_labels(labels / f"{path.stem}.txt") > 0
    ]
    if not candidates:
        raise RuntimeError(f"No labeled validation tiles found for {crop}")
    counts = np.array([count_labels(labels / f"{path.stem}.txt") for path in candidates])
    median = float(np.median(counts))
    index = min(range(len(candidates)), key=lambda i: (abs(counts[i] - median), candidates[i].name))
    return candidates[index]


def iou(a: np.ndarray, b: np.ndarray) -> float:
    left, top = np.maximum(a[:2], b[:2])
    right, bottom = np.minimum(a[2:], b[2:])
    inter = max(0.0, right - left) * max(0.0, bottom - top)
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    return inter / max(area_a + area_b - inter, 1e-9)


def greedy_match(gt: list[np.ndarray], pred: list[Detection], threshold: float) -> tuple[set[int], set[int]]:
    pairs = sorted(
        ((iou(g, p.box), gi, pi) for gi, g in enumerate(gt) for pi, p in enumerate(pred)),
        reverse=True,
    )
    matched_gt: set[int] = set()
    matched_pred: set[int] = set()
    for overlap, gi, pi in pairs:
        if overlap < threshold:
            break
        if gi not in matched_gt and pi not in matched_pred:
            matched_gt.add(gi)
            matched_pred.add(pi)
    return matched_gt, matched_pred


def draw_boxes(ax: plt.Axes, boxes: list[np.ndarray], color: str, linewidth: float = 1.5) -> None:
    for x1, y1, x2, y2 in boxes:
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False,
                               edgecolor=color, linewidth=linewidth))


def confidence_field(height: int, width: int, predictions: list[Detection]) -> np.ndarray:
    field = np.zeros((height, width), dtype=np.float32)
    yy, xx = np.mgrid[0:height, 0:width]
    for prediction in predictions:
        x1, y1, x2, y2 = prediction.box
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        sx = max((x2 - x1) / 2, 8.0)
        sy = max((y2 - y1) / 2, 8.0)
        response = prediction.confidence * np.exp(
            -0.5 * (((xx - cx) / sx) ** 2 + ((yy - cy) / sy) ** 2)
        )
        field = np.maximum(field, response.astype(np.float32))
    return field


def show_image(ax: plt.Axes, image: np.ndarray) -> None:
    ax.imshow(image)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_linewidth(0.7)
        spine.set_color("#333333")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--split", default="val", choices=["val", "test"])
    parser.add_argument("--image-size", type=int, default=640)
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.5)
    parser.add_argument("--device", default="mps")
    args = parser.parse_args()

    images = args.data / "images" / args.split
    labels = args.data / "labels" / args.split
    selected = {crop: choose_representative(images, labels, crop) for crop in ("magnolia", "azalea")}
    model = YOLO(str(args.weights))

    plt.rcParams.update({
        "font.family": "Arial",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    fig, axes = plt.subplots(2, 5, figsize=(15.8, 6.8), constrained_layout=True)
    column_titles = [
        "UAV RGB tile", "Provided annotations", "Detector predictions",
        f"IoU matching ($\\tau={args.iou:.1f}$)", "Spatial confidence field",
    ]

    mappable = None
    for row, crop in enumerate(("magnolia", "azalea")):
        image_path = selected[crop]
        bgr = cv2.imread(str(image_path))
        if bgr is None:
            raise RuntimeError(f"Cannot read {image_path}")
        image = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        height, width = image.shape[:2]
        gt = read_yolo_labels(labels / f"{image_path.stem}.txt", width, height)
        result = model.predict(str(image_path), imgsz=args.image_size, conf=args.confidence,
                               device=args.device, verbose=False)[0]
        predictions: list[Detection] = []
        if result.boxes is not None:
            xyxy = result.boxes.xyxy.detach().cpu().numpy()
            confidence = result.boxes.conf.detach().cpu().numpy()
            predictions = [Detection(box, float(score)) for box, score in zip(xyxy, confidence)]
        matched_gt, matched_pred = greedy_match(gt, predictions, args.iou)

        for col in range(5):
            show_image(axes[row, col], image)
            if row == 0:
                axes[row, col].set_title(column_titles[col], pad=7)
        axes[row, 0].set_ylabel(crop.capitalize(), fontsize=11, fontweight="bold", labelpad=8)
        draw_boxes(axes[row, 1], gt, COLORS["gt"])

        norm = Normalize(vmin=0.25, vmax=1.0)
        cmap = plt.get_cmap("viridis")
        for prediction in predictions:
            draw_boxes(axes[row, 2], [prediction.box], cmap(norm(prediction.confidence)))

        draw_boxes(axes[row, 3], [predictions[i].box for i in matched_pred], COLORS["tp"])
        draw_boxes(axes[row, 3], [p.box for i, p in enumerate(predictions) if i not in matched_pred], COLORS["fp"])
        draw_boxes(axes[row, 3], [g for i, g in enumerate(gt) if i not in matched_gt], COLORS["fn"])

        field = confidence_field(height, width, predictions)
        axes[row, 4].images[-1].set_alpha(0.35)
        mappable = axes[row, 4].imshow(field, cmap="magma", vmin=0.0, vmax=1.0, alpha=0.75)

        summary = f"GT {len(gt)} | Pred. {len(predictions)} | TP {len(matched_pred)}"
        axes[row, 3].text(0.02, 0.03, summary, transform=axes[row, 3].transAxes,
                          fontsize=8, color="black",
                          bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.88, "pad": 2})

    legend = [
        Patch(facecolor="none", edgecolor=COLORS["gt"], label="Provided annotation"),
        Patch(facecolor="none", edgecolor=COLORS["tp"], label="Matched prediction"),
        Patch(facecolor="none", edgecolor=COLORS["fp"], label="Unmatched prediction"),
        Patch(facecolor="none", edgecolor=COLORS["fn"], label="Unmatched annotation"),
    ]
    fig.legend(handles=legend, loc="lower center", ncol=4, frameon=False,
               bbox_to_anchor=(0.46, -0.01), fontsize=9)
    if mappable is not None:
        colorbar = fig.colorbar(mappable, ax=axes[:, 4], fraction=0.028, pad=0.018)
        colorbar.set_label("Detector confidence", fontsize=9)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.out_dir / f"detector_qualitative_{args.split}"
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {stem.with_suffix('.png')}")
    print(f"Saved: {stem.with_suffix('.pdf')}")
    for crop, path in selected.items():
        print(f"{crop}: {path.name} (selection: nearest non-empty GT median)")


if __name__ == "__main__":
    main()

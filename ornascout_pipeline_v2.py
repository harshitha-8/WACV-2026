#!/usr/bin/env python3
"""OrnaScout-VLM: leakage-safe data, evaluation, and cross-crop pipeline.

The script converts high-resolution RGB nursery images and YOLO labels into a
source-image-grouped WACV-style benchmark. Ground truth is never written into
the inference manifest. Model runners read only images and prompts; evaluation
joins predictions to a separate ground-truth file.

Subcommands:
  prepare       Validate, tile, split, and write inference/ground-truth files.
  merge-crops   Merge independently prepared Magnolia and Azalea datasets.
  evaluate      Score one or more model prediction JSONL files.
  cross-crop    Summarize train/test crop transfer protocols.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from PIL import Image


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
COUNT_BINS = ["0", "1-5", "6-15", "16-30", ">30"]
DENSITY_CLASSES = ["empty", "sparse", "moderate", "dense"]
COVERAGE_CLASSES = ["none", "low", "medium", "high"]
PRIORITY_CLASSES = ["low", "medium", "high"]
YES_NO = ["yes", "no"]
ANNOTATION_ISSUES: list[dict[str, Any]] = []


@dataclass(frozen=True)
class YoloBox:
    class_id: int
    cx: float
    cy: float
    w: float
    h: float

    def xyxy(self, width: int, height: int) -> tuple[float, float, float, float]:
        bw, bh = self.w * width, self.h * height
        return (
            self.cx * width - bw / 2,
            self.cy * height - bh / 2,
            self.cx * width + bw / 2,
            self.cy * height + bh / 2,
        )


@dataclass(frozen=True)
class ImageRecord:
    image_id: str
    crop: str
    image_path: str
    label_path: str
    width: int
    height: int
    n_boxes: int
    split: str


@dataclass(frozen=True)
class TileRecord:
    tile_id: str
    image_id: str
    crop: str
    split: str
    tile_path: str
    label_path: str
    source_image_path: str
    x0: int
    y0: int
    width: int
    height: int
    n_boxes: int
    box_coverage: float
    plant_presence: str
    count_bin: str
    density_class: str
    coverage_class: str
    is_boundary_tile: int
    is_hard_negative: int


def is_resource_fork(path: Path) -> bool:
    return path.name.startswith("._") or path.name == ".DS_Store"


def is_original_image(path: Path) -> bool:
    return (
        path.is_file()
        and not is_resource_fork(path)
        and path.suffix.lower() in IMAGE_EXTS
        and "_annotated" not in path.stem.lower()
    )


def crop_name(root: Path, override: str | None) -> str:
    if override:
        return override.strip().lower()
    class_file = root / "classes.txt"
    if class_file.exists():
        names = [x.strip() for x in class_file.read_text(errors="ignore").splitlines() if x.strip()]
        if names:
            return names[0].lower()
    return root.name.lower()


def read_yolo(path: Path) -> list[YoloBox]:
    boxes: list[YoloBox] = []
    for line_no, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 5:
            raise ValueError(f"{path}:{line_no}: expected five YOLO columns")
        class_id = int(float(parts[0]))
        cx, cy, w, h = (float(v) for v in parts[1:])
        if not all(0.0 <= v <= 1.0 for v in (cx, cy, w, h)):
            raise ValueError(f"{path}:{line_no}: invalid normalized box")
        if w <= 0 or h <= 0:
            ANNOTATION_ISSUES.append({
                "label_path": str(path),
                "line_no": line_no,
                "issue": "zero_area_box_rejected",
                "raw_line": line,
            })
            continue
        boxes.append(YoloBox(class_id, cx, cy, w, h))
    return boxes


def image_label_pairs(image_root: Path, label_root: Path) -> Iterable[tuple[Path, Path]]:
    images_by_stem = {
        image.stem: image
        for image in sorted(image_root.rglob("*"))
        if is_original_image(image)
    }
    labels_by_stem = {
        label.stem: label
        for label in sorted(label_root.rglob("*.txt"))
        if not is_resource_fork(label) and label.name != "classes.txt"
    }
    for stem in sorted(images_by_stem.keys() & labels_by_stem.keys()):
        yield images_by_stem[stem], labels_by_stem[stem]


def stable_fraction(value: str, seed: int) -> float:
    digest = hashlib.sha256(f"{seed}:{value}".encode()).hexdigest()
    return int(digest[:12], 16) / float(16**12 - 1)


def assign_split(image_id: str, seed: int, train: float, val: float) -> str:
    value = stable_fraction(image_id, seed)
    if value < train:
        return "train"
    if value < train + val:
        return "val"
    return "test"


def index_images(
    image_root: Path,
    label_root: Path,
    crop: str | None,
    seed: int,
    train_ratio: float,
    val_ratio: float,
) -> list[ImageRecord]:
    name = crop_name(label_root, crop)
    records: list[ImageRecord] = []
    for image, label in image_label_pairs(image_root, label_root):
        with Image.open(image) as img:
            width, height = img.size
        boxes = read_yolo(label)
        records.append(
            ImageRecord(
                image_id=f"{name}_{image.stem}",
                crop=name,
                image_path=str(image),
                label_path=str(label),
                width=width,
                height=height,
                n_boxes=len(boxes),
                split=assign_split(f"{name}_{image.stem}", seed, train_ratio, val_ratio),
            )
        )
    return records


def area(box: Sequence[float]) -> float:
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def intersection(
    box: Sequence[float], tile: Sequence[int]
) -> tuple[float, float, float, float] | None:
    bx1, by1, bx2, by2 = box
    tx1, ty1, tx2, ty2 = tile
    clipped = max(bx1, tx1), max(by1, ty1), min(bx2, tx2), min(by2, ty2)
    if clipped[2] <= clipped[0] or clipped[3] <= clipped[1]:
        return None
    return clipped


def grid(width: int, height: int, tile_size: int, overlap: float) -> list[tuple[int, int, int, int]]:
    if not 0 <= overlap < 1:
        raise ValueError("overlap must be in [0, 1)")
    stride = max(1, round(tile_size * (1 - overlap)))

    def starts(length: int) -> list[int]:
        edge = max(0, length - tile_size)
        values = list(range(0, edge + 1, stride)) or [0]
        if values[-1] != edge:
            values.append(edge)
        return values

    return [
        (x, y, min(x + tile_size, width), min(y + tile_size, height))
        for y in starts(height)
        for x in starts(width)
    ]


def count_bin(n: int) -> str:
    return "0" if n == 0 else "1-5" if n <= 5 else "6-15" if n <= 15 else "16-30" if n <= 30 else ">30"


def density(n: int) -> str:
    return "empty" if n == 0 else "sparse" if n <= 5 else "moderate" if n <= 20 else "dense"


def coverage(value: float) -> str:
    return "none" if value == 0 else "low" if value < 0.03 else "medium" if value < 0.12 else "high"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def prompt_text() -> str:
    return (
        "Inspect this UAV RGB tile from an ornamental nursery. Return one JSON object only. "
        "Use keys crop_type, plant_presence, count_bin, density_class, coverage_class, "
        "visual_evidence, scouting_priority, confidence, and human_review_needed. "
        "crop_type is magnolia, azalea, or unknown; plant_presence and human_review_needed are yes/no; "
        f"count_bin is one of {COUNT_BINS}; density_class is one of {DENSITY_CLASSES}; "
        f"coverage_class is one of {COVERAGE_CLASSES}; scouting_priority is one of {PRIORITY_CLASSES}; "
        "confidence is a number from 0 to 1. Describe only visible evidence. Use unknown or request "
        "human review when the evidence is insufficient."
    )


def tile_images(
    images: list[ImageRecord],
    out_dir: Path,
    tile_size: int,
    overlap: float,
    min_visible_fraction: float,
) -> list[TileRecord]:
    tiles_dir = out_dir / "tiles"
    labels_dir = out_dir / "tile_labels_yolo"
    tiles_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    records: list[TileRecord] = []

    for image_rec in images:
        boxes = read_yolo(Path(image_rec.label_path))
        boxes_px = [box.xyxy(image_rec.width, image_rec.height) for box in boxes]
        with Image.open(image_rec.image_path) as source:
            source = source.convert("RGB")
            for index, tile in enumerate(grid(image_rec.width, image_rec.height, tile_size, overlap)):
                x1, y1, x2, y2 = tile
                tile_w, tile_h = x2 - x1, y2 - y1
                kept: list[tuple[float, float, float, float]] = []
                boundary = 0
                for box in boxes_px:
                    overlap_box = intersection(box, tile)
                    if overlap_box is None:
                        continue
                    visible = area(overlap_box) / max(area(box), 1e-12)
                    if visible < min_visible_fraction:
                        boundary = 1
                        continue
                    if visible < 0.98:
                        boundary = 1
                    kept.append((
                        overlap_box[0] - x1,
                        overlap_box[1] - y1,
                        overlap_box[2] - x1,
                        overlap_box[3] - y1,
                    ))

                tile_id = f"{image_rec.image_id}_t{index:04d}"
                tile_path = tiles_dir / f"{tile_id}.jpg"
                label_path = labels_dir / f"{tile_id}.txt"
                source.crop(tile).save(tile_path, quality=95, subsampling=0)
                lines: list[str] = []
                occupied = 0.0
                for bx1, by1, bx2, by2 in kept:
                    bw, bh = bx2 - bx1, by2 - by1
                    occupied += bw * bh
                    lines.append(
                        f"0 {((bx1 + bx2) / 2 / tile_w):.6f} {((by1 + by2) / 2 / tile_h):.6f} "
                        f"{(bw / tile_w):.6f} {(bh / tile_h):.6f}"
                    )
                label_path.write_text("\n".join(lines), encoding="utf-8")
                n = len(kept)
                cov = min(1.0, occupied / max(tile_w * tile_h, 1))
                hard_negative = int(n == 0 and (boundary == 1 or image_rec.n_boxes > 0))
                records.append(
                    TileRecord(
                        tile_id=tile_id,
                        image_id=image_rec.image_id,
                        crop=image_rec.crop,
                        split=image_rec.split,
                        tile_path=str(tile_path),
                        label_path=str(label_path),
                        source_image_path=image_rec.image_path,
                        x0=x1,
                        y0=y1,
                        width=tile_w,
                        height=tile_h,
                        n_boxes=n,
                        box_coverage=cov,
                        plant_presence="yes" if n else "no",
                        count_bin=count_bin(n),
                        density_class=density(n),
                        coverage_class=coverage(cov),
                        is_boundary_tile=boundary,
                        is_hard_negative=hard_negative,
                    )
                )
    return records


def prepare(args: argparse.Namespace) -> None:
    ANNOTATION_ISSUES.clear()
    image_root = args.images_root or args.root
    label_root = args.labels_root or args.root
    if image_root is None or label_root is None:
        raise SystemExit("Provide --root, or both --images-root and --labels-root")
    images = index_images(image_root, label_root, args.crop, args.seed, args.train_ratio, args.val_ratio)
    tiles = tile_images(images, args.out_dir, args.tile_size, args.overlap, args.min_visible_fraction)
    unique_issues = list({
        (row["label_path"], row["line_no"], row["issue"]): row
        for row in ANNOTATION_ISSUES
    }.values())
    write_csv(args.out_dir / "image_index.csv", [asdict(x) for x in images])
    write_csv(args.out_dir / "tile_index.csv", [asdict(x) for x in tiles])
    write_csv(args.out_dir / "annotation_issues.csv", unique_issues)
    write_jsonl(
        args.out_dir / "inference_manifest.jsonl",
        ({"tile_id": x.tile_id, "image_path": x.tile_path, "crop": x.crop, "split": x.split, "prompt": prompt_text()} for x in tiles),
    )
    write_jsonl(
        args.out_dir / "ground_truth.jsonl",
        (
            {
                "tile_id": x.tile_id,
                "image_id": x.image_id,
                "crop_type": x.crop,
                "split": x.split,
                "tile_path": x.tile_path,
                "plant_presence": x.plant_presence,
                "count_bin": x.count_bin,
                "density_class": x.density_class,
                "coverage_class": x.coverage_class,
                "n_boxes": x.n_boxes,
                "box_coverage": x.box_coverage,
                "is_boundary_tile": x.is_boundary_tile,
                "is_hard_negative": x.is_hard_negative,
            }
            for x in tiles
        ),
    )
    write_jsonl(
        args.out_dir / "sft_train.jsonl",
        (
            {
                "tile_id": x.tile_id,
                "image_path": x.tile_path,
                "crop": x.crop,
                "prompt": prompt_text(),
                "target": {
                    "crop_type": x.crop,
                    "plant_presence": x.plant_presence,
                    "count_bin": x.count_bin,
                    "density_class": x.density_class,
                    "coverage_class": x.coverage_class,
                    "visual_evidence": "annotation-derived training target",
                    "scouting_priority": "high" if x.is_hard_negative or x.is_boundary_tile else "medium",
                    "confidence": 1.0,
                    "human_review_needed": "yes" if x.is_hard_negative or x.is_boundary_tile else "no",
                },
            }
            for x in tiles
            if x.split == "train"
        ),
    )
    summary = {
        "crop": crop_name(label_root, args.crop),
        "image_root": str(image_root),
        "label_root": str(label_root),
        "source_images": len(images),
        "tiles": len(tiles),
        "boxes": sum(x.n_boxes for x in images),
        "splits_by_source_image": Counter(x.split for x in images),
        "tiles_by_split": Counter(x.split for x in tiles),
        "count_bins": Counter(x.count_bin for x in tiles),
        "hard_negatives": sum(x.is_hard_negative for x in tiles),
        "rejected_annotation_boxes": len(unique_issues),
        "seed": args.seed,
        "tile_size": args.tile_size,
        "overlap": args.overlap,
    }
    (args.out_dir / "dataset_summary.json").write_text(json.dumps(summary, indent=2, default=dict))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def merge_crops(args: argparse.Namespace) -> None:
    manifests: list[dict[str, Any]] = []
    truths: list[dict[str, Any]] = []
    sft_rows: list[dict[str, Any]] = []
    tile_rows: list[dict[str, Any]] = []
    image_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for folder in args.inputs:
        for row in read_jsonl(folder / "inference_manifest.jsonl"):
            if row["tile_id"] in seen:
                raise ValueError(f"duplicate tile_id: {row['tile_id']}")
            seen.add(row["tile_id"])
            manifests.append(row)
        truths.extend(read_jsonl(folder / "ground_truth.jsonl"))
        sft_rows.extend(read_jsonl(folder / "sft_train.jsonl"))
        for filename, target in [("tile_index.csv", tile_rows), ("image_index.csv", image_rows)]:
            with (folder / filename).open(newline="", encoding="utf-8") as handle:
                target.extend(csv.DictReader(handle))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "inference_manifest.jsonl", manifests)
    write_jsonl(args.out_dir / "ground_truth.jsonl", truths)
    write_jsonl(args.out_dir / "sft_train.jsonl", sft_rows)
    write_csv(args.out_dir / "tile_index.csv", tile_rows)
    write_csv(args.out_dir / "image_index.csv", image_rows)
    (args.out_dir / "merge_summary.json").write_text(
        json.dumps({"tiles": len(manifests), "crops": dict(Counter(x["crop"] for x in manifests))}, indent=2)
    )


def parse_json(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def normalized_prediction(pred: dict[str, Any] | None) -> dict[str, Any]:
    if pred is None:
        return {}
    out = {str(k): v for k, v in pred.items()}
    for key in ["crop_type", "plant_presence", "count_bin", "density_class", "coverage_class", "scouting_priority", "human_review_needed"]:
        if key in out:
            out[key] = str(out[key]).strip().lower()
    try:
        out["confidence"] = float(out.get("confidence", 0.0))
    except (TypeError, ValueError):
        out["confidence"] = 0.0
    return out


def schema_score(pred: dict[str, Any]) -> float:
    checks = [
        pred.get("crop_type") in {"magnolia", "azalea", "unknown"},
        pred.get("plant_presence") in YES_NO,
        pred.get("count_bin") in COUNT_BINS,
        pred.get("density_class") in DENSITY_CLASSES,
        pred.get("coverage_class") in COVERAGE_CLASSES,
        pred.get("scouting_priority") in PRIORITY_CLASSES,
        pred.get("human_review_needed") in YES_NO,
        isinstance(pred.get("visual_evidence"), str) and bool(pred.get("visual_evidence", "").strip()),
        0.0 <= pred.get("confidence", -1.0) <= 1.0,
    ]
    return sum(checks) / len(checks)


def consistency_score(predictions: list[dict[str, Any]]) -> float:
    if len(predictions) <= 1:
        return 1.0
    keys = ["crop_type", "plant_presence", "count_bin", "density_class", "coverage_class"]
    agreements = []
    for key in keys:
        counts = Counter(str(x.get(key, "")) for x in predictions)
        agreements.append(max(counts.values()) / len(predictions))
    return statistics.mean(agreements)


def detector_agreement(pred: dict[str, Any], evidence: dict[str, Any] | None) -> float | None:
    if evidence is None:
        return None
    values: list[float] = []
    if "plant_presence" in evidence:
        values.append(float(pred.get("plant_presence") == str(evidence["plant_presence"]).lower()))
    if "count_bin" in evidence:
        values.append(float(pred.get("count_bin") == str(evidence["count_bin"]).lower()))
    return statistics.mean(values) if values else None


def gate_prediction(
    repeats: list[dict[str, Any]],
    evidence: dict[str, Any] | None,
    accept_threshold: float,
    abstain_threshold: float,
) -> dict[str, Any]:
    pred = repeats[0] if repeats else {}
    schema = schema_score(pred)
    consistency = consistency_score(repeats)
    confidence = max(0.0, min(1.0, float(pred.get("confidence", 0.0))))
    agreement = detector_agreement(pred, evidence)
    components = [(schema, 0.35), (consistency, 0.25), (confidence, 0.20)]
    if agreement is not None:
        components.append((agreement, 0.20))
    else:
        components = [(v, w / 0.80) for v, w in components]
    score = sum(value * weight for value, weight in components)
    decision = "accept" if score >= accept_threshold else "abstain" if score >= abstain_threshold else "escalate"
    return {
        "gate_score": round(score, 6),
        "gate_decision": decision,
        "schema_score": round(schema, 6),
        "consistency_score": round(consistency, 6),
        "detector_agreement": "" if agreement is None else round(agreement, 6),
    }


def macro_f1(rows: list[dict[str, Any]], key: str, labels: list[str]) -> float:
    scores: list[float] = []
    for label in labels:
        tp = sum(r[f"{key}_gt"] == label and r[f"{key}_pred"] == label for r in rows)
        fp = sum(r[f"{key}_gt"] != label and r[f"{key}_pred"] == label for r in rows)
        fn = sum(r[f"{key}_gt"] == label and r[f"{key}_pred"] != label for r in rows)
        denominator = 2 * tp + fp + fn
        scores.append(2 * tp / denominator if denominator else 0.0)
    return statistics.mean(scores) if scores else math.nan


def bootstrap_interval(
    rows: list[dict[str, Any]],
    metric,
    repeats: int,
    seed: int,
) -> tuple[float, float]:
    """Cluster bootstrap over source images, preserving within-image tiles."""
    by_image: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_image[row["image_id"]].append(row)
    image_ids = sorted(by_image)
    if not image_ids or repeats <= 0:
        return math.nan, math.nan
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(repeats):
        sample: list[dict[str, Any]] = []
        for image_id in (rng.choice(image_ids) for _ in image_ids):
            sample.extend(by_image[image_id])
        values.append(float(metric(sample)))
    values.sort()
    low = values[max(0, math.floor(0.025 * (len(values) - 1)))]
    high = values[min(len(values) - 1, math.ceil(0.975 * (len(values) - 1)))]
    return low, high


def evaluate(args: argparse.Namespace) -> None:
    truth = {x["tile_id"]: x for x in read_jsonl(args.ground_truth)}
    evidence = {x["tile_id"]: x for x in read_jsonl(args.detector_evidence)} if args.detector_evidence else {}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    metadata: dict[tuple[str, str], dict[str, Any]] = {}
    for prediction_file in args.predictions:
        for raw in read_jsonl(prediction_file):
            tile_id = raw["tile_id"]
            model = raw.get("model", prediction_file.stem)
            pred = normalized_prediction(parse_json(raw.get("prediction", raw.get("output", raw))))
            grouped[(model, tile_id)].append(pred)
            metadata[(model, tile_id)] = raw

    rows: list[dict[str, Any]] = []
    for (model, tile_id), repeats in grouped.items():
        if tile_id not in truth:
            continue
        gt = truth[tile_id]
        pred = repeats[0]
        gate = gate_prediction(repeats, evidence.get(tile_id), args.accept_threshold, args.abstain_threshold)
        row: dict[str, Any] = {
            "tile_id": tile_id,
            "image_id": gt["image_id"],
            "tile_path": gt.get("tile_path", ""),
            "model": model,
            "crop": gt["crop_type"],
            "split": gt["split"],
            "is_hard_negative": gt["is_hard_negative"],
            "latency_ms": metadata[(model, tile_id)].get("latency_ms", ""),
            "peak_memory_mb": metadata[(model, tile_id)].get("peak_memory_mb", ""),
            **gate,
        }
        for key in ["crop_type", "plant_presence", "count_bin", "density_class", "coverage_class"]:
            row[f"{key}_gt"] = gt[key]
            row[f"{key}_pred"] = pred.get(key, "")
            row[f"{key}_correct"] = int(pred.get(key, "") == gt[key])
        row["hallucination"] = int(gt["plant_presence"] == "no" and pred.get("plant_presence") == "yes")
        row["accepted_correct"] = int(gate["gate_decision"] == "accept" and row["plant_presence_correct"] == 1)
        row["false_accept"] = int(gate["gate_decision"] == "accept" and row["plant_presence_correct"] == 0)
        rows.append(row)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "per_tile_evaluation.csv", rows)
    summaries: list[dict[str, Any]] = []
    for (model, crop, split), subset_iter in _group_rows(rows, ["model", "crop", "split"]):
        subset = list(subset_iter)
        hard_negatives = [x for x in subset if int(x["is_hard_negative"]) == 1]
        accepted = [x for x in subset if x["gate_decision"] == "accept"]
        latency = [float(x["latency_ms"]) for x in subset if str(x["latency_ms"]) not in {"", "nan"}]
        memory = [float(x["peak_memory_mb"]) for x in subset if str(x["peak_memory_mb"]) not in {"", "nan"}]
        presence_ci = bootstrap_interval(
            subset,
            lambda sample: macro_f1(sample, "plant_presence", YES_NO),
            args.bootstrap,
            args.seed,
        )
        count_ci = bootstrap_interval(
            subset,
            lambda sample: macro_f1(sample, "count_bin", COUNT_BINS),
            args.bootstrap,
            args.seed + 1,
        )
        summaries.append({
            "model": model,
            "crop": crop,
            "split": split,
            "n": len(subset),
            "presence_f1": macro_f1(subset, "plant_presence", YES_NO),
            "presence_f1_ci_low": presence_ci[0],
            "presence_f1_ci_high": presence_ci[1],
            "count_bin_macro_f1": macro_f1(subset, "count_bin", COUNT_BINS),
            "count_bin_f1_ci_low": count_ci[0],
            "count_bin_f1_ci_high": count_ci[1],
            "density_macro_f1": macro_f1(subset, "density_class", DENSITY_CLASSES),
            "coverage_macro_f1": macro_f1(subset, "coverage_class", COVERAGE_CLASSES),
            "schema_valid_rate": statistics.mean(float(x["schema_score"] == 1.0) for x in subset),
            "hallucination_rate_hard_negative": statistics.mean(x["hallucination"] for x in hard_negatives) if hard_negatives else math.nan,
            "accept_rate": len(accepted) / len(subset),
            "selective_accuracy": statistics.mean(x["plant_presence_correct"] for x in accepted) if accepted else math.nan,
            "false_accept_rate": statistics.mean(x["false_accept"] for x in subset),
            "escalation_rate": statistics.mean(x["gate_decision"] == "escalate" for x in subset),
            "latency_ms_mean": statistics.mean(latency) if latency else math.nan,
            "peak_memory_mb_mean": statistics.mean(memory) if memory else math.nan,
        })
    write_csv(args.out_dir / "model_summary.csv", summaries)


def _group_rows(rows: list[dict[str, Any]], keys: list[str]):
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in keys)].append(row)
    return grouped.items()


def cross_crop(args: argparse.Namespace) -> None:
    rows: list[dict[str, Any]] = []
    for evaluation in args.evaluations:
        with evaluation.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                row["protocol"] = evaluation.parent.name
                rows.append(row)
    protocols: list[dict[str, Any]] = []
    for (protocol, model, crop), subset_iter in _group_rows(rows, ["protocol", "model", "crop"]):
        subset = list(subset_iter)
        protocols.append({
            "protocol": protocol,
            "model": model,
            "test_crop": crop,
            "n": len(subset),
            "presence_f1": macro_f1(subset, "plant_presence", YES_NO),
            "count_bin_macro_f1": macro_f1(subset, "count_bin", COUNT_BINS),
            "density_macro_f1": macro_f1(subset, "density_class", DENSITY_CLASSES),
            "coverage_macro_f1": macro_f1(subset, "coverage_class", COVERAGE_CLASSES),
        })
    write_csv(args.out, protocols)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OrnaScout-VLM WACV pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prepare")
    prep.add_argument("--root", type=Path)
    prep.add_argument("--images-root", type=Path)
    prep.add_argument("--labels-root", type=Path)
    prep.add_argument("--out-dir", type=Path, required=True)
    prep.add_argument("--crop")
    prep.add_argument("--tile-size", type=int, default=1024)
    prep.add_argument("--overlap", type=float, default=0.25)
    prep.add_argument("--min-visible-fraction", type=float, default=0.50)
    prep.add_argument("--seed", type=int, default=2026)
    prep.add_argument("--train-ratio", type=float, default=0.70)
    prep.add_argument("--val-ratio", type=float, default=0.15)
    prep.set_defaults(func=prepare)

    merge = sub.add_parser("merge-crops")
    merge.add_argument("--inputs", type=Path, nargs="+", required=True)
    merge.add_argument("--out-dir", type=Path, required=True)
    merge.set_defaults(func=merge_crops)

    evaluation = sub.add_parser("evaluate")
    evaluation.add_argument("--ground-truth", type=Path, required=True)
    evaluation.add_argument("--predictions", type=Path, nargs="+", required=True)
    evaluation.add_argument("--detector-evidence", type=Path)
    evaluation.add_argument("--out-dir", type=Path, required=True)
    evaluation.add_argument("--accept-threshold", type=float, default=0.75)
    evaluation.add_argument("--abstain-threshold", type=float, default=0.55)
    evaluation.add_argument("--bootstrap", type=int, default=1000)
    evaluation.add_argument("--seed", type=int, default=2026)
    evaluation.set_defaults(func=evaluate)

    transfer = sub.add_parser("cross-crop")
    transfer.add_argument("--evaluations", type=Path, nargs="+", required=True)
    transfer.add_argument("--out", type=Path, required=True)
    transfer.set_defaults(func=cross_crop)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "train_ratio", 0) + getattr(args, "val_ratio", 0) >= 1:
        raise SystemExit("train-ratio + val-ratio must be below 1")
    args.func(args)


if __name__ == "__main__":
    main()

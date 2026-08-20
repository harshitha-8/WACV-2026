#!/usr/bin/env python3
"""Single launcher for the complete OrnaScout-VLM experiment.

Edit only ``experiment_config.json`` when a new crop arrives. The launcher
delegates scientific logic to the versioned pipeline, model runner, training,
detector, and plotting modules while preserving one reproducible entry point.

Examples:
  python run_experiment.py inspect
  python run_experiment.py prepare --crop magnolia
  python run_experiment.py prepare --crop azalea
  python run_experiment.py merge
  python run_experiment.py figures --crop magnolia
  python run_experiment.py infer --model smolvlm2_2p2b --scope magnolia --limit 10
  python run_experiment.py evaluate --scope magnolia
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE / "experiment_config.json"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    config["project_root"] = str(Path(config.get("project_root", HERE)).expanduser())
    config["output_root"] = str(Path(config["output_root"]).expanduser())
    return config


def clean_labels(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.txt")
        if path.is_file() and not path.name.startswith("._") and path.name != "classes.txt"
    )


def original_images(root: Path) -> list[Path]:
    search_root = root / "images" if (root / "images").is_dir() else root
    return sorted(
        path
        for path in search_root.rglob("*")
        if path.is_file()
        and not path.name.startswith("._")
        and path.suffix.lower() in IMAGE_EXTS
        and "_annotated" not in path.stem.lower()
    )


def inspect_crop(crop: str, image_root: Path, label_root: Path) -> dict[str, Any]:
    if not image_root.exists() or not label_root.exists():
        return {
            "crop": crop,
            "image_root": str(image_root),
            "label_root": str(label_root),
            "status": "missing",
        }
    labels = clean_labels(label_root)
    images = original_images(image_root)
    image_stems = {path.stem for path in images}
    label_stems = {path.stem for path in labels}
    resource_forks = list(label_root.rglob("._*.txt"))
    classes = list(label_root.rglob("classes.txt"))
    annotation_boxes = 0
    rejected_zero_area_rows = 0
    malformed_rows = 0
    class_ids: set[int] = set()
    for label in labels:
        for line in label.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            values = line.split()
            try:
                if len(values) != 5:
                    raise ValueError
                class_id = int(float(values[0]))
                coords = [float(value) for value in values[1:]]
                if any(value < 0 or value > 1 for value in coords):
                    raise ValueError
            except ValueError:
                malformed_rows += 1
                continue
            if coords[2] <= 0 or coords[3] <= 0:
                rejected_zero_area_rows += 1
                continue
            annotation_boxes += 1
            class_ids.add(class_id)
    all_labels_have_images = label_stems <= image_stems
    return {
        "crop": crop,
        "image_root": str(image_root),
        "label_root": str(label_root),
        "status": "ready" if labels and all_labels_have_images and malformed_rows == 0 else "incomplete",
        "clean_annotation_txt": len(labels),
        "original_rgb_images": len(images),
        "matched_image_label_pairs": len(image_stems & label_stems),
        "labels_without_image": len(label_stems - image_stems),
        "images_without_label": len(image_stems - label_stems),
        "macos_resource_fork_txt_ignored": len(resource_forks),
        "classes_txt_ignored_as_annotation": len(classes),
        "valid_annotation_boxes": annotation_boxes,
        "empty_annotation_files": sum(label.stat().st_size == 0 for label in labels),
        "rejected_zero_area_rows": rejected_zero_area_rows,
        "malformed_annotation_rows": malformed_rows,
        "class_ids": sorted(class_ids),
    }


def configured_datasets(config: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Normalize one or more independent source roots for every crop."""
    datasets: dict[str, list[dict[str, Any]]] = {}
    for raw_crop, raw_sources in config.get("datasets", {}).items():
        sources = raw_sources if isinstance(raw_sources, list) else [raw_sources]
        normalized: list[dict[str, Any]] = []
        for source in sources:
            if isinstance(source, str):
                image_root = label_root = Path(source).expanduser()
                version = image_root.name
            elif isinstance(source, dict):
                image_root = Path(source["images"]).expanduser()
                label_root = Path(source.get("labels", source["images"])).expanduser()
                version = str(source.get("version", label_root.name))
            else:
                raise TypeError(f"Unsupported dataset source for {raw_crop}: {source!r}")
            normalized.append({"images": image_root, "labels": label_root, "version": version})
        if normalized:
            datasets[raw_crop.lower()] = normalized
    return datasets


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def crop_output(config: dict[str, Any], crop: str) -> Path:
    return Path(config["output_root"]) / crop.lower()


def scope_output(config: dict[str, Any], scope: str) -> Path:
    return Path(config["output_root"]) / scope.lower()


def command_inspect(config: dict[str, Any]) -> None:
    datasets = configured_datasets(config)
    if not datasets:
        raise SystemExit("No dataset paths are configured")
    report = []
    for crop, roots in datasets.items():
        for source_index, source in enumerate(roots, start=1):
            source_report = inspect_crop(crop, source["images"], source["labels"])
            source_report["source_index"] = source_index
            source_report["source_count"] = len(roots)
            source_report["version"] = source["version"]
            report.append(source_report)
    print(json.dumps(report, indent=2))


def command_prepare(config: dict[str, Any], crop: str) -> None:
    datasets = configured_datasets(config)
    if crop not in datasets:
        raise SystemExit(f"No path configured for crop '{crop}' in experiment_config.json")
    roots = datasets[crop]
    prepared_sources: list[Path] = []
    for source_index, source in enumerate(roots, start=1):
        report = inspect_crop(crop, source["images"], source["labels"])
        if report["status"] != "ready":
            raise SystemExit(
                f"Dataset source {source_index}/{len(roots)} is not ready:\n"
                f"{json.dumps(report, indent=2)}"
            )
        source_output = (
            crop_output(config, crop)
            if len(roots) == 1
            else Path(config["output_root"]) / "_sources" / f"{crop}_{source_index:02d}"
        )
        run([
            sys.executable,
            str(HERE / "ornascout_pipeline_v2.py"),
            "prepare",
            "--images-root", str(source["images"]),
            "--labels-root", str(source["labels"]),
            "--crop", crop,
            "--out-dir", str(source_output),
            "--tile-size", str(config.get("tile_size", 1024)),
            "--overlap", str(config.get("overlap", 0.25)),
            "--min-visible-fraction", str(config.get("min_visible_fraction", 0.5)),
            "--seed", str(config.get("seed", 2026)),
        ])
        prepared_sources.append(source_output)

    if len(prepared_sources) > 1:
        run([
            sys.executable,
            str(HERE / "ornascout_pipeline_v2.py"),
            "merge-crops",
            "--inputs", *(str(path) for path in prepared_sources),
            "--out-dir", str(crop_output(config, crop)),
        ])
    summary_path = crop_output(config, crop) / "dataset_summary.json"
    if summary_path.exists():
        print("\nPreparation complete:")
        print(summary_path.read_text(encoding="utf-8"))
    merge_summary = crop_output(config, crop) / "merge_summary.json"
    if merge_summary.exists():
        print("\nMerged source summary:")
        print(merge_summary.read_text(encoding="utf-8"))
    print(f"Outputs: {crop_output(config, crop)}")


def command_merge(config: dict[str, Any]) -> None:
    prepared = [
        crop_output(config, crop)
        for crop in configured_datasets(config)
        if (crop_output(config, crop) / "inference_manifest.jsonl").exists()
    ]
    if not prepared:
        raise SystemExit("Prepare at least one configured crop before merging")
    run([
        sys.executable,
        str(HERE / "ornascout_pipeline_v2.py"),
        "merge-crops",
        "--inputs", *(str(path) for path in prepared),
        "--out-dir", str(scope_output(config, "combined")),
    ])


def command_prepare_all(config: dict[str, Any], config_path: Path) -> None:
    datasets = configured_datasets(config)
    for crop in datasets:
        command_prepare(config, crop)
    command_merge(config)
    run([
        sys.executable,
        str(HERE / "exploratory_data_analysis.py"),
        "--config", str(config_path),
    ])


def command_infer(
    config: dict[str, Any],
    model: str,
    scope: str,
    split: str,
    repeats: int,
    limit: int | None,
    adapter: Path | None,
    run_name: str | None,
    max_new_tokens: int,
    device: str,
    dtype: str,
    single_image_patch: bool,
) -> None:
    manifest = scope_output(config, scope) / "inference_manifest.jsonl"
    label = run_name or model
    output = Path(config["output_root"]) / "predictions" / f"{label}_{scope}_{split}.jsonl"
    command = [
        sys.executable,
        str(HERE / "run_vlm_wacv.py"),
        "--manifest", str(manifest),
        "--model", model,
        "--run-name", label,
        "--split", split,
        "--repeats", str(repeats),
        "--max-new-tokens", str(max_new_tokens),
        "--device", device,
        "--dtype", dtype,
        "--out", str(output),
    ]
    if limit is not None:
        command.extend(["--limit", str(limit)])
    if adapter is not None:
        command.extend(["--peft-adapter", str(adapter)])
    if single_image_patch:
        command.append("--single-image-patch")
    run(command)


def command_train(config: dict[str, Any], scope: str) -> None:
    run([
        sys.executable,
        str(HERE / "train_smolvlm_lora.py"),
        "--train", str(scope_output(config, scope) / "sft_train.jsonl"),
        "--out-dir", str(Path(config["output_root"]) / "adapters" / f"smolvlm2_{scope}"),
    ])


def command_evaluate(config: dict[str, Any], scope: str) -> None:
    prediction_dir = Path(config["output_root"]) / "predictions"
    prediction_files = sorted(
        path
        for path in prediction_dir.glob(f"*_{scope}_test.jsonl")
        if not path.name.startswith("detector_")
        and not path.name.startswith("._")
        and "debug" not in path.stem
        and path.stat().st_size > 0
    )
    if not prediction_files:
        raise SystemExit(f"No test prediction files found for scope '{scope}'")
    command = [
        sys.executable,
        str(HERE / "ornascout_pipeline_v2.py"),
        "evaluate",
        "--ground-truth", str(scope_output(config, scope) / "ground_truth.jsonl"),
        "--predictions", *(str(path) for path in prediction_files),
        "--out-dir", str(Path(config["output_root"]) / "evaluation" / scope),
        "--seed", str(config.get("seed", 2026)),
    ]
    detector_file = prediction_dir / f"detector_{scope}_test.jsonl"
    if detector_file.exists():
        command.extend(["--detector-evidence", str(detector_file)])
    run(command)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="One-entry OrnaScout-VLM experiment launcher")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect")
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--crop", required=True)
    sub.add_parser("merge")
    sub.add_parser("prepare-all")
    figures = sub.add_parser("figures")
    figures.add_argument("--crop", required=True)
    train = sub.add_parser("train")
    train.add_argument("--scope", choices=["magnolia", "azalea", "combined"], required=True)
    infer = sub.add_parser("infer")
    infer.add_argument(
        "--model",
        choices=["smolvlm2_500m", "smolvlm2_2p2b", "phi35_vision", "llava15_7b"],
        required=True,
    )
    infer.add_argument("--scope", choices=["magnolia", "azalea", "combined"], required=True)
    infer.add_argument("--split", choices=["val", "test", "all"], default="test")
    infer.add_argument("--repeats", type=int, default=3)
    infer.add_argument("--limit", type=int)
    infer.add_argument("--max-new-tokens", type=int, default=128)
    infer.add_argument("--device", default="auto")
    infer.add_argument("--dtype", choices=["auto", "float16", "float32", "bfloat16"], default="auto")
    infer.add_argument("--single-image-patch", action="store_true")
    infer.add_argument("--adapter", type=Path)
    infer.add_argument("--run-name", help="Unique label, e.g. smolvlm2_magnolia_to_azalea")
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--scope", choices=["magnolia", "azalea", "combined"], required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config)
    if args.command == "inspect":
        command_inspect(config)
    elif args.command == "prepare":
        command_prepare(config, args.crop.lower())
    elif args.command == "merge":
        command_merge(config)
    elif args.command == "prepare-all":
        command_prepare_all(config, args.config)
    elif args.command == "figures":
        command_figures(config, args.crop.lower())
    elif args.command == "train":
        command_train(config, args.scope)
    elif args.command == "infer":
        command_infer(
            config,
            args.model,
            args.scope,
            args.split,
            args.repeats,
            args.limit,
            args.adapter,
            args.run_name,
            args.max_new_tokens,
            args.device,
            args.dtype,
            args.single_image_patch,
        )
    elif args.command == "evaluate":
        command_evaluate(config, args.scope)


if __name__ == "__main__":
    main()

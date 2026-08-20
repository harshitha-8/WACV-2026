#!/usr/bin/env python3
"""Create data, evaluation, ablation, and failure-analysis figures."""

from __future__ import annotations

import argparse
import csv
import json
import textwrap
from pathlib import Path

from PIL import Image


def rows(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def configure_style() -> None:
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": ["Arial", "DejaVu Sans"],
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
        "figure.facecolor": "white",
    })


def save_figure(fig, out_dir: Path, name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{name}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(out_dir / f"{name}.pdf", bbox_inches="tight", facecolor="white")


def _first_jsonl_record(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                return json.loads(line)
    raise ValueError(f"No records found in {path}")


def _is_complete_json_object(text: str) -> bool:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = candidate.removeprefix("```json").removeprefix("```").strip()
        candidate = candidate.removesuffix("```").strip()
    try:
        return isinstance(json.loads(candidate), dict)
    except (json.JSONDecodeError, TypeError):
        return False


def smoke_report(predictions: list[Path], ground_truth: Path, out_dir: Path) -> None:
    """Render a one-tile engineering diagnostic without implying task accuracy."""
    import matplotlib.pyplot as plt

    configure_style()
    records = [_first_jsonl_record(path) for path in predictions if path.exists() and path.stat().st_size]
    if not records:
        raise SystemExit("No non-empty smoke prediction files were supplied")

    tile_ids = {record["tile_id"] for record in records}
    if len(tile_ids) != 1:
        raise SystemExit(f"Smoke records must use one common tile; found {sorted(tile_ids)}")
    tile_id = next(iter(tile_ids))
    truth = None
    with ground_truth.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("tile_id") == tile_id:
                truth = row
                break
    if truth is None:
        raise SystemExit(f"Ground truth not found for smoke tile {tile_id}")

    report_rows = []
    for record in records:
        report_rows.append({
            "model": record["model"].split("_zeroshot", 1)[0],
            "model_id": record.get("model_id", ""),
            "tile_id": tile_id,
            "device": record.get("device", ""),
            "dtype": record.get("dtype", ""),
            "latency_s": round(float(record.get("latency_ms", 0.0)) / 1000.0, 3),
            "complete_json": int(_is_complete_json_object(record.get("prediction", ""))),
            "output_preview": record.get("prediction", "").replace("\n", " ")[:120],
        })
    report_rows.sort(key=lambda row: row["latency_s"])

    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "smoke_diagnostic.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(report_rows[0]))
        writer.writeheader()
        writer.writerows(report_rows)

    fig, (image_ax, latency_ax) = plt.subplots(
        1, 2, figsize=(12.5, 5.4), gridspec_kw={"width_ratios": [1.05, 1.25]}
    )
    image_ax.imshow(Image.open(truth["tile_path"]).convert("RGB"))
    image_ax.set_title("Shared smoke-test tile", loc="left")
    image_ax.axis("off")
    gt_text = (
        f"Crop: {truth['crop_type']}   |   boxes: {truth['n_boxes']}\n"
        f"Count bin: {truth['count_bin']}   |   density: {truth['density_class']}   |   "
        f"coverage: {truth['coverage_class']}"
    )
    image_ax.text(
        0.0, -0.08, gt_text, transform=image_ax.transAxes, va="top", fontsize=9,
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "#f4f6f7", "edgecolor": "#aab3bb"},
    )

    labels = [row["model"] for row in report_rows]
    latencies = [row["latency_s"] for row in report_rows]
    bars = latency_ax.barh(labels, latencies, color="#4c78a8", height=0.58)
    latency_ax.set_xscale("log")
    latency_ax.set_xlabel("Generation latency for 8 output tokens (s, log scale)")
    latency_ax.set_title("Compatibility smoke test", loc="left")
    latency_ax.grid(axis="x", alpha=0.25)
    for bar, row in zip(bars, report_rows):
        status = "complete JSON" if row["complete_json"] else "truncated"
        latency_ax.text(
            bar.get_width() * 1.06, bar.get_y() + bar.get_height() / 2,
            f"{row['latency_s']:.1f}s | {status}", va="center", fontsize=8,
        )
    latency_ax.margins(x=0.32)

    fig.suptitle("OrnaScout model-runtime diagnostic", fontsize=13, fontweight="bold")
    fig.text(
        0.5, 0.015,
        textwrap.fill(
            "One Magnolia test tile, one repeat, and an eight-token cap. This figure verifies model loading "
            "and execution only; it is not an accuracy, memory, or deployment benchmark.",
            width=120,
        ),
        ha="center", va="bottom", fontsize=8, color="#4f5b66",
    )
    fig.tight_layout(rect=[0, 0.06, 1, 0.94])
    save_figure(fig, out_dir, "00_smoke_runtime_diagnostic")
    plt.close(fig)


def evaluation_figures(per_tile: Path, summary: Path, out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    configure_style()
    detailed, aggregate = rows(per_tile), rows(summary)
    out_dir.mkdir(parents=True, exist_ok=True)
    test = [x for x in aggregate if x["split"] == "test"]
    models = [x["model"] for x in test]
    metrics = ["presence_f1", "count_bin_macro_f1", "density_macro_f1", "coverage_macro_f1"]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    width = 0.18
    positions = list(range(len(models)))
    for offset, metric in enumerate(metrics):
        ax.bar([x + (offset - 1.5) * width for x in positions], [float(r[metric]) for r in test], width, label=metric)
    ax.set_xticks(positions, models)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Score")
    ax.legend(ncol=2)
    fig.tight_layout()
    save_figure(fig, out_dir, "03_model_comparison")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4.5))
    for row in test:
        ax.scatter(float(row["latency_ms_mean"]), float(row["presence_f1"]), s=100, label=row["model"])
    ax.set_xlabel("Mean latency per tile (ms)")
    ax.set_ylabel("Presence F1")
    ax.legend()
    fig.tight_layout()
    save_figure(fig, out_dir, "04_accuracy_latency_tradeoff")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    gate_labels = ["accept", "abstain", "escalate"]
    width = 0.8 / max(1, len(models))
    positions = list(range(len(gate_labels)))
    for model_idx, model in enumerate(models):
        subset = [x for x in detailed if x["model"] == model and x["split"] == "test"]
        values = [sum(x["gate_decision"] == label for x in subset) / max(1, len(subset)) for label in gate_labels]
        ax.bar([x + model_idx * width for x in positions], values, width, label=model)
    ax.set_xticks([x + width * max(0, len(models) - 1) / 2 for x in positions], gate_labels)
    ax.set_ylabel("Fraction of test tiles")
    ax.set_title("Evidence-gate outcomes")
    ax.legend()
    fig.tight_layout()
    save_figure(fig, out_dir, "05_gate_outcomes")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for model in models:
        subset = sorted(
            [x for x in detailed if x["model"] == model and x["split"] == "test"],
            key=lambda x: float(x["gate_score"]),
            reverse=True,
        )
        coverage, risk = [], []
        for k in range(max(1, len(subset) // 20), len(subset) + 1, max(1, len(subset) // 20)):
            accepted = subset[:k]
            coverage.append(k / len(subset))
            risk.append(1 - sum(int(x["plant_presence_correct"]) for x in accepted) / k)
        ax.plot(coverage, risk, marker="o", markersize=3, label=model)
    ax.set_xlabel("Coverage")
    ax.set_ylabel("Selective risk")
    ax.set_title("Risk-coverage behavior")
    ax.legend()
    fig.tight_layout()
    save_figure(fig, out_dir, "06_risk_coverage")
    plt.close(fig)

    wrong = [x for x in detailed if x["plant_presence_correct"] == "0"]
    wrong.sort(key=lambda row: float(row.get("gate_score", 0.0)), reverse=True)
    failures = []
    seen: set[tuple[str, str, str]] = set()
    for row in wrong:
        key = (row["model"], row["crop"], row["image_id"])
        if key in seen:
            continue
        failures.append(row)
        seen.add(key)
        if len(failures) == 12:
            break
    (out_dir / "failure_cases.json").write_text(json.dumps(failures, indent=2))
    visible_failures = [x for x in failures if x.get("tile_path") and Path(x["tile_path"]).exists()]
    fig, axes = plt.subplots(3, 4, figsize=(12, 8))
    for ax in axes.flat:
        ax.axis("off")
    for ax, failure in zip(axes.flat, visible_failures):
        ax.imshow(Image.open(failure["tile_path"]).convert("RGB"))
        ax.set_title(
            f"{failure['model']} | GT={failure['plant_presence_gt']} | pred={failure['plant_presence_pred']}",
            fontsize=7,
        )
        ax.axis("off")
    fig.suptitle("Highest-confidence presence errors, diversified by source image")
    fig.tight_layout()
    save_figure(fig, out_dir, "07_failure_gallery")
    plt.close(fig)


def cross_crop_figure(table: Path, out_dir: Path) -> None:
    import matplotlib.pyplot as plt

    configure_style()
    data = rows(table)
    out_dir.mkdir(parents=True, exist_ok=True)
    protocols = sorted({x["protocol"] for x in data})
    models = sorted({x["model"] for x in data})
    fig, ax = plt.subplots(figsize=(max(7, len(protocols) * 1.4), max(4, len(models) * 0.7)))
    matrix = []
    for model in models:
        matrix.append([
            float(next((x["presence_f1"] for x in data if x["model"] == model and x["protocol"] == protocol), "nan"))
            for protocol in protocols
        ])
    image = ax.imshow(matrix, vmin=0, vmax=1, cmap="viridis")
    ax.set_xticks(range(len(protocols)), protocols, rotation=30, ha="right")
    ax.set_yticks(range(len(models)), models)
    ax.set_title("Cross-crop presence F1")
    for row_idx, values in enumerate(matrix):
        for col_idx, value in enumerate(values):
            ax.text(col_idx, row_idx, f"{value:.3f}", ha="center", va="center", color="white" if value < 0.55 else "black")
    fig.colorbar(image, ax=ax, label="F1")
    fig.tight_layout()
    save_figure(fig, out_dir, "08_cross_crop_transfer_matrix")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    evaluation = sub.add_parser("evaluation")
    evaluation.add_argument("--per-tile", type=Path, required=True)
    evaluation.add_argument("--summary", type=Path, required=True)
    evaluation.add_argument("--out-dir", type=Path, required=True)
    transfer = sub.add_parser("cross-crop")
    transfer.add_argument("--table", type=Path, required=True)
    transfer.add_argument("--out-dir", type=Path, required=True)
    smoke = sub.add_parser("smoke")
    smoke.add_argument("--predictions", type=Path, nargs="+", required=True)
    smoke.add_argument("--ground-truth", type=Path, required=True)
    smoke.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "evaluation":
        evaluation_figures(args.per_tile, args.summary, args.out_dir)
    elif args.command == "cross-crop":
        cross_crop_figure(args.table, args.out_dir)
    else:
        smoke_report(args.predictions, args.ground_truth, args.out_dir)


if __name__ == "__main__":
    main()

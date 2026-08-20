#!/usr/bin/env python3
"""Prepare and summarize a human audit of YOLO annotation precision.

The script never infers annotation correctness from pixels. It creates a
representative random sample for estimating label precision and a separate
geometry-stress sample for finding unusual boxes. Only completed human review
fields are used by ``summarize``.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

ALLOWED_STATUS = {"valid", "wrong_target", "poor_extent", "duplicate", "uncertain"}
COLORS = {"magnolia": "#2878B5", "azalea": "#D1495B"}


def configure_style() -> None:
    plt.rcParams.update({
        "font.family": ["Arial", "DejaVu Sans"],
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
        "figure.facecolor": "white",
    })


def robust_z(values: pd.Series) -> pd.Series:
    median = float(values.median())
    mad = float((values - median).abs().median())
    scale = 1.4826 * mad
    if scale <= 1e-12:
        return pd.Series(np.zeros(len(values)), index=values.index)
    return (values - median) / scale


def audit_candidates(boxes: pd.DataFrame, images: pd.DataFrame) -> pd.DataFrame:
    data = boxes.merge(
        images[["source", "crop", "image_id", "image_path"]],
        on=["source", "crop", "image_id"],
        how="left",
        validate="many_to_one",
    )
    if data.image_path.isna().any():
        raise ValueError("Some annotation rows do not map to a source image")
    parts: list[pd.DataFrame] = []
    for _, group in data.groupby("crop", sort=True):
        part = group.copy()
        part["area_robust_z"] = robust_z(np.log10(part.area_norm.clip(lower=1e-9)))
        part["aspect_robust_z"] = robust_z(np.log(part.aspect_ratio.clip(lower=1e-6)))
        part["geometry_review_score"] = (
            part.area_robust_z.abs()
            + 0.5 * part.aspect_robust_z.abs()
            + 0.75 * part.near_edge.astype(float)
        )
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def sample_without_replacement(
    group: pd.DataFrame,
    representative_n: int,
    stress_n: int,
    seed: int,
) -> pd.DataFrame:
    representative = group.sample(min(representative_n, len(group)), random_state=seed).copy()
    representative["sample_type"] = "representative_random"
    remainder = group.drop(index=representative.index)
    stress = remainder.nlargest(min(stress_n, len(remainder)), "geometry_review_score").copy()
    stress["sample_type"] = "geometry_stress"
    return pd.concat([representative, stress], ignore_index=True)


def context_crop(row: pd.Series, context_scale: float = 2.2) -> Image.Image:
    with Image.open(row.image_path) as opened:
        image = opened.convert("RGB")
    width, height = image.size
    cx, cy = float(row.x_center) * width, float(row.y_center) * height
    box_w, box_h = float(row.width_norm) * width, float(row.height_norm) * height
    context_side = max(128.0, max(box_w, box_h) * context_scale)
    context_w = context_side
    context_h = context_side
    x1 = max(0, int(round(cx - context_w / 2)))
    y1 = max(0, int(round(cy - context_h / 2)))
    x2 = min(width, int(round(cx + context_w / 2)))
    y2 = min(height, int(round(cy + context_h / 2)))
    patch = image.crop((x1, y1, x2, y2))
    draw = ImageDraw.Draw(patch)
    bx1 = (float(row.x_center) - float(row.width_norm) / 2) * width - x1
    by1 = (float(row.y_center) - float(row.height_norm) / 2) * height - y1
    bx2 = (float(row.x_center) + float(row.width_norm) / 2) * width - x1
    by2 = (float(row.y_center) + float(row.height_norm) / 2) * height - y1
    line_width = max(3, min(patch.size) // 120)
    draw.rectangle((bx1, by1, bx2, by2), outline=(255, 215, 0), width=line_width)
    return patch


def render_review_sheets(manifest: pd.DataFrame, out_dir: Path) -> None:
    sheets = out_dir / "review_sheets"
    sheets.mkdir(parents=True, exist_ok=True)
    for sheet_index, start in enumerate(range(0, len(manifest), 16), start=1):
        subset = manifest.iloc[start:start + 16]
        fig, axes = plt.subplots(4, 4, figsize=(12, 12))
        for axis in axes.flat:
            axis.axis("off")
        for axis, (_, row) in zip(axes.flat, subset.iterrows()):
            axis.imshow(context_crop(row))
            axis.set_title(
                f"{row.audit_id} | {row.crop} | {row.sample_type.replace('_', ' ')}",
                fontsize=7,
            )
            axis.axis("off")
        fig.tight_layout(pad=0.6)
        fig.savefig(sheets / f"audit_sheet_{sheet_index:02d}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)


def prepare(args: argparse.Namespace) -> None:
    configure_style()
    images = pd.read_csv(args.eda_tables / "images.csv", dtype={"image_id": str})
    boxes = pd.read_csv(args.eda_tables / "boxes.csv", dtype={"image_id": str})
    required = {"label_line", "area_norm", "aspect_ratio", "near_edge"}
    missing = required - set(boxes.columns)
    if missing:
        raise SystemExit(
            f"Missing {sorted(missing)} in boxes.csv. Run `python wacv_pipeline.py eda` first."
        )
    candidates = audit_candidates(boxes, images)
    selected: list[pd.DataFrame] = []
    for crop_index, (crop, group) in enumerate(candidates.groupby("crop", sort=True)):
        selected.append(sample_without_replacement(
            group,
            args.representative_per_crop,
            args.stress_per_crop,
            args.seed + crop_index,
        ))
    manifest = pd.concat(selected, ignore_index=True)
    manifest = manifest.sort_values(["crop", "sample_type", "geometry_review_score"], ascending=[True, True, False])
    manifest = manifest.reset_index(drop=True)
    manifest.insert(0, "audit_id", [f"A{index:04d}" for index in range(1, len(manifest) + 1)])
    manifest["review_status"] = ""
    manifest["review_notes"] = ""
    keep = [
        "audit_id", "crop", "source", "image_id", "image_path", "label_line",
        "sample_type", "geometry_review_score", "x_center", "y_center",
        "width_norm", "height_norm", "area_norm", "aspect_ratio", "near_edge",
        "review_status", "review_notes",
    ]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest[keep].to_csv(args.out_dir / "annotation_audit_manifest.csv", index=False)
    render_review_sheets(manifest, args.out_dir)

    counts = manifest.groupby(["crop", "sample_type"]).size().unstack(fill_value=0)
    counts = counts.rename(columns={
        "geometry_stress": "Geometry stress test",
        "representative_random": "Representative random sample",
    })
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    counts.plot.bar(ax=ax, color=["#4C78A8", "#F2CF5B"])
    ax.set_ylabel("Audited boxes")
    ax.set_xlabel("")
    ax.set_title("Annotation-audit sampling design")
    ax.legend(title="", frameon=False)
    ax.tick_params(axis="x", rotation=0)
    fig.tight_layout()
    fig.savefig(args.out_dir / "audit_sampling_design.png", dpi=300, bbox_inches="tight")
    fig.savefig(args.out_dir / "audit_sampling_design.pdf", bbox_inches="tight")
    plt.close(fig)

    instructions = f"""# Annotation audit instructions

Review each yellow ground-truth box in `review_sheets/` and fill `review_status`
in `annotation_audit_manifest.csv` with exactly one of:

- `valid`: correct target and defensible extent
- `wrong_target`: the box encloses the wrong semantic target
- `poor_extent`: correct target but materially inconsistent box extent
- `duplicate`: duplicate annotation of the same target
- `uncertain`: cannot be resolved from the image

Do not edit `sample_type`. The **representative_random** subset is the only
subset used to estimate annotation precision. The **geometry_stress** subset is
reported separately as a diagnostic and must not be used as an unbiased error
rate. This audit estimates precision of existing boxes; it does not estimate
missed-annotation recall.

After review, run:

```bash
python wacv_pipeline.py summarize-audit
```
"""
    (args.out_dir / "AUDIT_INSTRUCTIONS.md").write_text(instructions, encoding="utf-8")
    print(f"Audit manifest: {args.out_dir / 'annotation_audit_manifest.csv'}")
    print(f"Review sheets: {args.out_dir / 'review_sheets'}")


def wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return math.nan, math.nan
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return center - radius, center + radius


def summarize(args: argparse.Namespace) -> None:
    path = args.out_dir / "annotation_audit_manifest.csv"
    data = pd.read_csv(path, keep_default_na=False)
    invalid = sorted(set(data.review_status) - ALLOWED_STATUS - {""})
    if invalid:
        raise SystemExit(f"Invalid review_status values: {invalid}")
    reviewed = data[data.review_status != ""].copy()
    representative = reviewed[reviewed.sample_type == "representative_random"]
    expected_counts = data[data.sample_type == "representative_random"].groupby("crop").size()
    reviewed_counts = representative.groupby("crop").size().reindex(expected_counts.index, fill_value=0)
    incomplete = reviewed_counts[reviewed_counts < expected_counts]
    if not incomplete.empty:
        progress = ", ".join(
            f"{crop}: {int(reviewed_counts[crop])}/{int(expected_counts[crop])}"
            for crop in expected_counts.index
        )
        raise SystemExit(
            "Representative annotation audit is incomplete. "
            f"Review progress: {progress}. Fill review_status for every "
            "representative_random row before summarizing."
        )
    configure_style()
    rows: list[dict[str, object]] = []
    for crop, group in representative.groupby("crop", sort=True):
        resolved = group[group.review_status != "uncertain"]
        valid = int((resolved.review_status == "valid").sum())
        low, high = wilson(valid, len(resolved))
        rows.append({
            "crop": crop,
            "reviewed_representative": len(group),
            "resolved_representative": len(resolved),
            "valid_boxes": valid,
            "annotation_precision": valid / len(resolved) if len(resolved) else math.nan,
            "ci95_low": low,
            "ci95_high": high,
        })
    summary = pd.DataFrame(rows)
    summary.to_csv(args.out_dir / "annotation_audit_summary.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    values = summary.annotation_precision.to_numpy(dtype=float)
    lower = values - summary.ci95_low.to_numpy(dtype=float)
    upper = summary.ci95_high.to_numpy(dtype=float) - values
    axes[0].bar(summary.crop, values, color=[COLORS.get(crop, "#777777") for crop in summary.crop])
    axes[0].errorbar(summary.crop, values, yerr=np.vstack([lower, upper]), fmt="none", color="black", capsize=4)
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("Validated-box fraction")
    axes[0].set_title("Representative annotation precision (95% Wilson CI)")

    category = pd.crosstab(reviewed.crop, reviewed.review_status)
    category = category.reindex(columns=["valid", "wrong_target", "poor_extent", "duplicate", "uncertain"], fill_value=0)
    category.div(category.sum(axis=1), axis=0).mul(100).T.plot.bar(ax=axes[1], color=[COLORS.get(crop, "#777777") for crop in category.index])
    axes[1].set_ylabel("Within-crop reviewed boxes (%)")
    axes[1].set_xlabel("")
    axes[1].set_title("Audit outcome composition (all sampled boxes)")
    axes[1].tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(args.out_dir / "annotation_audit_results.png", dpi=300, bbox_inches="tight")
    fig.savefig(args.out_dir / "annotation_audit_results.pdf", bbox_inches="tight")
    plt.close(fig)
    print(summary.to_string(index=False))


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Human annotation-quality audit")
    sub = p.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--eda-tables", type=Path, required=True)
    prepare_parser.add_argument("--out-dir", type=Path, required=True)
    prepare_parser.add_argument("--representative-per-crop", type=int, default=96)
    prepare_parser.add_argument("--stress-per-crop", type=int, default=64)
    prepare_parser.add_argument("--seed", type=int, default=2026)
    summarize_parser = sub.add_parser("summarize")
    summarize_parser.add_argument("--out-dir", type=Path, required=True)
    return p


def main() -> None:
    args = parser().parse_args()
    if args.command == "prepare":
        prepare(args)
    else:
        summarize(args)


if __name__ == "__main__":
    main()

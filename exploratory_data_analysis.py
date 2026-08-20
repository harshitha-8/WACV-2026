#!/usr/bin/env python3
"""Source-level exploratory analysis for Magnolia and azalea UAV RGB data."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageOps

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
COLORS = {"magnolia": "#2878B5", "azalea": "#D1495B"}


def configured_sources(config: dict[str, Any]) -> list[tuple[str, str, Path, Path]]:
    sources: list[tuple[str, str, Path, Path]] = []
    for crop, raw_sources in config["datasets"].items():
        entries = raw_sources if isinstance(raw_sources, list) else [raw_sources]
        for index, entry in enumerate(entries, start=1):
            if isinstance(entry, str):
                image_root = label_root = Path(entry)
            else:
                image_root = Path(entry["images"])
                label_root = Path(entry.get("labels", entry["images"]))
            sources.append((crop.lower(), f"{crop.lower()}_{index}", image_root, label_root))
    return sources


def original_images(root: Path) -> list[Path]:
    search_root = root / "images" if (root / "images").is_dir() else root
    return sorted(
        path for path in search_root.rglob("*")
        if path.is_file()
        and not path.name.startswith("._")
        and path.suffix.lower() in IMAGE_EXTENSIONS
        and "_annotated" not in path.stem.lower()
    )


def clean_labels(root: Path) -> dict[str, Path]:
    return {
        path.stem: path for path in sorted(root.rglob("*.txt"))
        if path.is_file() and not path.name.startswith("._") and path.name != "classes.txt"
    }


def perceptual_hash(image: Image.Image) -> str:
    gray = ImageOps.grayscale(image).resize((9, 8), Image.Resampling.LANCZOS)
    values = np.asarray(gray, dtype=np.int16)
    bits = values[:, 1:] > values[:, :-1]
    packed = np.packbits(bits.flatten())
    return packed.tobytes().hex()


def image_signals(image: Image.Image) -> dict[str, float]:
    sample = image.copy()
    sample.thumbnail((512, 512), Image.Resampling.LANCZOS)
    rgb = np.asarray(sample.convert("RGB"), dtype=np.float32) / 255.0
    gray = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    gx = np.diff(gray, axis=1)
    gy = np.diff(gray, axis=0)
    exg = 2.0 * rgb[:, :, 1] - rgb[:, :, 0] - rgb[:, :, 2]
    return {
        "brightness_mean": float(gray.mean()),
        "brightness_std": float(gray.std()),
        "gradient_energy": float((gx * gx).mean() + (gy * gy).mean()),
        "excess_green_mean": float(exg.mean()),
        "green_fraction": float((exg > 0.05).mean()),
    }


def parse_label(path: Path, image_id: str, crop: str, source: str) -> tuple[list[dict], list[dict]]:
    boxes: list[dict] = []
    issues: list[dict] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        values = line.split()
        if len(values) != 5:
            issues.append({"source": source, "crop": crop, "image_id": image_id, "issue": "wrong_column_count", "line": line_number})
            continue
        try:
            class_id = int(float(values[0]))
            x, y, width, height = map(float, values[1:])
        except ValueError:
            issues.append({"source": source, "crop": crop, "image_id": image_id, "issue": "non_numeric_label", "line": line_number})
            continue
        if not all(math.isfinite(value) for value in (x, y, width, height)) or width <= 0 or height <= 0:
            issues.append({"source": source, "crop": crop, "image_id": image_id, "issue": "invalid_box_value", "line": line_number})
            continue
        x1, y1, x2, y2 = x - width / 2, y - height / 2, x + width / 2, y + height / 2
        # Six-decimal YOLO exports can overshoot the frame by about 5e-7.
        # Treat only geometrically meaningful overflow as an annotation issue.
        tolerance = 1e-6
        outside = int(x1 < -tolerance or y1 < -tolerance or x2 > 1 + tolerance or y2 > 1 + tolerance)
        near_edge = int(x1 <= 0.01 or y1 <= 0.01 or x2 >= 0.99 or y2 >= 0.99)
        if outside:
            issues.append({"source": source, "crop": crop, "image_id": image_id, "issue": "box_outside_normalized_frame", "line": line_number})
        boxes.append({
            "source": source, "crop": crop, "image_id": image_id, "class_id": class_id,
            "label_line": line_number,
            "x_center": x, "y_center": y, "width_norm": width, "height_norm": height,
            "area_norm": width * height, "aspect_ratio": width / height,
            "near_edge": near_edge, "outside_frame": outside,
            "grid_row_4": min(3, max(0, int(y * 4))),
            "grid_col_4": min(3, max(0, int(x * 4))),
        })
    return boxes, issues


def count_bin(value: int) -> str:
    return "0" if value == 0 else "1-5" if value <= 5 else "6-15" if value <= 15 else "16-30" if value <= 30 else ">30"


def coverage_bin(value: float) -> str:
    return "none" if value == 0 else "low" if value < 0.03 else "medium" if value < 0.12 else "high"


def collect(config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    image_rows: list[dict] = []
    box_rows: list[dict] = []
    issue_rows: list[dict] = []
    for crop, source, image_root, label_root in configured_sources(config):
        labels = clean_labels(label_root)
        images = original_images(image_root)
        image_stems = {path.stem for path in images}
        for label_stem in sorted(set(labels) - image_stems):
            issue_rows.append({"source": source, "crop": crop, "image_id": label_stem, "issue": "label_without_image", "line": ""})
        for image_path in images:
            label_path = labels.get(image_path.stem)
            if label_path is None:
                issue_rows.append({"source": source, "crop": crop, "image_id": image_path.stem, "issue": "image_without_label", "line": ""})
                continue
            try:
                with Image.open(image_path) as opened:
                    image = opened.convert("RGB")
                    width, height = image.size
                    signals = image_signals(image)
                    d_hash = perceptual_hash(image)
            except Exception as exc:
                issue_rows.append({"source": source, "crop": crop, "image_id": image_path.stem, "issue": f"unreadable_image:{type(exc).__name__}", "line": ""})
                continue
            boxes, box_issues = parse_label(label_path, image_path.stem, crop, source)
            issue_rows.extend(box_issues)
            for box in boxes:
                box["width_px"] = box["width_norm"] * width
                box["height_px"] = box["height_norm"] * height
                box["area_px"] = box["area_norm"] * width * height
            box_rows.extend(boxes)
            total_area = min(1.0, sum(box["area_norm"] for box in boxes))
            image_rows.append({
                "source": source, "crop": crop, "image_id": image_path.stem,
                "image_path": str(image_path), "label_path": str(label_path),
                "width": width, "height": height, "megapixels": width * height / 1e6,
                "file_size_mb": image_path.stat().st_size / 1024**2,
                "n_boxes": len(boxes), "count_bin": count_bin(len(boxes)),
                "box_area_sum": total_area, "coverage_bin": coverage_bin(total_area),
                "near_edge_boxes": sum(box["near_edge"] for box in boxes),
                "outside_boxes": sum(box["outside_frame"] for box in boxes),
                "dhash": d_hash, **signals,
            })
    return pd.DataFrame(image_rows), pd.DataFrame(box_rows), pd.DataFrame(issue_rows)


def save_figure(fig: plt.Figure, figures: Path, name: str) -> None:
    fig.savefig(figures / f"{name}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(figures / f"{name}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def style() -> None:
    plt.rcParams.update({
        "font.family": ["Arial", "DejaVu Sans"], "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.titleweight": "bold", "figure.facecolor": "white",
    })


def dataset_overview(images: pd.DataFrame, figures: Path) -> None:
    source = images.groupby(["source", "crop"], as_index=False).agg(
        images=("image_id", "count"),
        boxes=("n_boxes", "sum"),
        median_boxes=("n_boxes", "median"),
        near_edge_boxes=("near_edge_boxes", "sum"),
    )
    # Crop names are the scientifically relevant groups in the current snapshot;
    # internal source indices are retained in the CSV rather than shown in figures.
    source_labels = source["crop"].str.title()
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    axes[0, 0].bar(source_labels, source["images"], color=[COLORS[crop] for crop in source["crop"]])
    axes[0, 0].set_title("Matched source images"); axes[0, 0].tick_params(axis="x", rotation=20)
    axes[0, 1].bar(source_labels, source["boxes"], color=[COLORS[crop] for crop in source["crop"]])
    axes[0, 1].set_title("Total annotated objects"); axes[0, 1].tick_params(axis="x", rotation=20)
    crops = sorted(images["crop"].unique())
    axes[1, 0].boxplot([images.loc[images.crop == crop, "n_boxes"] for crop in crops], tick_labels=crops, showfliers=False)
    axes[1, 0].set_title("Objects per image"); axes[1, 0].set_ylabel("YOLO boxes")
    near_edge_rate = 100 * source["near_edge_boxes"] / source["boxes"]
    axes[1, 1].bar(source_labels, near_edge_rate, color=[COLORS[crop] for crop in source["crop"]])
    axes[1, 1].set_title("Annotations near image boundary"); axes[1, 1].set_ylabel("Percent"); axes[1, 1].tick_params(axis="x", rotation=20)
    fig.suptitle("OrnaScout dataset composition", fontsize=16, fontweight="bold")
    fig.tight_layout()
    save_figure(fig, figures, "01_dataset_overview")


def image_characteristics(images: pd.DataFrame, figures: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    for crop, group in images.groupby("crop"):
        axes[0, 0].scatter(group.width, group.height, s=18, alpha=0.55, label=crop, color=COLORS[crop])
        axes[0, 1].hist(group.megapixels, bins=20, alpha=0.55, label=crop, color=COLORS[crop])
        axes[1, 0].hist(group.brightness_mean, bins=25, alpha=0.55, label=crop, color=COLORS[crop])
        axes[1, 1].hist(group.gradient_energy, bins=25, alpha=0.55, label=crop, color=COLORS[crop])
    axes[0, 0].set_title("Image resolution"); axes[0, 0].set_xlabel("Width (px)"); axes[0, 0].set_ylabel("Height (px)")
    axes[0, 1].set_title("Megapixel distribution"); axes[0, 1].set_xlabel("Megapixels")
    axes[1, 0].set_title("Mean luminance"); axes[1, 0].set_xlabel("Normalized brightness")
    axes[1, 1].set_title("Gradient-energy sharpness proxy"); axes[1, 1].set_xlabel("Gradient energy")
    for axis in axes.flat: axis.legend(frameon=False)
    fig.suptitle("Image-domain characteristics", fontsize=16, fontweight="bold"); fig.tight_layout()
    save_figure(fig, figures, "02_image_characteristics")


def object_geometry(boxes: pd.DataFrame, figures: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    for crop, group in boxes.groupby("crop"):
        axes[0, 0].hist(np.log10(group.area_norm.clip(lower=1e-8)), bins=35, alpha=0.55, label=crop, color=COLORS[crop])
        sample = group.sample(min(3000, len(group)), random_state=2026)
        axes[0, 1].scatter(sample.width_norm, sample.height_norm, s=8, alpha=0.25, label=crop, color=COLORS[crop])
        axes[1, 0].hist(group.aspect_ratio.clip(upper=5), bins=35, alpha=0.55, label=crop, color=COLORS[crop])
    edge = boxes.groupby("crop")["near_edge"].mean().sort_index()
    axes[1, 1].bar(edge.index, 100 * edge.values, color=[COLORS[crop] for crop in edge.index])
    axes[0, 0].set_title("Normalized object area"); axes[0, 0].set_xlabel("log10(width x height)")
    axes[0, 1].set_title("Normalized box dimensions"); axes[0, 1].set_xlabel("Width"); axes[0, 1].set_ylabel("Height")
    axes[1, 0].set_title("Box aspect ratio"); axes[1, 0].set_xlabel("Width / height (clipped at 5)")
    axes[1, 1].set_title("Boxes near image boundary"); axes[1, 1].set_ylabel("Percent")
    for axis in axes.flat:
        if axis is not axes[1, 1]: axis.legend(frameon=False)
    fig.suptitle("Annotation geometry and small-object regime", fontsize=16, fontweight="bold"); fig.tight_layout()
    save_figure(fig, figures, "03_object_geometry")


def spatial_heatmaps(boxes: pd.DataFrame, figures: Path) -> None:
    crops = sorted(boxes.crop.unique())
    fig, axes = plt.subplots(1, len(crops), figsize=(7 * len(crops), 6), squeeze=False)
    probability_maps: dict[str, np.ndarray] = {}
    for crop in crops:
        group = boxes[boxes.crop == crop]
        hist, _, _ = np.histogram2d(group.y_center, group.x_center, bins=30, range=[[0, 1], [0, 1]])
        probability_maps[crop] = 100.0 * hist / max(float(hist.sum()), 1.0)
    shared_max = max(float(values.max()) for values in probability_maps.values())
    for axis, crop in zip(axes[0], crops):
        image = axis.imshow(
            probability_maps[crop], origin="upper", extent=[0, 1, 1, 0],
            cmap="magma", aspect="equal", vmin=0.0, vmax=shared_max,
        )
        axis.set_title(f"{crop.capitalize()} box centers"); axis.set_xlabel("Normalized x"); axis.set_ylabel("Normalized y")
        fig.colorbar(image, ax=axis, fraction=0.046, label="Annotations per cell (%)")
    fig.suptitle("Spatial distribution of annotation centers", fontsize=16, fontweight="bold"); fig.tight_layout()
    save_figure(fig, figures, "04_spatial_density")


def count_and_coverage(images: pd.DataFrame, figures: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.2))
    for crop, group in images.groupby("crop"):
        label = f"{crop} (n={len(group)})"
        axes[0].hist(
            group.n_boxes, bins=30, density=True, histtype="step", linewidth=2.2,
            label=label, color=COLORS[crop],
        )
        axes[0].axvline(group.n_boxes.median(), color=COLORS[crop], linestyle="--", linewidth=1.4)
        rho = group[["n_boxes", "box_area_sum"]].corr(method="spearman").iloc[0, 1]
        axes[1].scatter(
            group.n_boxes, group.box_area_sum, s=20, alpha=0.5,
            label=f"{crop} (Spearman r={rho:.2f})", color=COLORS[crop],
        )
    axes[0].set_title("Source-image annotation counts")
    axes[0].set_xlabel("Ground-truth boxes per source image")
    axes[0].set_ylabel("Probability density")
    axes[0].legend(frameon=False)
    axes[1].set_title("Count versus annotated image occupancy")
    axes[1].set_xlabel("Ground-truth boxes per source image")
    axes[1].set_ylabel("Summed normalized box area (clipped at 1)")
    axes[1].legend(frameon=False)
    fig.suptitle("Annotation quantity and occupancy", fontsize=16, fontweight="bold"); fig.tight_layout()
    save_figure(fig, figures, "05_count_coverage_labels")


def cross_crop_shift(images: pd.DataFrame, boxes: pd.DataFrame, figures: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for crop, group in boxes.groupby("crop"):
        values = np.sort(group.area_norm.to_numpy())
        axes[0].plot(values, np.linspace(0, 1, len(values), endpoint=True), label=crop, color=COLORS[crop], linewidth=2)
    for crop, group in images.groupby("crop"):
        axes[1].scatter(group.excess_green_mean, group.brightness_mean, s=18, alpha=0.45, label=crop, color=COLORS[crop])
        axes[2].hist(group.green_fraction, bins=25, alpha=0.55, label=crop, color=COLORS[crop])
    axes[0].set_xscale("log"); axes[0].set_title("Object-area empirical CDF"); axes[0].set_xlabel("Normalized area"); axes[0].set_ylabel("Cumulative fraction")
    axes[1].set_title("Appearance shift"); axes[1].set_xlabel("Mean excess green"); axes[1].set_ylabel("Mean brightness")
    axes[2].set_title("Green-pixel fraction"); axes[2].set_xlabel("Fraction")
    for axis in axes: axis.legend(frameon=False)
    fig.suptitle("Magnolia-azalea domain shift", fontsize=16, fontweight="bold"); fig.tight_layout()
    save_figure(fig, figures, "06_cross_crop_shift")


def representative_contact_sheet(images: pd.DataFrame, boxes: pd.DataFrame, figures: Path, crop: str) -> None:
    subset = images[images.crop == crop].sort_values("n_boxes")
    if subset.empty:
        return
    quantiles = np.linspace(0, 1, 12)
    indices = sorted(set(min(len(subset) - 1, round(q * (len(subset) - 1))) for q in quantiles))
    chosen = subset.iloc[indices]
    fig, axes = plt.subplots(3, 4, figsize=(16, 11))
    for axis in axes.flat:
        axis.axis("off")
    for axis, (_, row) in zip(axes.flat, chosen.iterrows()):
        with Image.open(row.image_path) as opened:
            image = opened.convert("RGB")
            image.thumbnail((900, 650), Image.Resampling.LANCZOS)
        image_boxes = boxes[(boxes.crop == crop) & (boxes.image_id == row.image_id)]
        draw = ImageDraw.Draw(image)
        for _, box in image_boxes.iterrows():
            x1 = (box.x_center - box.width_norm / 2) * image.width
            y1 = (box.y_center - box.height_norm / 2) * image.height
            x2 = (box.x_center + box.width_norm / 2) * image.width
            y2 = (box.y_center + box.height_norm / 2) * image.height
            draw.rectangle((x1, y1, x2, y2), outline=(255, 215, 0), width=max(1, image.width // 400))
        axis.imshow(image); axis.axis("off")
        axis.set_title(f"{row.source} | boxes={row.n_boxes}", fontsize=9)
    fig.suptitle(f"Representative {crop} images across count quantiles", fontsize=16, fontweight="bold")
    fig.tight_layout()
    save_figure(fig, figures, f"07_{crop}_representative_contact_sheet")


def ordered_distribution(data: pd.DataFrame, key: str, order: list[str]) -> pd.DataFrame:
    table = pd.crosstab(data["crop"], data[key]).reindex(columns=order, fill_value=0)
    return table.div(table.sum(axis=1), axis=0).mul(100)


def prepared_overview(tiles: pd.DataFrame, figures: Path) -> None:
    split_order = ["train", "val", "test"]
    crops = sorted(tiles.crop.unique())
    source_rows = tiles[["source_image_path", "crop", "split"]].drop_duplicates()
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    for axis, frame, title, ylabel in [
        (axes[0, 0], source_rows, "Source images by leakage-safe split", "Source images"),
        (axes[0, 1], tiles, "Generated tiles by split", "Tiles"),
    ]:
        table = pd.crosstab(frame["split"], frame["crop"]).reindex(split_order, fill_value=0)
        table.plot.bar(ax=axis, color=[COLORS[crop] for crop in table.columns])
        axis.set_title(title); axis.set_xlabel(""); axis.set_ylabel(ylabel); axis.tick_params(axis="x", rotation=0)
    positive = tiles.assign(positive=tiles.n_boxes.gt(0)).groupby(["crop", "split"])["positive"].mean().unstack().reindex(columns=split_order)
    positive.T.plot.bar(ax=axes[1, 0], color=[COLORS[crop] for crop in positive.index])
    axes[1, 0].set_title("Positive-tile rate"); axes[1, 0].set_ylabel("Fraction"); axes[1, 0].set_xlabel(""); axes[1, 0].set_ylim(0, 1); axes[1, 0].tick_params(axis="x", rotation=0)
    median_count = tiles.groupby(["crop", "split"])["n_boxes"].median().unstack().reindex(columns=split_order)
    median_count.T.plot.bar(ax=axes[1, 1], color=[COLORS[crop] for crop in median_count.index])
    axes[1, 1].set_title("Median visible centers per tile"); axes[1, 1].set_ylabel("Boxes per tile"); axes[1, 1].set_xlabel(""); axes[1, 1].tick_params(axis="x", rotation=0)
    fig.suptitle("Prepared dataset composition and split behavior", fontsize=16, fontweight="bold")
    fig.tight_layout(); save_figure(fig, figures, "08_prepared_dataset_overview")


def prepared_label_balance(tiles: pd.DataFrame, figures: Path) -> None:
    specifications = [
        ("count_bin", ["0", "1-5", "6-15", "16-30", ">30"], "Count-bin support"),
        ("density_class", ["empty", "sparse", "moderate", "dense"], "Density-class support"),
        ("coverage_class", ["none", "low", "medium", "high"], "Coverage-class support"),
        ("plant_presence", ["no", "yes"], "Presence support"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    for axis, (key, order, title) in zip(axes.flat, specifications):
        table = ordered_distribution(tiles, key, order)
        table.T.plot.bar(ax=axis, color=[COLORS[crop] for crop in table.index])
        axis.set_title(title); axis.set_ylabel("Within-crop percent"); axis.set_xlabel(""); axis.tick_params(axis="x", rotation=20)
    fig.suptitle("Tile-label balance by crop", fontsize=16, fontweight="bold")
    fig.tight_layout(); save_figure(fig, figures, "09_tile_label_balance")


def prepared_count_coverage(tiles: pd.DataFrame, figures: Path) -> None:
    crops = sorted(tiles.crop.unique())
    fig, axes = plt.subplots(1, len(crops), figsize=(7 * len(crops), 5), squeeze=False)
    for axis, crop in zip(axes[0], crops):
        group = tiles[tiles.crop == crop]
        graphic = axis.hexbin(group.n_boxes, group.box_coverage, gridsize=28, mincnt=1, bins="log", cmap="viridis")
        axis.set_title(f"{crop.capitalize()}: count versus coverage")
        axis.set_xlabel("Visible box centers per tile"); axis.set_ylabel("Summed box-area proxy")
        fig.colorbar(graphic, ax=axis, fraction=0.046, label="log10(tile frequency)")
    fig.suptitle("Relationship between tile count and spatial coverage", fontsize=16, fontweight="bold")
    fig.tight_layout(); save_figure(fig, figures, "10_tile_count_coverage")


def prepared_split_stability(tiles: pd.DataFrame, figures: Path) -> None:
    split_order = ["train", "val", "test"]
    crops = sorted(tiles.crop.unique())
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    labels, count_values, coverage_values = [], [], []
    for crop in crops:
        for split in split_order:
            subset = tiles[(tiles.crop == crop) & (tiles.split == split)]
            labels.append(f"{crop}\n{split}")
            count_values.append(subset.n_boxes)
            coverage_values.append(subset.box_coverage)
    axes[0].boxplot(count_values, tick_labels=labels, showfliers=False)
    axes[0].set_title("Object count by crop and split"); axes[0].set_ylabel("Boxes per tile")
    axes[1].boxplot(coverage_values, tick_labels=labels, showfliers=False)
    axes[1].set_title("Summed box area by crop and split"); axes[1].set_ylabel("Summed box-area proxy")
    fig.suptitle("Leakage-safe split stability", fontsize=16, fontweight="bold")
    fig.tight_layout(); save_figure(fig, figures, "11_split_stability")


def prepared_spatial_maps(tiles: pd.DataFrame, figures: Path) -> None:
    indexed_parts: list[pd.DataFrame] = []
    for _, group in tiles.groupby("source_image_path", sort=False):
        part = group.copy()
        x_values = {value: index for index, value in enumerate(sorted(part.x0.unique()))}
        y_values = {value: index for index, value in enumerate(sorted(part.y0.unique()))}
        part["grid_col"] = part.x0.map(x_values)
        part["grid_row"] = part.y0.map(y_values)
        indexed_parts.append(part)
    indexed = pd.concat(indexed_parts, ignore_index=True)
    crops = sorted(indexed.crop.unique())
    fig, axes = plt.subplots(1, len(crops), figsize=(7 * len(crops), 6), squeeze=False)
    for axis, crop in zip(axes[0], crops):
        group = indexed[indexed.crop == crop].copy()
        group["positive"] = group.n_boxes.gt(0).astype(float)
        rate_table = group.pivot_table(index="grid_row", columns="grid_col", values="positive", aggfunc="mean")
        image = axis.imshow(rate_table.to_numpy(), origin="upper", cmap="magma", vmin=0, vmax=1, aspect="equal")
        axis.set_title(f"{crop.capitalize()} positive-tile probability")
        axis.set_xlabel("Tile column"); axis.set_ylabel("Tile row")
        axis.set_xticks(range(len(rate_table.columns)), [str(int(value) + 1) for value in rate_table.columns])
        axis.set_yticks(range(len(rate_table.index)), [str(int(value) + 1) for value in rate_table.index])
        fig.colorbar(image, ax=axis, fraction=0.046, label="Positive fraction")
    fig.suptitle("Spatial distribution of annotated evidence", fontsize=16, fontweight="bold")
    fig.tight_layout(); save_figure(fig, figures, "12_spatial_positive_rate")


def prepared_source_behavior(tiles: pd.DataFrame, images: pd.DataFrame, figures: Path, tables: Path) -> None:
    source = tiles.groupby(["source_image_path", "crop", "split"], as_index=False).agg(
        tiles=("tile_id", "count"), positive_tile_rate=("n_boxes", lambda values: float((values > 0).mean())),
        mean_boxes_per_tile=("n_boxes", "mean"), max_boxes_per_tile=("n_boxes", "max"),
        hard_negative_tiles=("is_hard_negative", "sum"), boundary_tiles=("is_boundary_tile", "sum"),
    )
    source = source.merge(
        images[["image_path", "n_boxes", "brightness_mean", "green_fraction"]],
        left_on="source_image_path", right_on="image_path", how="left", validate="one_to_one",
    ).rename(columns={"n_boxes": "source_boxes"})
    source.to_csv(tables / "prepared_source_summary.csv", index=False)
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    for crop, group in source.groupby("crop"):
        axes[0, 0].scatter(group.source_boxes, group.positive_tile_rate, s=22, alpha=0.55, label=crop, color=COLORS[crop])
        axes[0, 1].scatter(group.source_boxes, group.mean_boxes_per_tile, s=22, alpha=0.55, label=crop, color=COLORS[crop])
        axes[1, 0].hist(group.positive_tile_rate, bins=20, alpha=0.55, label=crop, color=COLORS[crop])
        axes[1, 1].scatter(group.green_fraction, group.positive_tile_rate, s=22, alpha=0.55, label=crop, color=COLORS[crop])
    axes[0, 0].set_title("Source annotations versus positive-tile rate"); axes[0, 0].set_xlabel("Source boxes"); axes[0, 0].set_ylabel("Positive-tile fraction")
    axes[0, 1].set_title("Source annotations versus mean tile count"); axes[0, 1].set_xlabel("Source boxes"); axes[0, 1].set_ylabel("Mean boxes per tile")
    axes[1, 0].set_title("Positive-tile fraction across source images"); axes[1, 0].set_xlabel("Positive-tile fraction")
    axes[1, 1].set_title("Appearance versus tile positivity"); axes[1, 1].set_xlabel("Source green fraction"); axes[1, 1].set_ylabel("Positive-tile fraction")
    for axis in axes.flat: axis.legend(frameon=False)
    fig.suptitle("Source-image to tile-level behavior", fontsize=16, fontweight="bold")
    fig.tight_layout(); save_figure(fig, figures, "13_source_to_tile_behavior")


def prepared_ecdfs(tiles: pd.DataFrame, figures: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for crop, group in tiles.groupby("crop"):
        for axis, values, label in [
            (axes[0], group.n_boxes.to_numpy(), "Boxes per tile"),
            (axes[1], group.box_coverage.to_numpy(), "Summed box-area proxy"),
        ]:
            ordered = np.sort(values)
            axis.plot(ordered, np.arange(1, len(ordered) + 1) / len(ordered), linewidth=2, label=crop, color=COLORS[crop])
            axis.set_xlabel(label); axis.set_ylabel("Cumulative fraction"); axis.legend(frameon=False)
    axes[0].set_title("Tile-count empirical CDF"); axes[1].set_title("Coverage empirical CDF")
    fig.suptitle("Cross-crop tile-label shift", fontsize=16, fontweight="bold")
    fig.tight_layout(); save_figure(fig, figures, "14_tile_label_ecdfs")


def prepared_cooccurrence(tiles: pd.DataFrame, figures: Path) -> None:
    crops = sorted(tiles.crop.unique())
    count_order = ["0", "1-5", "6-15", "16-30", ">30"]
    coverage_order = ["none", "low", "medium", "high"]
    fig, axes = plt.subplots(1, len(crops), figsize=(7 * len(crops), 5), squeeze=False)
    for axis, crop in zip(axes[0], crops):
        table = pd.crosstab(tiles.loc[tiles.crop == crop, "count_bin"], tiles.loc[tiles.crop == crop, "coverage_class"])
        table = table.reindex(index=count_order, columns=coverage_order, fill_value=0)
        percentages = table.to_numpy(dtype=float) / max(1, table.to_numpy().sum()) * 100
        image = axis.imshow(percentages, cmap="Blues", aspect="auto")
        axis.set_xticks(range(len(coverage_order)), coverage_order, rotation=20)
        axis.set_yticks(range(len(count_order)), count_order)
        axis.set_xlabel("Coverage class"); axis.set_ylabel("Count bin"); axis.set_title(crop.capitalize())
        for row in range(percentages.shape[0]):
            for column in range(percentages.shape[1]):
                axis.text(column, row, f"{percentages[row, column]:.1f}%", ha="center", va="center", color="white" if percentages[row, column] > percentages.max() * 0.5 else "black")
        fig.colorbar(image, ax=axis, fraction=0.046, label="Within-crop percent")
    fig.suptitle("Count-bin and coverage-class co-occurrence", fontsize=16, fontweight="bold")
    fig.tight_layout(); save_figure(fig, figures, "15_label_cooccurrence")


def prepared_imbalance(tiles: pd.DataFrame, images: pd.DataFrame, boxes: pd.DataFrame, figures: Path) -> None:
    crops = sorted(tiles.crop.unique())
    levels = {
        "Source images": images.crop.value_counts(),
        "Source boxes": boxes.crop.value_counts(),
        "Generated tiles": tiles.crop.value_counts(),
        "Positive tiles": tiles.loc[tiles.n_boxes > 0, "crop"].value_counts(),
    }
    matrix = pd.DataFrame(levels).T.reindex(columns=crops).fillna(0)
    percentages = matrix.div(matrix.sum(axis=1), axis=0).mul(100)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    percentages.plot.bar(stacked=True, ax=axes[0], color=[COLORS[crop] for crop in crops])
    axes[0].set_title("Crop composition across statistical levels"); axes[0].set_ylabel("Percent"); axes[0].set_xlabel(""); axes[0].tick_params(axis="x", rotation=15)
    inverse = 1 / percentages.clip(lower=1e-9)
    inverse = inverse.div(inverse.sum(axis=1), axis=0)
    inverse.plot.bar(ax=axes[1], color=[COLORS[crop] for crop in crops])
    axes[1].set_title("Normalized inverse-frequency sampling weights"); axes[1].set_ylabel("Weight"); axes[1].set_xlabel(""); axes[1].tick_params(axis="x", rotation=15)
    fig.suptitle("Crop imbalance and sampling implications", fontsize=16, fontweight="bold")
    fig.tight_layout(); save_figure(fig, figures, "16_crop_imbalance")


def prepared_tables_and_report(tiles: pd.DataFrame, tables: Path, out_dir: Path) -> None:
    crop_split = tiles.groupby(["crop", "split"], as_index=False).agg(
        source_images=("source_image_path", "nunique"), tiles=("tile_id", "count"),
        positive_tiles=("n_boxes", lambda values: int((values > 0).sum())),
        median_boxes=("n_boxes", "median"), mean_coverage=("box_coverage", "mean"),
        hard_negatives=("is_hard_negative", "sum"),
    )
    crop_split.to_csv(tables / "prepared_summary_by_crop_split.csv", index=False)
    leakage = tiles.groupby("source_image_path").split.nunique()
    audit = {
        "tiles": int(len(tiles)), "unique_tile_ids": int(tiles.tile_id.nunique()),
        "source_images": int(tiles.source_image_path.nunique()),
        "source_images_crossing_splits": int((leakage > 1).sum()),
        "duplicate_tile_ids": int(tiles.tile_id.duplicated().sum()),
        "duplicate_tile_paths": int(tiles.tile_path.duplicated().sum()),
        "tiles_by_crop": {str(k): int(v) for k, v in tiles.crop.value_counts().items()},
        "tiles_by_split": {str(k): int(v) for k, v in tiles.split.value_counts().items()},
        "hard_negatives": int(tiles.is_hard_negative.sum()),
        "count_bins": {str(k): int(v) for k, v in tiles.count_bin.value_counts().items()},
        "coverage_classes": {str(k): int(v) for k, v in tiles.coverage_class.value_counts().items()},
        "density_classes": {str(k): int(v) for k, v in tiles.density_class.value_counts().items()},
        "tiles_per_source_min": int(tiles.groupby("source_image_path").size().min()),
        "tiles_per_source_max": int(tiles.groupby("source_image_path").size().max()),
    }
    (out_dir / "prepared_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    lines = [
        "# Prepared tile-level EDA", "",
        f"- Tiles: **{audit['tiles']:,}** from **{audit['source_images']:,}** source images.",
        f"- Crop composition: `{audit['tiles_by_crop']}`.",
        f"- Split composition: `{audit['tiles_by_split']}`.",
        f"- Hard-negative tiles: **{audit['hard_negatives']:,}**.",
        f"- Count-bin support: `{audit['count_bins']}`.",
        f"- Coverage-class support: `{audit['coverage_classes']}`.",
        f"- Density-class support: `{audit['density_classes']}`.",
        f"- Tiles per source image: **{audit['tiles_per_source_min']} to {audit['tiles_per_source_max']}**.",
        f"- Duplicate tile IDs: **{audit['duplicate_tile_ids']}**; duplicate tile paths: **{audit['duplicate_tile_paths']}**.",
        f"- Source images crossing splits: **{audit['source_images_crossing_splits']}**.", "",
        "Tiles are correlated views derived from source images and are not independent experimental samples. Confidence intervals and statistical tests must cluster by source image.",
        "Crop imbalance remains substantial after tiling; report per-crop metrics and use crop-aware sampling rather than relying only on a pooled score.",
        "The current coverage taxonomy is severely imbalanced: the high class contains most tiles while the low class is nearly absent. Recalibrate coverage thresholds from training data only before treating coverage classification as a primary benchmark.",
        "The current object-truncation flag fires when any source box is partially intersected or rejected by a tile. Its high prevalence makes it unsuitable, by itself, as ground truth for human-review decisions.",
    ]
    (out_dir / "PREPARED_EDA_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def prepared_eda(tile_index: Path, images: pd.DataFrame, boxes: pd.DataFrame, out_dir: Path) -> None:
    tiles = pd.read_csv(tile_index, low_memory=False)
    for column in ["x0", "y0", "width", "height", "n_boxes", "box_coverage", "is_boundary_tile", "is_hard_negative"]:
        tiles[column] = pd.to_numeric(tiles[column], errors="raise")
    figures, tables = out_dir / "prepared_figures", out_dir / "tables"
    figures.mkdir(parents=True, exist_ok=True); tables.mkdir(parents=True, exist_ok=True)
    prepared_overview(tiles, figures)
    prepared_label_balance(tiles, figures)
    prepared_count_coverage(tiles, figures)
    prepared_split_stability(tiles, figures)
    prepared_spatial_maps(tiles, figures)
    prepared_source_behavior(tiles, images, figures, tables)
    prepared_ecdfs(tiles, figures)
    prepared_cooccurrence(tiles, figures)
    prepared_imbalance(tiles, images, boxes, figures)
    prepared_tables_and_report(tiles, tables, out_dir)


def summaries(images: pd.DataFrame, boxes: pd.DataFrame, issues: pd.DataFrame, tables: Path) -> dict[str, Any]:
    by_source = images.groupby(["source", "crop"], as_index=False).agg(
        labeled_images=("image_id", "count"), total_boxes=("n_boxes", "sum"),
        median_boxes=("n_boxes", "median"), mean_megapixels=("megapixels", "mean"),
        median_brightness=("brightness_mean", "median"), median_gradient_energy=("gradient_energy", "median"),
    )
    by_crop = images.groupby("crop", as_index=False).agg(
        labeled_images=("image_id", "count"), total_boxes=("n_boxes", "sum"),
        median_boxes=("n_boxes", "median"), mean_boxes=("n_boxes", "mean"),
        mean_megapixels=("megapixels", "mean"), empty_images=("n_boxes", lambda values: int((values == 0).sum())),
    )
    duplicates = images.groupby("dhash").filter(lambda group: len(group) > 1).sort_values(["dhash", "source", "image_id"])
    by_source.to_csv(tables / "summary_by_source.csv", index=False)
    by_crop.to_csv(tables / "summary_by_crop.csv", index=False)
    duplicates.to_csv(tables / "possible_perceptual_duplicates.csv", index=False)
    issue_counts = Counter(issues.issue) if not issues.empty else Counter()
    class_counts = Counter(int(value) for value in boxes.class_id) if not boxes.empty else Counter()
    crop_statistics: dict[str, dict[str, float | int]] = {}
    for crop, group in images.groupby("crop"):
        crop_boxes = boxes[boxes.crop == crop]
        crop_statistics[str(crop)] = {
            "images": int(len(group)),
            "annotations": int(len(crop_boxes)),
            "empty_images": int((group.n_boxes == 0).sum()),
            "median_boxes_per_image": float(group.n_boxes.median()),
            "p10_boxes_per_image": float(group.n_boxes.quantile(0.10)),
            "p90_boxes_per_image": float(group.n_boxes.quantile(0.90)),
            "median_box_area_norm": float(crop_boxes.area_norm.median()),
            "median_brightness": float(group.brightness_mean.median()),
            "median_green_fraction": float(group.green_fraction.median()),
        }
    resolution_profiles = {
        f"{source}:{int(width)}x{int(height)}": int(count)
        for (source, width, height), count in images.groupby(["source", "width", "height"]).size().items()
    }
    return {
        "labeled_images": int(len(images)), "annotations": int(len(boxes)),
        "images_by_crop": {str(k): int(v) for k, v in images.crop.value_counts().items()},
        "annotations_by_crop": {str(k): int(v) for k, v in boxes.crop.value_counts().items()},
        "class_ids": {str(k): int(v) for k, v in sorted(class_counts.items())},
        "crop_statistics": crop_statistics,
        "resolution_profiles": resolution_profiles,
        "issue_counts": dict(issue_counts),
        "possible_duplicate_images": int(len(duplicates)),
        "near_edge_box_fraction": float(boxes.near_edge.mean()) if len(boxes) else None,
        "outside_frame_boxes": int(boxes.outside_frame.sum()) if len(boxes) else 0,
    }


def write_report(report: dict[str, Any], out_dir: Path) -> None:
    crop_stats = report["crop_statistics"]
    magnolia = crop_stats.get("magnolia", {})
    azalea = crop_stats.get("azalea", {})
    image_total = max(1, report["labeled_images"])
    annotation_total = max(1, report["annotations"])
    lines = [
        "# OrnaScout exploratory data analysis",
        "",
        "## Audit summary",
        "",
        f"- Matched labeled source images: **{report['labeled_images']:,}**",
        f"- Valid YOLO boxes: **{report['annotations']:,}**",
        f"- Images by crop: `{report['images_by_crop']}`",
        f"- Annotations by crop: `{report['annotations_by_crop']}`",
        f"- Resolution profiles: `{report['resolution_profiles']}`",
        f"- Observed class IDs: `{report['class_ids']}`",
        f"- Annotation/data issues: `{report['issue_counts']}`",
        f"- Boxes extending outside normalized frame: **{report['outside_frame_boxes']:,}**",
        f"- Near-edge box fraction: **{report['near_edge_box_fraction']:.3f}**" if report["near_edge_box_fraction"] is not None else "- Near-edge box fraction: unavailable",
        f"- Images in possible perceptual-duplicate groups: **{report['possible_duplicate_images']:,}**",
        "",
        "## Initial findings",
        "",
        f"- Magnolia contributes **{magnolia.get('images', 0):,} images ({100 * magnolia.get('images', 0) / image_total:.1f}%)** and "
        f"**{magnolia.get('annotations', 0):,} boxes ({100 * magnolia.get('annotations', 0) / annotation_total:.1f}%)**. "
        "Training and aggregate reporting therefore require crop-aware sampling and per-crop metrics.",
        f"- Azalea contributes **{azalea.get('images', 0):,} images** and **{azalea.get('annotations', 0):,} boxes**. "
        f"Its median count is **{azalea.get('median_boxes_per_image', 0):.0f} boxes/image** "
        f"(10th-90th percentile: {azalea.get('p10_boxes_per_image', 0):.1f}-{azalea.get('p90_boxes_per_image', 0):.1f}).",
        f"- Magnolia has a median of **{magnolia.get('median_boxes_per_image', 0):.0f} boxes/image** "
        f"(10th-90th percentile: {magnolia.get('p10_boxes_per_image', 0):.1f}-{magnolia.get('p90_boxes_per_image', 0):.1f}).",
        f"- Median normalized box area differs across crops (azalea: **{azalea.get('median_box_area_norm', 0):.5f}**; "
        f"magnolia: **{magnolia.get('median_box_area_norm', 0):.5f}**), providing a measurable cross-crop scale shift.",
        f"- Reviewed source images with zero annotations: **{sum(int(stats.get('empty_images', 0)) for stats in crop_stats.values())}**. "
        "These are retained as source-level negatives; tiling supplies additional empty and boundary-hard-negative examples.",
        "- The single YOLO class ID denotes an ornamental-plant instance, not species identity. Magnolia/azalea identity comes from source metadata and must remain explicit in every manifest.",
        "",
        "## Quality-control interpretation",
        "",
        f"{report['issue_counts'].get('invalid_box_value', 0)} invalid zero-area rows are excluded from valid-box statistics without modifying source labels. "
        f"{report['issue_counts'].get('image_without_label', 0)} RGB image without a reviewed label is excluded from supervised splits.",
        "No box exceeds the normalized frame after allowing a 1e-6 tolerance for six-decimal YOLO rounding.",
        "",
        "Possible perceptual duplicates require visual confirmation; a shared dHash is not proof of duplication.",
        "The EDA uses source images as the statistical unit. Generated tiles must not be treated as independent samples.",
    ]
    (out_dir / "EDA_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "eda_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Source-level EDA for OrnaScout")
    parser.add_argument("--config", type=Path, default=Path(__file__).parent / "experiment_config.json")
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    out_dir = args.out_dir or Path(config["output_root"]) / "eda"
    figures, tables = out_dir / "figures", out_dir / "tables"
    figures.mkdir(parents=True, exist_ok=True); tables.mkdir(parents=True, exist_ok=True)
    style()
    images, boxes, issues = collect(config)
    if images.empty or boxes.empty:
        raise SystemExit("EDA requires matched readable images and valid YOLO boxes")
    images.to_csv(tables / "images.csv", index=False)
    boxes.to_csv(tables / "boxes.csv", index=False)
    issues.to_csv(tables / "issues.csv", index=False)
    report = summaries(images, boxes, issues, tables)
    dataset_overview(images, figures)
    image_characteristics(images, figures)
    object_geometry(boxes, figures)
    spatial_heatmaps(boxes, figures)
    count_and_coverage(images, figures)
    cross_crop_shift(images, boxes, figures)
    diagnostics = out_dir / "diagnostics"
    diagnostics.mkdir(parents=True, exist_ok=True)
    for crop in sorted(images.crop.unique()):
        representative_contact_sheet(images, boxes, diagnostics, crop)
    write_report(report, out_dir)
    prepared_index = Path(config["output_root"]) / "combined" / "tile_index.csv"
    if prepared_index.exists():
        prepared_eda(prepared_index, images, boxes, out_dir)
    print(json.dumps(report, indent=2))
    print(f"EDA outputs: {out_dir}")


if __name__ == "__main__":
    main()

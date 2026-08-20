#!/usr/bin/env python3
"""Generate a publication-ready OrnaScout architecture as SVG, PNG, and PDF."""

from __future__ import annotations

import base64
import csv
import html
import io
import subprocess
from pathlib import Path

from PIL import Image, ImageEnhance


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs" / "wacv" / "paper_figures"
WIDTH, HEIGHT = 2800, 1300
FONT_FAMILY = "Helvetica, Arial, sans-serif"


def representative_images(index_path: Path, count: int = 2) -> list[Path]:
    with index_path.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row["split"] == "train"]
    if not rows:
        raise RuntimeError(f"No training images found in {index_path}")

    # Preserve real acquisition diversity when a crop has multiple source roots.
    groups: dict[Path, list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault(Path(row["image_path"]).parent, []).append(row)
    selected: list[Path] = []
    for group in groups.values():
        group.sort(key=lambda row: int(row["n_boxes"]))
        selected.append(Path(group[len(group) // 2]["image_path"]))
        if len(selected) == count:
            return selected

    rows.sort(key=lambda row: int(row["n_boxes"]))
    quantiles = (0.52, 0.82) if count == 2 else tuple((i + 1) / (count + 1) for i in range(count))
    for quantile in quantiles:
        candidate = Path(rows[min(len(rows) - 1, round(quantile * (len(rows) - 1)))]["image_path"])
        if candidate not in selected:
            selected.append(candidate)
        if len(selected) == count:
            break
    return selected


def image_uri(path: Path, crop: tuple[float, float, float, float] | None = None) -> str:
    image = Image.open(path).convert("RGB")
    if crop:
        width, height = image.size
        left, top, right, bottom = crop
        image = image.crop((int(left * width), int(top * height), int(right * width), int(bottom * height)))
    image.thumbnail((720, 520), Image.Resampling.LANCZOS)
    image = ImageEnhance.Sharpness(image).enhance(1.08)
    stream = io.BytesIO()
    image.save(stream, format="JPEG", quality=91, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(stream.getvalue()).decode("ascii")


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def multiline(x: float, y: float, lines: list[str], size: int, weight: int = 400,
              fill: str = "#1d2530", anchor: str = "middle", leading: float = 1.18) -> str:
    spans = []
    for index, line in enumerate(lines):
        dy = 0 if index == 0 else size * leading
        spans.append(f'<tspan x="{x}" dy="{dy}">{esc(line)}</tspan>')
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT_FAMILY}" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{"".join(spans)}</text>'
    )


def container(x: int, y: int, w: int, h: int, label: str, accent: str = "#344b5f") -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="28" fill="#ffffff" '
        f'stroke="{accent}" stroke-width="2.2" stroke-dasharray="10 7"/>'
        f'<rect x="{x + 22}" y="{y - 18}" width="{max(210, len(label) * 13)}" height="36" rx="8" '
        f'fill="#ffffff" stroke="none"/>'
        f'{multiline(x + 34, y + 7, [label], 27, 700, accent, "start")}'
    )


def module(x: int, y: int, w: int, h: int, title: str, body: list[str],
           fill: str, stroke: str, number: str | None = None, dashed: bool = False) -> str:
    dash = ' stroke-dasharray="8 6"' if dashed else ""
    title_text = f"{number}. {title}" if number else title
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="15" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="2.2"{dash}/>'
        f'{multiline(x + w / 2, y + 40, [title_text], 22, 700)}'
        f'{multiline(x + w / 2, y + 78, body, 17, 400, "#313a45", leading=1.12)}'
    )


def image_stack_panel(x: int, y: int, w: int, h: int, label: str,
                      uris: list[str], clip_id: str) -> str:
    card_w = 165
    card_h = h - 16
    x_positions = (x, x + w - card_w)
    y_positions = (y + 12, y)
    parts = [multiline(x + w / 2, y - 25, [label], 22, 700)]
    for index, uri in enumerate(uris[:2]):
        image_x = x_positions[index]
        image_y = y_positions[index]
        clip = f"{clip_id}-{index}"
        parts.append(
            f'<rect x="{image_x}" y="{image_y}" width="{card_w}" height="{card_h}" '
            f'fill="#ffffff" stroke="#20272e" stroke-width="2" filter="url(#shadow)"/>'
            f'<clipPath id="{clip}"><rect x="{image_x + 4}" y="{image_y + 4}" '
            f'width="{card_w - 8}" height="{card_h - 8}"/></clipPath>'
        )
        parts.append(
            f'<image x="{image_x + 4}" y="{image_y + 4}" width="{card_w - 8}" height="{card_h - 8}" '
            f'preserveAspectRatio="xMidYMid slice" clip-path="url(#{clip})" href="{uri}"/>'
        )
    return "".join(parts)


def arrow(points: list[tuple[float, float]], dashed: bool = False) -> str:
    path = " ".join(("M" if index == 0 else "L") + f" {x} {y}" for index, (x, y) in enumerate(points))
    marker = "arrow-dashed" if dashed else "arrow"
    dash = ' stroke-dasharray="9 7"' if dashed else ""
    return (
        f'<path d="{path}" fill="none" stroke="#263746" stroke-width="2.6" '
        f'stroke-linejoin="round" stroke-linecap="square" marker-end="url(#{marker})"{dash}/>'
    )


def connector(points: list[tuple[float, float]], dashed: bool = False) -> str:
    path = " ".join(("M" if index == 0 else "L") + f" {x} {y}" for index, (x, y) in enumerate(points))
    dash = ' stroke-dasharray="9 7"' if dashed else ""
    return (
        f'<path d="{path}" fill="none" stroke="#263746" stroke-width="2.4" '
        f'stroke-linejoin="round" stroke-linecap="square"{dash}/>'
    )


def junction(x: float, y: float) -> str:
    return f'<circle cx="{x}" cy="{y}" r="4" fill="#263746"/>'


def pill(x: int, y: int, w: int, text: str, fill: str, stroke: str) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="42" rx="9" fill="{fill}" stroke="{stroke}" stroke-width="1.7"/>'
        f'{multiline(x + w / 2, y + 27, [text], 17, 600)}'
    )


def build_svg(magnolia: list[Path], azalea: list[Path]) -> str:
    magnolia_uris = [image_uri(path) for path in magnolia]
    azalea_uris = [image_uri(path) for path in azalea]
    tile_uris = [
        image_uri(magnolia[0], (0.05, 0.10, 0.47, 0.55)),
        image_uri(magnolia[-1], (0.45, 0.35, 0.87, 0.80)),
        image_uri(azalea[0], (0.20, 0.08, 0.62, 0.53)),
    ]

    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="9.8" refY="5" markerWidth="7" markerHeight="7" orient="auto" markerUnits="strokeWidth">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="#263746"/>
  </marker>
  <marker id="arrow-dashed" viewBox="0 0 10 10" refX="9.8" refY="5" markerWidth="7" markerHeight="7" orient="auto" markerUnits="strokeWidth">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="#263746"/>
  </marker>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="3" stdDeviation="3" flood-opacity="0.12"/></filter>
</defs>
<rect width="100%" height="100%" fill="#ffffff"/>
''']

    parts += [
        container(45, 95, 400, 735, "A. Cross-crop UAV inputs", "#315c73"),
        container(485, 95, 395, 735, "B. Source-safe preparation", "#315c73"),
        container(920, 95, 1325, 735, "C. OrnaScout inference", "#28715f"),
        container(2285, 95, 470, 735, "D. Selective reliability", "#7a5710"),
        container(485, 885, 2270, 245, "E. Evaluation protocol", "#5e6873"),
        image_stack_panel(100, 185, 290, 225, "Magnolia RGB", magnolia_uris, "input-mag"),
        image_stack_panel(100, 535, 290, 225, "Azalea RGB", azalea_uris, "input-aza"),
    ]

    # Source-safe preparation.
    parts += [
        module(555, 190, 255, 130, "Source-image split", ["train / validation / test", "before any tiling"], "#eaf2f7", "#315c73", "1"),
        module(555, 395, 255, 130, "Overlapping tiling", ["1024 px default", "25% overlap"], "#eaf2f7", "#315c73", "2"),
        module(555, 635, 255, 120, "YOLO supervision", ["one-class boxes", "training partitions only"], "#fff6d8", "#a87500", None, True),
        connector([(390, 298), (465, 298), (465, 255)]),
        connector([(390, 648), (465, 648), (465, 255)]),
        junction(465, 255),
        arrow([(465, 255), (555, 255)]),
        arrow([(682, 320), (682, 395)]),
    ]

    # Main inference path.
    parts += [
        module(970, 190, 205, 160, "Detector evidence", ["plant confidence", "predicted count"], "#eef1f3", "#596875", "3"),
        module(1225, 190, 225, 160, "Budgeted selector", ["evidence-ranked", "exploitation + exploration"], "#e8f6ef", "#28715f", "4"),
        module(1775, 190, 190, 160, "VLM model adapter", ["structured", "visual reasoning"], "#eef1f3", "#596875", "5"),
        module(2010, 190, 185, 160, "Schema decoder", ["fixed JSON schema", "model-agnostic parsing"], "#eee9f7", "#71519a", "6"),
        arrow([(810, 460), (900, 460), (900, 270), (970, 270)]),
        arrow([(1175, 270), (1225, 270)]),
        arrow([(1450, 270), (1500, 270)]),
        arrow([(1725, 270), (1775, 270)]),
        arrow([(1965, 270), (2010, 270)]),
        arrow([(810, 695), (940, 695), (940, 310), (970, 310)], True),
    ]

    # Selected real evidence tiles.
    parts.append(f'<rect x="1500" y="150" width="225" height="240" rx="15" fill="#ffffff" stroke="#28715f" stroke-width="2.2"/>')
    parts.append(multiline(1612, 180, ["Selected evidence tiles"], 19, 700))
    for index, uri in enumerate(tile_uris):
        x = 1518 + index * 54
        y = 210 + index * 30
        clip = f"tile-{index}"
        parts.append(f'<clipPath id="{clip}"><rect x="{x}" y="{y}" width="92" height="72" rx="4"/></clipPath>')
        parts.append(f'<rect x="{x}" y="{y}" width="92" height="72" rx="4" fill="#fff" stroke="#263746" stroke-width="1.5"/>')
        parts.append(f'<image x="{x + 2}" y="{y + 2}" width="88" height="68" preserveAspectRatio="xMidYMid slice" clip-path="url(#{clip})" href="{uri}"/>')
    parts.append(multiline(1612, 370, ["equal VLM-call budget"], 16, 500, "#54606a"))

    # Adapter bank and proposed components.
    parts += [
        multiline(1000, 460, ["VLM adapters (one per run)"], 21, 700, "#263746", "start"),
        pill(970, 485, 205, "SmolVLM2-500M", "#f1f3f5", "#596875"),
        pill(1190, 485, 205, "SmolVLM2-2.2B", "#f1f3f5", "#596875"),
        pill(970, 545, 205, "Phi-3.5-Vision", "#f1f3f5", "#596875"),
        pill(1190, 545, 205, "LLaVA-1.5-7B", "#f1f3f5", "#596875"),
        module(1480, 475, 300, 155, "Task record", ["presence, count bin, density, coverage", "with selected-tile provenance"], "#eee9f7", "#71519a"),
        module(1840, 475, 330, 155, "Reliability evidence*", ["schema validity + repeat consistency", "detector agreement + confidence"], "#e8f6ef", "#28715f"),
        arrow([(2102, 350), (2102, 430), (1630, 430), (1630, 475)]),
        arrow([(1780, 552), (1840, 552)]),
    ]

    # Reliability branch, all straight vertical connectors.
    parts += [
        module(2350, 180, 340, 150, "Failure-risk gate*", ["fit on validation outcomes", "threshold frozen before test"], "#e8f6ef", "#28715f", "7"),
        module(2315, 430, 185, 135, "Accept", ["retain record", "and provenance"], "#edf6ee", "#3b7a43"),
        module(2540, 430, 185, 135, "Human review", ["route uncertain or", "inconsistent cases"], "#fff2df", "#a35f12"),
        arrow([(2170, 552), (2260, 552), (2260, 255), (2350, 255)]),
        connector([(2520, 330), (2520, 385)]),
        junction(2520, 385),
        arrow([(2520, 385), (2407, 385), (2407, 430)]),
        arrow([(2520, 385), (2632, 385), (2632, 430)]),
    ]

    # Evaluation band.
    parts += [
        multiline(540, 955, ["Cross-crop protocols"], 22, 700, "#263746", "start"),
        pill(540, 985, 135, "M→M", "#eef4f8", "#315c73"),
        pill(690, 985, 135, "A→A", "#eef4f8", "#315c73"),
        pill(840, 985, 135, "M→A", "#eef4f8", "#315c73"),
        pill(990, 985, 135, "A→M", "#eef4f8", "#315c73"),
        pill(1140, 985, 155, "pooled", "#eef4f8", "#315c73"),
        multiline(540, 1068, ["Source-image-clustered 95% confidence intervals"], 17, 500, "#4c5762", "start"),
        multiline(1370, 955, ["Reliability and efficiency"], 22, 700, "#263746", "start"),
        pill(1370, 985, 185, "task macro-F1", "#f1f3f5", "#596875"),
        pill(1570, 985, 175, "schema validity", "#f1f3f5", "#596875"),
        pill(1760, 985, 175, "risk / coverage", "#f1f3f5", "#596875"),
        pill(1950, 985, 185, "latency / memory", "#f1f3f5", "#596875"),
        multiline(1370, 1068, ["Verified-negative hallucination; AURC; false-accept rate"], 17, 500, "#4c5762", "start"),
        multiline(2200, 955, ["Ablations"], 22, 700, "#263746", "start"),
        pill(2200, 985, 155, "selector", "#fff6d8", "#a87500"),
        pill(2370, 985, 155, "gate signals", "#fff6d8", "#a87500"),
        pill(2540, 985, 155, "tile budget", "#fff6d8", "#a87500"),
        multiline(2200, 1068, ["tile size · overlap · exploration · repeats"], 17, 500, "#4c5762", "start"),
    ]

    # Legend and provenance.
    parts += [
        arrow([(90, 1185), (185, 1185)]),
        multiline(205, 1191, ["test-time path"], 16, 500, "#4c5762", "start"),
        arrow([(90, 1225), (185, 1225)], True),
        multiline(205, 1231, ["training / calibration only"], 16, 500, "#4c5762", "start"),
        multiline(2705, 1118, ["* proposed OrnaScout components"], 16, 700, "#28715f", "end"),
        '</svg>',
    ]
    return "".join(parts)


def main() -> None:
    magnolia = representative_images(ROOT / "outputs/wacv/magnolia/image_index.csv")
    azalea = representative_images(ROOT / "outputs/wacv/azalea/image_index.csv")
    OUT.mkdir(parents=True, exist_ok=True)
    svg_path = OUT / "01_method_architecture.svg"
    png_path = OUT / "01_method_architecture.png"
    pdf_path = OUT / "01_method_architecture.pdf"
    svg_path.write_text(build_svg(magnolia, azalea), encoding="utf-8")
    subprocess.run(["rsvg-convert", "-w", "5600", "-h", "2600", str(svg_path), "-o", str(png_path)], check=True)
    subprocess.run(["rsvg-convert", "-f", "pdf", str(svg_path), "-o", str(pdf_path)], check=True)
    print(svg_path)
    print(png_path)
    print(pdf_path)


if __name__ == "__main__":
    main()

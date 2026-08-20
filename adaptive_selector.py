#!/usr/bin/env python3
"""Select adaptive, uniform, or random tiles under one fixed image budget."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def read(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--detector", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--budget", type=int, default=8)
    p.add_argument("--exploration", type=float, default=0.25)
    p.add_argument("--strategy", choices=["adaptive", "uniform", "random"], default="adaptive")
    p.add_argument("--split", choices=["train", "val", "test"])
    p.add_argument("--seed", type=int, default=2026)
    args = p.parse_args()
    evidence = {r["tile_id"]: r for r in read(args.detector)}
    by_image = defaultdict(list)
    for row in read(args.manifest):
        if args.split is not None and row.get("split") != args.split:
            continue
        image_id = row["tile_id"].rsplit("_t", 1)[0]
        e = evidence.get(row["tile_id"], {})
        score = float(e.get("detector_confidence", 0)) + min(float(e.get("detector_count", 0)), 20) / 20
        by_image[image_id].append((score, row))
    if not by_image:
        suffix = f" for split {args.split!r}" if args.split else ""
        raise SystemExit(f"No candidate tiles found{suffix}")
    rng = random.Random(args.seed)
    selected = []
    for items in by_image.values():
        budget = min(args.budget, len(items))
        spatial = sorted(items, key=lambda x: x[1]["tile_id"])
        if args.strategy == "random":
            chosen = rng.sample(spatial, budget)
        elif args.strategy == "uniform":
            if budget == 1:
                chosen = [spatial[len(spatial) // 2]]
            else:
                indices = [round(i * (len(spatial) - 1) / (budget - 1)) for i in range(budget)]
                chosen = [spatial[index] for index in indices]
        else:
            ranked = sorted(items, key=lambda x: (-x[0], x[1]["tile_id"]))
            explore_n = min(len(ranked), round(budget * args.exploration))
            exploit_n = budget - explore_n
            chosen = ranked[:exploit_n]
            remaining = ranked[exploit_n:]
            chosen.extend(rng.sample(remaining, min(explore_n, len(remaining))))
        selected.extend(row for _, row in chosen)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in sorted(selected, key=lambda x: x["tile_id"]):
            handle.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()

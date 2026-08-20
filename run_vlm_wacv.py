#!/usr/bin/env python3
"""Run one registered VLM without silently repairing malformed outputs."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from model_adapters import load_adapter


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--models", type=Path, default=Path(__file__).parent / "configs" / "models.json")
    p.add_argument("--model", required=True)
    p.add_argument("--run-name")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--split", choices=["train", "val", "test", "all"], default="test")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--limit", type=int)
    p.add_argument("--max-new-tokens", type=int, default=160)
    p.add_argument("--device", default="auto")
    p.add_argument("--dtype", choices=["auto", "float16", "bfloat16", "float32"], default="auto")
    p.add_argument("--peft-adapter", type=Path)
    p.add_argument("--single-image-patch", action="store_true")
    p.add_argument("--phi-num-crops", type=int, default=4)
    args = p.parse_args()

    try:
        import psutil
    except ImportError as exc:
        raise SystemExit("Install requirements.txt before VLM inference") from exc

    registry = json.loads(args.models.read_text(encoding="utf-8"))
    if args.model not in registry:
        raise SystemExit(f"Unknown model: {args.model}; choose from {sorted(registry)}")
    config = registry[args.model]
    if args.phi_num_crops < 1:
        raise SystemExit("--phi-num-crops must be at least 1")
    adapter = load_adapter(config, args.device, args.dtype, args.phi_num_crops)
    if args.single_image_patch and hasattr(adapter.processor, "image_processor"):
        image_processor = adapter.processor.image_processor
        if hasattr(image_processor, "do_image_splitting"):
            image_processor.do_image_splitting = False
        if hasattr(image_processor, "size") and isinstance(image_processor.size, dict):
            image_processor.size = {"longest_edge": 384}
    if args.peft_adapter:
        from peft import PeftModel
        adapter.model = PeftModel.from_pretrained(adapter.model, str(args.peft_adapter))
        adapter.model.eval()
    rows = [r for r in read_jsonl(args.manifest) if args.split == "all" or r["split"] == args.split]
    if args.limit is not None:
        rows = rows[: args.limit]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    process = psutil.Process(os.getpid())
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            for repeat in range(args.repeats):
                started = time.perf_counter()
                output = adapter.generate(row["image_path"], row["prompt"], args.max_new_tokens, args.repeats > 1)
                latency = (time.perf_counter() - started) * 1000
                record = {
                    "tile_id": row["tile_id"], "model": args.run_name or args.model,
                    "model_id": config["model_id"], "repeat": repeat, "prediction": output,
                    "latency_ms": round(latency, 3),
                    "peak_memory_mb": round(process.memory_info().rss / 1024**2, 3),
                    "device": adapter.device.type, "dtype": str(adapter.dtype).replace("torch.", ""),
                    "phi_num_crops": args.phi_num_crops if config["adapter_type"] == "phi35" else None,
                }
                handle.write(json.dumps(record, ensure_ascii=True) + "\n")
                handle.flush()


if __name__ == "__main__":
    main()

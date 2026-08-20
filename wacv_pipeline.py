#!/usr/bin/env python3
"""Single entry point for OrnaScout preparation, inference, and evaluation."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = Path(os.environ.get("ORNA_CONFIG", HERE / "experiment_config.json")).expanduser()
MODELS = ["smolvlm2_500m", "smolvlm2_2p2b", "phi35_vision", "llava15_7b"]
PHI_ENV = Path(os.environ.get(
    "ORNA_PHI_ENV",
    Path.home() / ".cache" / "ornascout" / "phi35-vision",
))
PHI_PYTHON = PHI_ENV / "bin" / "python"


def run(*parts: object) -> None:
    command = [str(x) for x in parts]
    print("+", " ".join(command), flush=True)
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from None


def settings() -> tuple[dict, Path]:
    if not CONFIG.exists():
        raise SystemExit(
            f"Configuration not found: {CONFIG}. Copy "
            "experiment_config.example.json to experiment_config.json and set "
            "the local image and label paths, or define ORNA_CONFIG."
        )
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    return cfg, Path(cfg["output_root"])


def prediction_files(root: Path, scope: str, split: str) -> list[Path]:
    return sorted(
        path for path in (root / "predictions").glob(f"*_{scope}_{split}.jsonl")
        if not path.name.startswith(("detector_", "._"))
    )


def inference_python(model: str) -> Path:
    if model != "phi35_vision":
        return Path(sys.executable)
    if not PHI_PYTHON.exists():
        raise SystemExit(
            "Phi-3.5-Vision requires its official Transformers 4.43 runtime. "
            "Create it once with: python wacv_pipeline.py setup-phi"
        )
    return PHI_PYTHON


def phi_bootstrap_python(requested: Path | None) -> Path:
    candidates = [
        requested,
        Path(shutil.which("python3.11")) if shutil.which("python3.11") else None,
        Path.home() / "miniconda3" / "envs" / "ornascout" / "bin" / "python",
        Path.home() / "miniconda3" / "envs" / "geoai" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate is not None and candidate.exists():
            return candidate
    raise SystemExit(
        "Phi setup requires Python 3.10 or 3.11. Pass it explicitly with "
        "--python /path/to/python3.11."
    )


def infer(model: str, scope: str, split: str, repeats: int, limit: int | None,
          device: str, manifest: Path | None = None, adapter: Path | None = None,
          max_new_tokens: int | None = None, phi_num_crops: int = 4,
          run_tag: str | None = None) -> None:
    _, root = settings()
    manifest = manifest or root / scope / "inference_manifest.jsonl"
    method = manifest.stem.replace("selected_", "", 1) if manifest.name.startswith("selected_") else "all_tiles"
    adaptation = f"_{adapter.name}" if adapter else "_zeroshot"
    run_name = f"{model}{adaptation}_{method}"
    if run_tag:
        run_name = f"{run_name}_{run_tag}"
    out = root / "predictions" / f"{run_name}_{scope}_{split}.jsonl"
    cmd: list[object] = [
        inference_python(model), HERE / "run_vlm_wacv.py", "--manifest", manifest,
        "--model", model, "--run-name", run_name, "--split", split, "--repeats", repeats,
        "--device", device, "--out", out,
    ]
    if limit is not None:
        cmd.extend(["--limit", limit])
    if max_new_tokens is not None:
        cmd.extend(["--max-new-tokens", max_new_tokens])
    if model == "phi35_vision":
        cmd.extend(["--phi-num-crops", phi_num_crops])
    if adapter is not None:
        cmd.extend(["--peft-adapter", adapter])
    run(*cmd)


def evaluate(scope: str, split: str) -> None:
    cfg, root = settings()
    predictions = [
        p for p in prediction_files(root, scope, split)
        if p.exists() and p.stat().st_size and "_smoke_" not in p.name
    ]
    if not predictions:
        raise SystemExit(f"No {split} predictions found for {scope}")
    command: list[object] = [
        sys.executable, HERE / "ornascout_pipeline_v2.py", "evaluate",
        "--ground-truth", root / scope / "ground_truth.jsonl",
        "--predictions", *predictions,
        "--out-dir", root / "evaluation" / scope / split,
        "--seed", cfg.get("seed", 2026),
    ]
    detector = root / "predictions" / f"detector_{scope}_{split}.jsonl"
    if detector.exists():
        command.extend(["--detector-evidence", detector])
    run(*command)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="OrnaScout WACV reproducible launcher")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect"); sub.add_parser("eda"); sub.add_parser("prepare")
    setup_phi = sub.add_parser("setup-phi")
    setup_phi.add_argument("--python", type=Path)
    sub.add_parser("audit-labels"); sub.add_parser("summarize-audit")
    train_vlm = sub.add_parser("train-vlm"); train_vlm.add_argument("--scope", choices=["magnolia", "azalea", "combined"], required=True)
    export = sub.add_parser("detector-export"); export.add_argument("--scope", required=True)
    train = sub.add_parser("detector-train")
    train.add_argument("--scope", required=True)
    train.add_argument("--epochs", type=int, default=100)
    train.add_argument("--image-size", type=int, default=1024)
    train.add_argument("--batch", type=int, default=8)
    train.add_argument("--device", choices=["auto", "cpu", "mps"], default="auto")
    train.add_argument("--workers", type=int, default=2)
    train.add_argument("--cache", choices=["false", "disk", "ram"], default="false")
    train.add_argument("--patience", type=int, default=20)
    train.add_argument("--name")
    predict = sub.add_parser("detector-predict"); predict.add_argument("--scope", required=True); predict.add_argument("--weights", type=Path, required=True); predict.add_argument("--split", default="test"); predict.add_argument("--image-size", type=int, default=1024); predict.add_argument("--device", choices=["auto", "cpu", "mps"], default="auto")
    select = sub.add_parser("select"); select.add_argument("--scope", required=True); select.add_argument("--split", default="test"); select.add_argument("--budget", type=int, default=8); select.add_argument("--exploration", type=float, default=0.25); select.add_argument("--strategy", choices=["adaptive", "uniform", "random"], default="adaptive")
    smoke = sub.add_parser("smoke"); smoke.add_argument("--scope", default="combined"); smoke.add_argument("--model", choices=MODELS); smoke.add_argument("--device", default="auto")
    smoke_report = sub.add_parser("smoke-report"); smoke_report.add_argument("--scope", default="combined"); smoke_report.add_argument("--split", default="test")
    full = sub.add_parser("infer"); full.add_argument("--scope", required=True); full.add_argument("--model", choices=MODELS); full.add_argument("--split", choices=["val", "test"], default="test"); full.add_argument("--repeats", type=int, default=3); full.add_argument("--device", default="auto"); full.add_argument("--selection", choices=["all", "adaptive", "uniform", "random"], default="all"); full.add_argument("--budget", type=int, default=8); full.add_argument("--exploration", type=float, default=0.25); full.add_argument("--adapter", type=Path); full.add_argument("--phi-num-crops", type=int, choices=[1, 4, 16], default=4)
    ev = sub.add_parser("evaluate"); ev.add_argument("--scope", required=True); ev.add_argument("--split", choices=["val", "test"], required=True)
    gate = sub.add_parser("gate"); gate.add_argument("--calibration-scope", required=True); gate.add_argument("--test-scope", required=True); gate.add_argument("--target-risk", type=float, default=0.10)
    return p


def main() -> None:
    args = parser().parse_args()
    cfg, root = settings()
    if args.command == "inspect":
        run(sys.executable, HERE / "run_experiment.py", "--config", CONFIG, "inspect")
    elif args.command == "eda":
        run(sys.executable, HERE / "exploratory_data_analysis.py", "--config", CONFIG)
    elif args.command == "prepare":
        run(sys.executable, HERE / "run_experiment.py", "--config", CONFIG, "prepare-all")
    elif args.command == "setup-phi":
        bootstrap = phi_bootstrap_python(args.python)
        run(bootstrap, "-m", "venv", PHI_ENV)
        run(PHI_PYTHON, "-m", "pip", "install", "--upgrade", "pip")
        run(PHI_PYTHON, "-m", "pip", "install", "-r", HERE / "requirements-phi.txt")
    elif args.command == "audit-labels":
        run(sys.executable, HERE / "annotation_quality_audit.py", "prepare",
            "--eda-tables", root / "eda" / "tables",
            "--out-dir", root / "annotation_audit",
            "--seed", cfg.get("seed", 2026))
    elif args.command == "summarize-audit":
        run(sys.executable, HERE / "annotation_quality_audit.py", "summarize",
            "--out-dir", root / "annotation_audit")
    elif args.command == "train-vlm":
        run(sys.executable, HERE / "run_experiment.py", "train", "--scope", args.scope)
    elif args.command == "detector-export":
        run(sys.executable, HERE / "detector_evidence.py", "export",
            "--tile-index", root / args.scope / "tile_index.csv",
            "--out-dir", root / "detector_data" / args.scope)
    elif args.command == "detector-train":
        run_name = args.name or args.scope
        run(sys.executable, HERE / "detector_evidence.py", "train",
            "--data", root / "detector_data" / args.scope / "data.yaml",
            "--epochs", args.epochs, "--image-size", args.image_size,
            "--batch", args.batch, "--device", args.device,
            "--workers", args.workers, "--cache", args.cache,
            "--patience", args.patience,
            "--project", root / "detector_runs", "--name", run_name)
    elif args.command == "detector-predict":
        run(sys.executable, HERE / "detector_evidence.py", "predict",
            "--manifest", root / args.scope / "inference_manifest.jsonl",
            "--weights", args.weights, "--split", args.split,
            "--image-size", args.image_size, "--device", args.device,
            "--out", root / "predictions" / f"detector_{args.scope}_{args.split}.jsonl")
    elif args.command == "select":
        run(sys.executable, HERE / "adaptive_selector.py",
            "--manifest", root / args.scope / "inference_manifest.jsonl",
            "--detector", root / "predictions" / f"detector_{args.scope}_{args.split}.jsonl",
            "--split", args.split,
            "--budget", args.budget, "--exploration", args.exploration, "--strategy", args.strategy,
            "--out", root / args.scope / f"selected_{args.strategy}_{args.split}_b{args.budget}_e{round(args.exploration * 100):02d}.jsonl")
    elif args.command == "smoke":
        for model in [args.model] if args.model else MODELS:
            infer(
                model, args.scope, "test", 1, 1, args.device,
                max_new_tokens=8, phi_num_crops=1, run_tag="smoke",
            )
    elif args.command == "smoke-report":
        predictions = [
            path for path in prediction_files(root, args.scope, args.split)
            if path.exists() and path.stat().st_size and "_smoke_" in path.name
        ]
        if not predictions:
            raise SystemExit(f"No smoke prediction files found for {args.scope}/{args.split}")
        run(
            sys.executable, HERE / "make_figures.py", "smoke",
            "--predictions", *predictions,
            "--ground-truth", root / args.scope / "ground_truth.jsonl",
            "--out-dir", root / "figures" / args.scope / "smoke",
        )
    elif args.command == "infer":
        chosen = [args.model] if args.model else MODELS
        selected = root / args.scope / f"selected_{args.selection}_{args.split}_b{args.budget}_e{round(args.exploration * 100):02d}.jsonl" if args.selection != "all" else None
        for model in chosen:
            if args.adapter and model not in {"smolvlm2_500m", "smolvlm2_2p2b"}:
                raise SystemExit("The current LoRA training path is restricted to SmolVLM2.")
            infer(
                model, args.scope, args.split, args.repeats, None, args.device,
                selected, args.adapter, phi_num_crops=args.phi_num_crops,
            )
    elif args.command == "evaluate":
        evaluate(args.scope, args.split)
    elif args.command == "gate":
        run(sys.executable, HERE / "selective_gate.py",
            "--calibration", root / "evaluation" / args.calibration_scope / "val" / "per_tile_evaluation.csv",
            "--test", root / "evaluation" / args.test_scope / "test" / "per_tile_evaluation.csv",
            "--target-risk", args.target_risk,
            "--out", root / "evaluation" / args.test_scope / f"selective_from_{args.calibration_scope}.csv")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fit one validation-only failure gate per VLM and apply it to test rows."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

FEATURES = ["schema_score", "consistency_score", "detector_agreement", "gate_score"]
CORRECT = ["plant_presence_correct", "count_bin_correct", "density_class_correct", "coverage_class_correct"]


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def matrix(items: list[dict]) -> Any:
    import numpy as np

    return np.asarray([[float(row.get(key) or "nan") for key in FEATURES] for row in items], dtype=float)


def is_correct(row: dict) -> int:
    return int(all(int(row[key]) == 1 for key in CORRECT))


def by_model(items: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in items:
        grouped[row["model"]].append(row)
    return grouped


def threshold_at_risk(risk: Any, errors: Any, target: float) -> float:
    import numpy as np

    threshold = -1.0
    for candidate in sorted(set(float(value) for value in risk)):
        accepted = np.flatnonzero(risk <= candidate)
        if len(accepted) and float(errors[accepted].mean()) <= target:
            threshold = candidate
    return threshold


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--target-risk", type=float, default=0.10)
    args = parser.parse_args()

    try:
        import numpy as np
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
    except ImportError as exc:
        raise SystemExit("Install requirements.txt before fitting the selective gate") from exc

    calibration, test = by_model(read_rows(args.calibration)), by_model(read_rows(args.test))
    output: list[dict] = []
    summaries: list[dict] = []
    for model_name, test_rows in sorted(test.items()):
        cal_rows = calibration.get(model_name, [])
        if not cal_rows:
            raise SystemExit(f"No calibration rows for model '{model_name}'")
        errors = np.asarray([1 - is_correct(row) for row in cal_rows])
        if len(set(errors.tolist())) < 2:
            raise SystemExit(f"Calibration outcomes for '{model_name}' contain only one class")
        gate = make_pipeline(
            SimpleImputer(strategy="constant", fill_value=-1),
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=2026),
        )
        gate.fit(matrix(cal_rows), errors)
        calibration_risk = gate.predict_proba(matrix(cal_rows))[:, 1]
        threshold = threshold_at_risk(calibration_risk, errors, args.target_risk)
        test_risk = gate.predict_proba(matrix(test_rows))[:, 1]
        model_output = []
        for row, risk in zip(test_rows, test_risk):
            row["predicted_failure_risk"] = round(float(risk), 6)
            row["selective_decision"] = "accept" if risk <= threshold else "review"
            model_output.append(row)
        output.extend(model_output)
        accepted = [row for row in model_output if row["selective_decision"] == "accept"]
        summaries.append({
            "model": model_name,
            "target_risk": args.target_risk,
            "calibrated_threshold": threshold,
            "test_coverage": len(accepted) / len(model_output),
            "test_selective_accuracy": (
                sum(is_correct(row) for row in accepted) / len(accepted) if accepted else None
            ),
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    args.out.with_suffix(".json").write_text(json.dumps({
        "models": summaries,
        "warning": "Empirical validation calibration; no distribution-free guarantee under crop shift.",
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

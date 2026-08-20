# OrnaScout Technical Project Guide

## 1. Project purpose

OrnaScout studies whether a limited visual-computation budget can be allocated
reliably across a high-resolution UAV image. The system uses detector evidence
to choose a small set of informative image tiles, applies the same selected
evidence to several vision-language models (VLMs), decodes a fixed scouting
record, and refers unreliable records to human review.

The research question is:

> Under a fixed number of VLM calls per source image, can detector-guided tile
> selection and validation-calibrated abstention improve structured prediction
> reliability across Magnolia and Azalea?

The work is not unrestricted image captioning and does not infer disease,
treatment, plant health, or agronomic urgency, because those variables are not
present in the annotations.

## 2. Inputs and outputs

### 2.1 Source inputs

| Input | Magnolia | Azalea |
|---|---|---|
| RGB source images | 297 matched images, 5184 x 3888 | 121 matched images, 5280 x 3956 |
| Reviewed labels | 297 YOLO `.txt` files | 121 YOLO `.txt` files, including three valid empty negatives |
| Usable one-class boxes | 15,644 | 14,198 |
| Active source | `Magnolia_newRGB_review_v3` | original RGB images plus `model_relabeled_review_azalea` labels |

The combined relabeled snapshot contains 418 source images and 29,842 usable
boxes. Five zero-width annotation rows are rejected during preparation without
modifying the reviewed source labels.

### 2.2 YOLO annotation format

Each RGB image must retain a matching annotation file with the same basename:

```text
IMG_0001.JPG
IMG_0001.txt
```

Each line of the `.txt` file is:

```text
class_id x_center y_center width height
```

Coordinates are normalized to `[0,1]`. The current problem uses one class, so
`class_id` is normally `0`. An empty `.txt` file is a valid negative only when a
reviewer has confirmed that the source image contains no labeled target.

Do **not** concatenate every YOLO label into one text file. YOLO requires one
label file per image. OrnaScout creates unified manifests instead:

- `image_index.csv`: one source-image record per row;
- `tile_index.csv`: geometry, split, crop, and derived labels for every tile;
- `ground_truth.jsonl`: evaluation targets;
- `inference_manifest.jsonl`: tile path plus frozen VLM instruction;
- `selected_<strategy>_<split>_b<budget>_e<exploration>.jsonl`: evidence selected
  for a controlled VLM run.

### 2.3 System outputs

The detector produces local boxes, predicted count, and mean confidence. The
Budgeted Evidence Selector produces at most `K` tiles per source image. A VLM is
asked to produce one structured record with these nine fields:

```json
{
  "crop_type": "magnolia | azalea | unknown",
  "plant_presence": "yes | no",
  "count_bin": "0 | 1-5 | 6-15 | 16-30 | >30",
  "density_class": "empty | sparse | moderate | dense",
  "coverage_class": "none | low | medium | high",
  "visual_evidence": "short visible-evidence statement",
  "scouting_priority": "low | medium | high",
  "confidence": 0.0,
  "human_review_needed": "yes | no"
}
```

Only crop identity, presence, count, density, and box-coverage quantities are
derived from the current annotations. Priority and review fields are workflow
outputs and must not be presented as ground-truth agronomic recommendations.

The final selective output is either:

1. an accepted structured record with evidence provenance; or
2. an escalated record routed to human review.

## 3. End-to-end pipeline

### Stage 1: Source-safe preparation

Source images are assigned to train, validation, and test partitions before
tiling. This prevents overlapping tiles from one UAV image from entering more
than one partition. Images are tiled at 1024 pixels with 25% overlap. The active
snapshot contains 10,570 training tiles, 2,030 validation tiles, and 2,030 test
tiles.

### Stage 2: Local detector evidence

A lightweight YOLO11n detector is trained only on training tiles. For tile `t`,
it supplies mean confidence `c_t` and local predicted count `n_t`. The implemented
evidence score is:

```text
q_t = c_t + min(n_t, 20) / 20
```

Count clipping prevents unusually dense tiles from dominating solely because
they contain more predictions.

### Stage 3: Budgeted Evidence Selector

For the default budget `K=8` and exploration fraction `rho=0.25`, six tiles are
selected by evidence score and two are sampled from the remaining candidates
with a fixed random seed. Random, spatially uniform, and pure top-K selectors
must receive exactly the same budget for a fair ablation.

### Stage 4: Model-agnostic VLM inference

Every registered VLM receives the same selected images, frozen prompt, output
schema, generation length, and repeat count. Ground-truth `.txt` boxes are not
shown to the VLM during validation or testing. They are used only to train the
detector and score predictions.

### Stage 5: Schema decoding and reliability evidence

The decoder measures raw schema validity rather than silently rewriting a
malformed answer. With repeated generation, the pipeline also measures
categorical consistency. Detector agreement compares the structured presence
and count-bin output with local detector evidence.

### Stage 6: Validation-calibrated selective gate

A failure model is fitted on validation outcomes only. Its threshold is frozen
before test evaluation. Records below the accepted-risk requirement are kept;
the rest are routed to review. This is empirical validation calibration, not a
distribution-free guarantee after crop shift.

## 4. Models in the controlled comparison

| Registry key | Model | Experimental role |
|---|---|---|
| `smolvlm2_500m` | SmolVLM2-500M | Smallest edge-oriented baseline |
| `smolvlm2_2p2b` | SmolVLM2-2.2B | Primary compact VLM |
| `phi35_vision` | Phi-3.5-Vision | Intermediate Microsoft VLM baseline |
| `llava15_7b` | LLaVA-1.5-7B | Larger historical reference, not an edge model |

All four are VLMs because they consume visual and textual inputs. Their language
backbone size does not change the system category to an LLM or SLM. Model IDs
and roles are defined once in `configs/models.json`.

## 5. File map

| File | Responsibility |
|---|---|
| `wacv_pipeline.py` | Single user-facing command launcher |
| `experiment_config.json` | Dataset paths, output path, tiling parameters, seed |
| `configs/models.json` | Frozen model IDs and adapter types |
| `run_experiment.py` | Internal preparation orchestration |
| `ornascout_pipeline_v2.py` | Parsing, source splits, tiling, target derivation, evaluation |
| `exploratory_data_analysis.py` | Source- and tile-level dataset analysis |
| `annotation_quality_audit.py` | Stratified human annotation audit |
| `detector_evidence.py` | Detector export, training, and local evidence inference |
| `adaptive_selector.py` | Adaptive, uniform, and random fixed-budget selectors |
| `model_adapters.py` | SmolVLM2, Phi, and LLaVA loading and generation adapters |
| `run_vlm_wacv.py` | Repeated VLM inference, latency, and process-memory capture |
| `train_smolvlm_lora.py` | SmolVLM2 LoRA adaptation path |
| `selective_gate.py` | Validation-only failure model and frozen test routing |
| `make_figures.py` | Dataset and evaluation figures |
| `make_detector_qualitative.py` | Reproducible detector overlays and confidence field |
| `make_method_architecture.py` | Method architecture assets |
| `EXPERIMENT_PROTOCOL.md` | Required comparison and ablation matrix |
| `FIGURE_PROTOCOL.md` | Paper, supplementary, and diagnostic figure rules |
| `RESULTS_STATUS.md` | Claim ledger separating completed from planned results |

There are no Java source files in the active research pipeline. The executable
implementation is Python, and the paper is LaTeX.

## 6. How the project was built

1. Reviewed Magnolia and Azalea RGB/YOLO pairs were indexed by basename.
2. Invalid rows, macOS resource forks, preview images, and unmatched files were
   excluded without altering the source annotations.
3. Source images were split before overlapping tiling.
4. Tile labels and unified JSONL/CSV manifests were generated.
5. Cross-crop shift and annotation geometry were measured before model fitting.
6. A lightweight detector was trained to produce inspectable local evidence.
7. A fixed-budget exploit-explore selector was implemented around detector
   confidence and clipped local count.
8. Model adapters enforced one task prompt and output schema across four VLMs.
9. Evaluation was designed around task accuracy, raw schema validity,
   hallucination on verified negatives, latency, memory, crop transfer, and
   selective risk.
10. Paper-facing claims were separated from diagnostics through a result ledger
    and figure protocol.

## 7. Reproducible execution order

```bash
cd /path/to/WACV-2026
source .venv/bin/activate

# Audit and prepare
python wacv_pipeline.py inspect
python wacv_pipeline.py prepare
python wacv_pipeline.py eda
python wacv_pipeline.py audit-labels

# Detector
python wacv_pipeline.py detector-export --scope combined
python wacv_pipeline.py detector-train --scope combined --epochs 100

WEIGHTS="outputs/wacv/detector_runs/combined/weights/best.pt"
python wacv_pipeline.py detector-predict --scope combined --split val  --weights "$WEIGHTS" --device mps
python wacv_pipeline.py detector-predict --scope combined --split test --weights "$WEIGHTS" --device mps

# Equal-budget evidence
python wacv_pipeline.py select --scope combined --split val  --strategy adaptive --budget 8 --exploration 0.25
python wacv_pipeline.py select --scope combined --split test --strategy adaptive --budget 8 --exploration 0.25

# Run each model separately; first validate the schema on a small smoke sample.
python wacv_pipeline.py smoke --scope combined --model smolvlm2_500m --device mps
python wacv_pipeline.py infer --scope combined --model smolvlm2_500m --split val \
  --selection adaptive --budget 8 --exploration 0.25 --repeats 1 --device mps

# Evaluation and selective routing
python wacv_pipeline.py evaluate --scope combined --split val
python wacv_pipeline.py evaluate --scope combined --split test
python wacv_pipeline.py gate --calibration-scope combined --test-scope combined --target-risk 0.10
```

Formal model comparisons require identical hardware, precision, generation
length, tile budget, and repeats. Phi uses its isolated official Transformers
runtime created by `python wacv_pipeline.py setup-phi`.

## 8. Current measured status and scientific boundary

### Completed

- Relabeled corpus preparation and source-safe split.
- Preliminary 15-epoch YOLO11n detector at 640-pixel input.
- Preliminary detector validation: precision 0.911, recall 0.905, mAP50 0.965,
  and mAP50-95 0.789.
- Detector evidence for 2,030 validation and 2,030 test tiles.
- Adaptive validation selection at `K=8`, `rho=0.25`.
- One-repeat SmolVLM2-500M validation inference on 464 selected tiles.
- Reproducible detector qualitative figure for one held-out tile per crop.

### Critical unresolved result

The completed SmolVLM2-500M run generated non-JSON text despite the JSON
instruction. Raw schema-valid rate is therefore 0%, and current task F1 values
are not scientifically usable. This is a schema-generation/decoding failure,
not evidence that every task prediction is intrinsically wrong. The output
contract must be corrected and verified on a small sample before expensive
full-model inference is repeated.

### Still required for the WACV result claim

- Finish and summarize the representative annotation audit.
- Correct and verify structured VLM output.
- Run validation and test inference for all registered models.
- Run adaptive, uniform, random, and pure top-K equal-budget comparisons.
- Run budget, exploration, overlap, tile-size, repeat, and gate-signal ablations.
- Fit the gate on validation outcomes and freeze it before test routing.
- Produce Magnolia-to-Azalea, Azalea-to-Magnolia, within-crop, and pooled results.
- Report source-image-clustered confidence intervals and paired differences.
- Measure latency and memory on declared, identical hardware.
- Either evaluate an external nursery dataset or restrict generalization claims
  to the two observed crops and acquisition conditions.

## 9. Definition of experimental success

The project is successful only if it demonstrates, under equal visual budget:

1. detector-guided exploit-explore selection improves a declared task or
   reliability metric over random, uniform, and pure top-K routing;
2. the gain or failure pattern is reported separately for Magnolia and Azalea;
3. unsupported records are rejected at a useful risk-coverage operating point;
4. efficiency is measured rather than inferred from parameter count; and
5. every headline result is computed from frozen validation/test outputs with
   source-image-clustered uncertainty.

Detector accuracy alone, a successful runtime smoke test, or visually appealing
overlays do not establish the paper's central claim.

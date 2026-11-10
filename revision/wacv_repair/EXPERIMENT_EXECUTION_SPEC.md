# Experiment Execution Specification

## A. Data integrity

### Inputs

- frozen source-image inventory;
- raw and reviewed annotations;
- acquisition metadata where available; and
- existing split and tile manifests.

### Checks

1. exact and perceptual duplicate search before splitting;
2. source, sequence, flight, row, and near-neighbor leakage audit;
3. image-label pairing and dimensions;
4. invalid, empty, truncated, and boundary boxes;
5. negative-source verification;
6. class/bin support by train, validation, test, and crop; and
7. cryptographic hashes for all manifests.

### Deliverables

`data_audit.json`, `source_split.csv`, `manifest_hashes.json`, and a human-audit
report with sample size, sampling strata, agreement, adjudication, and
exclusions.

## B. Detector and detector-only system

Run M->M, A->A, M->A, A->M, and pooled protocols. Report AP50:95, precision,
recall, false positives, count error, and recall by object size/density. Build a
deterministic source record from detector outputs for all derivable fields.

This is the minimum baseline against which VLM value is assessed.

## C. Corrected selector study

Policies:

1. random;
2. true 2D spatial/farthest-point;
3. confidence top-K;
4. count top-K;
5. normalized combined top-K;
6. current exploit--explore;
7. diversity-aware exploit--explore;
8. shuffled-score control; and
9. GT oracle for diagnosis only.

Budgets: K in {1, 2, 4, 8, 16}. Exploration rho in {0, .125, .25, .5, .75, 1}
on validation only. Use per-source deterministic seeds and repeated stochastic
runs.

## D. VLM-value experiment

Hold source tests, budget, prompts, schema, and reduction fixed. Compare:

- detector-only;
- deterministic detector aggregation;
- whole-image downsampled VLM;
- spatially uniform tiled VLM;
- best validation-selected evidence policy; and
- evidence policy plus selective gate.

Primary endpoint: source-level exact record or a predeclared inventory utility
score. Secondary endpoints: field metrics, hallucination, review burden, and
cost.

## E. Directed crop transfer

For each training protocol, freeze detector, policy, VLM configuration, source
reducer, and gate without target-test feedback. Report:

- within-domain performance;
- cross-domain performance;
- paired transfer drop;
- detector miss/routing miss decomposition;
- scale/density-stratified diagnostics; and
- risk/coverage under shift.

## F. Selective reliability

### Gate construction

- use source-grouped cross-fitting on validation data;
- generate out-of-fold risk scores;
- select the target-risk threshold from those scores;
- refit only after freezing features and hyperparameters; and
- evaluate test once.

### Baselines

Raw VLM confidence, strict schema-only, detector agreement, equal-weight score,
declared fixed score, and learned gate.

### Outputs

AURC, coverage at target risk, observed accepted risk, false-accept rate,
accepted sources, review rate, and confidence intervals.

## G. Source-level reduction

Implement coordinate-aware count fusion and per-field aggregation. Test:

- duplicate detections across overlapping tiles;
- conflicting tile records;
- malformed records;
- no accepted tiles;
- boundary-truncated instances; and
- crop-specific calibration.

## H. Efficiency

Measure each stage separately and end to end:

- source decoding/tiling;
- detector inference over candidates;
- selection;
- image preparation/transfer;
- VLM generation;
- parsing/gating;
- source reduction; and
- expected human-review workload.

Report hardware, OS, library versions, precision, warm-up, image resolution,
generation length, mean, p50, p95, throughput, peak memory, and model-loading
memory.

## I. Failure analysis

Use a frozen stratified sample and at least two reviewers where feasible.
Taxonomy:

- annotation/data issue;
- detector miss;
- routing miss;
- boundary truncation;
- malformed schema;
- count/density/coverage error;
- unsupported positive;
- source-reduction conflict;
- gate false accept;
- gate false reject; and
- correct abstention.

Report denominator, count, rate, agreement, and adjudication. Select qualitative
examples by the frozen rule rather than visual preference.

## J. Artifact contract

Every run records commit, command, manifest hash, split hash, model and revision,
checkpoint hash, seed, hardware, start/end time, environment, and output hash.
Tables and figures are generated directly from immutable result artifacts.

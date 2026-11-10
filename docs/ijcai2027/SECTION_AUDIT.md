# Section-by-Section Scientific Audit

This audit treats the WACV PDF as the submitted baseline and the reviewer
comments as requirements. It describes what must change before prose is
polished. Unsupported numerical claims must be removed rather than estimated.

## Title

### Current risk

"Reliable Cross-Crop Nursery Monitoring" overstates what was demonstrated.
The submitted paper did not report directed transfer results or useful
risk--coverage operating points.

### Revision

Use a title that describes the verified method unless the missing evidence is
completed. Working title:

> OrnaScout: Fixed-Budget Visual Evidence Allocation with Selective Prediction
> for High-Resolution UAV Imagery

Restore "cross-crop" only if both transfer directions are fully evaluated.
Restore "reliable" only if a validation-fitted gate improves accepted risk at
non-trivial coverage on held-out source images.

## Abstract

### Problems

- Too many dataset statistics obscure the AI contribution.
- Cross-crop reliability is implied without transfer or gate results.
- Selector diagnostics are presented as if they establish end-task value.

### Required structure

1. Operational problem and fixed-budget constraint.
2. Method: evidence allocation, structured prediction, selective decision.
3. Evaluation protocol: source-disjoint crops, detector-only controls, directed
   transfer, and risk--coverage.
4. Two or three verified quantitative findings.
5. One bounded conclusion stating the demonstrated trade-off.

No abstract number may be inserted before the result ledger marks it VERIFIED.

## 1. Introduction

### Problem statement

Define the source-level decision explicitly: input, budget, output fields,
abstention action, and cost. Explain which fields are detector-derived and
which require semantic interpretation. Do not imply health, stress, mortality,
or management recommendations because the dataset contains one-class boxes.

### Why a VLM

The introduction must answer the strongest reviewer question: why is this not
only detection or counting? State a falsifiable hypothesis:

> Under a fixed number of inspected tiles, structured multimodal inference can
> add auditable semantic fields and calibrated abstention beyond detector-only
> aggregation, without sacrificing operationally useful coverage.

If the experiments do not support that hypothesis, narrow the system to
budgeted evidence routing and remove the VLM-value claim.

### Contributions

List only completed contributions. The final list should contain at most three:

1. fixed-budget evidence allocation with equal-cost controls;
2. source-safe directed transfer and source-level evaluation; and
3. selective structured prediction with explicit risk--coverage operating
   points.

Dataset statistics and standard engineering components are not contributions.

## 2. Related Work

Reorganize around four comparison axes rather than a catalogue of models:

1. adaptive region/token selection for high-resolution vision;
2. aerial small-object detection, counting, and sliced inference;
3. selective prediction, abstention, and risk control under shift; and
4. agricultural VLM evaluation and cross-domain generalization.

End each subsection with a precise gap. Add the closest detector-only,
counting, adaptive-computation, and diversity-aware selection methods used as
baselines. Avoid claiming that no prior work exists unless a documented
literature search supports the statement.

## 3. Method

### 3.1 Problem setup and scope

- Define source image, crop domain, candidate tiles, selected set, budget,
  structured target, source-level output, and review action.
- Separate tile-level and source-level targets.
- Define the cost model: detector cost over all tiles, VLM cost over selected
  tiles, reduction cost, and human-review cost.
- State that source splitting occurs before tiling.

### 3.2 Local detector evidence

- Report detector architecture, checkpoint selection, input size, confidence
  threshold, NMS, training schedule, and count clipping.
- Justify `n_max=20` using validation-only sensitivity or remove the arbitrary
  constant.
- Add detector-only predictions for every downstream field that can be derived
  from boxes.
- Quantify detector misses by crop and object-size stratum.

### 3.3 Budgeted Evidence Selector

- Present exploit--explore as one policy in a family, not as the assumed
  winner.
- State the random seed construction and behavior when fewer than K candidates
  exist.
- Add spatial diversity and uncertainty/diversity-aware exploration.
- Explain whether selection is source-independent and how ties are resolved.
- Evaluate the full K x rho surface with validation-only policy selection.

### 3.4 Source-level evidence audit

- Define `Omega_i` and `Omega_t` before their first use.
- State pixel-coordinate conventions and clipping at image boundaries.
- Report source-clustered paired differences, not only marginal intervals.
- Keep GT oracle and shuffled-score controls explicitly diagnostic.

### 3.5 Structured inference

- Publish the exact prompt, output JSON schema, allowed values, count-bin
  boundaries, density definition, coverage definition, decoding parameters,
  stop condition, and parser behavior.
- Rename Equation 8. It is mean constraint satisfaction, not exact schema
  validity. Also report strict whole-record validity separately.
- Define how malformed generations enter task scoring.
- State the number of repeats and their use at train, validation, and test time.

### 3.6 Selective decision

- Distinguish post-generation safety from compute savings.
- Justify or ablate the fixed weights in the reliability score.
- Freeze the risk target before test evaluation.
- Compare raw confidence, schema-only rejection, fixed score, learned gate,
  and a simple detector-agreement baseline.
- Report coverage, selective risk, false-accept rate, accepted source count,
  and review workload at the chosen operating point.
- Do not claim distribution-free risk control.

### 3.7 Source-level reduction

Implement this section before submission. Specify:

- overlap-aware de-duplication;
- voting/fusion rule for each field;
- coordinate-aware count aggregation;
- conflict handling;
- behavior when no tile is accepted; and
- source-level calibration and evaluation.

The final paper cannot say that the reducer is planned or unavailable.

### Algorithm

Revise the algorithm to expose two stages:

1. pre-inference selection, which controls VLM cost; and
2. post-inference acceptance, which controls decision risk.

Include source-level reduction and return one source decision plus a review
status. Initialize all sets explicitly.

## 4. Experimental Design

### 4.1 Dataset and annotation audit

- State ownership, release status, licensing/access conditions, capture
  protocol, geography at a non-identifying level, sensors, altitude/range,
  and annotation process.
- Complete the human audit with sample size, sampling rule, reviewer count,
  agreement, adjudication, and exclusions.
- Report crop/source imbalance and negative-source counts.
- Do not call the corpus a public dataset unless release is authorized.

### 4.2 Observed domain shift

Keep descriptive shift statistics, but do not treat them as causal proof of
transfer failure. Add crop-conditional object-size, density, appearance, and
detector-recall distributions with source-level uncertainty.

### 4.3 Evaluation protocols

Report M->M, A->A, M->A, A->M, and pooled training with the same held-out
source tests. Freeze all hyperparameters on validation data. Publish split and
manifest hashes. Ensure no tile, source, or near-duplicate crosses a split.

### 4.4 Baselines

Mandatory baselines:

- detector-only source aggregation;
- detector plus deterministic rules for presence/count/density/coverage;
- full-image downsampled VLM;
- random, spatial, confidence, count, combined, and exploit--explore routing;
- diversity-aware/uncertainty-aware routing;
- schema-only and confidence-only rejection; and
- oracle routing for diagnosis only.

### 4.5 Metrics and statistics

- Define the unit of analysis for every metric.
- Report per-field macro-F1 and source-level exact-record accuracy.
- Report calibration and selective metrics with source-clustered intervals.
- Use paired bootstrap differences for policy comparisons on shared sources.
- Correct for or clearly limit multiple exploratory comparisons.
- Report detector, tiling, selection, transfer, VLM, reduction, and human-review
  costs separately.

### 4.6 Ablations

Every ablation must answer one causal question. Predeclare the primary policy,
budget, model, risk target, and test metric before final scoring. Prompt, tile
size, overlap, K, rho, reliability signals, and number of generations belong in
the supplement unless one changes the central conclusion.

## 5. Results

### 5.1 Data and detector

Retain only verified corpus and detector results. Include crop-stratified
detector performance and the detector-only downstream baseline.

### 5.2 Equal-budget policy comparison

Report the Pareto frontier instead of declaring one policy best. Show utility,
coverage/diversity, negative evidence, accepted risk, and latency. Include
paired differences against combined top-K and spatial uniform.

### 5.3 VLM necessity and model generality

Lead with detector-only versus detector+VLM. Model scaling is secondary.
Explain any near-zero task F1, schema failure, or hallucination rate rather than
presenting it as an unexplained table entry. Identify hardware and full timing
protocol.

### 5.4 Directed cross-crop transfer

Replace all instructional prose with a completed 2x2 matrix and paired transfer
drops. Include source-level confidence intervals and at least one diagnostic
breakdown by object scale or density stratum.

### 5.5 Selective reliability

Include the complete risk--coverage figure in the main paper. Mark the
validation-selected operating point and report its held-out coverage, risk,
false-accept rate, accepted sources, and review burden.

### 5.6 Failure analysis

Report an adjudicated taxonomy with counts and denominators. Select examples by
a frozen rule. Distinguish detector miss, routing miss, boundary truncation,
schema failure, semantic error, unsupported positive, reduction conflict, and
correct abstention.

## 6. Discussion, Limitations, and Ethics

Discuss what was demonstrated, not what was intended. Explicitly cover:

- two-crop external-validity limit;
- one-class annotation limit;
- detector dependence;
- calibration under target shift;
- cost of human review;
- private-data reproducibility;
- possible automation bias; and
- the requirement for human agronomic oversight.

## 7. Conclusion

Use three sentences: problem, verified result, bounded implication. Do not
contain plans, placeholders, or claims broader than the evaluated tasks.

## Figures and tables in the seven-page paper

1. **Figure 1:** compact architecture plus explicit cost/safety split.
2. **Table 1:** dataset, source split, and detector-only baseline.
3. **Figure 2:** equal-budget Pareto comparison across policies.
4. **Table 2:** detector-only versus detector+VLM source-level performance.
5. **Table 3:** 2x2 directed transfer matrix with paired drops.
6. **Figure 3:** held-out risk--coverage curves and operating point.
7. **Table 4:** ablation of selector and reliability signals.

Domain-shift diagnostics, model ladder details, prompts, qualitative panels,
and full sensitivity sweeps move to the supplement.

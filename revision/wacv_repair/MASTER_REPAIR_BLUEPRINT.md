# Master WACV Repair Blueprint

## 1. Target paper identity

### Paper type

WACV application-track paper with a computer-vision systems contribution. The
paper should not compete primarily on a new backbone or universal state-of-the-
art accuracy. It should compete on:

- a clearly defined fixed-budget visual decision problem;
- a complete source-level system;
- careful equal-cost comparative assessment;
- directed crop-shift evaluation;
- selective prediction with operational review burden; and
- transparent failure and efficiency analysis.

### One-sentence scientific thesis

> For high-resolution UAV nursery imagery, evidence allocation and acceptance
> should be optimized jointly at a fixed multimodal budget, because foreground
> recall, spatial diversity, negative evidence, decision risk, and compute are
> competing objectives.

This thesis remains valid even if exploit--explore is not the single best
policy on every metric.

### Primary scientific question

At the same source-image VLM budget, does detector-guided evidence allocation
plus validation-only selective prediction improve the source-level utility--
risk trade-off over detector-only aggregation and simpler random, spatial, and
top-ranked policies under directed crop shift?

## 2. What caused rejection

### Fatal completeness defects

1. Sections 5.4, 5.5, and 5.6 contained instructions rather than results.
2. Section 3.7 stated that the source-level reducer was not implemented.
3. The sentence after the risk-threshold equation was incomplete.
4. The conclusion contained unfinished prospective text.
5. The LaTeX source and submitted PDF do not contain a consistent numerical
   record.

Any one of the first four can signal an unfinished submission. Together they
make a clear reject rational even when the idea is innovative.

### Scientific evidence defects

1. No M->M, A->A, M->A, A->M transfer matrix.
2. No held-out risk--coverage curves for the fitted gate.
3. No detector-only source-level baseline.
4. No evidence that a VLM is needed for the chosen targets.
5. Exploit--explore lost to simpler policies on several direct metrics.
6. End-to-end detector-to-decision efficiency was not measured.
7. Failure taxonomy and human audit were described but not completed.

### Framing defects

- "Reliable cross-crop monitoring" exceeded the demonstrated evidence.
- One-class boxes support inventory-oriented tasks, not plant health or
  agronomic recommendations.
- Tile-level task prediction was discussed as if it were source-level nursery
  monitoring.
- Post-generation rejection was allowed to sound like a compute-saving step.

## 3. Required paper-level changes

### Title

Use a bounded title until transfer and risk claims are verified:

> OrnaScout: Fixed-Budget Visual Evidence Allocation and Selective Prediction
> for High-Resolution UAV Nursery Imagery

"Cross-crop" may return after the directed transfer table is complete.
"Reliable" should be avoided unless fixed-risk coverage is convincingly
demonstrated on held-out source images.

### Abstract

Rewrite to five moves:

1. operational problem;
2. fixed-budget formulation;
3. system and baselines;
4. completed source-level findings; and
5. bounded implication.

Remove the long list of dataset medians unless one directly explains the
evaluated shift. The abstract must contain detector-only comparison, transfer,
and selective-risk evidence if these remain central claims.

### Introduction

- State the agricultural decision: inventory-oriented source-level scouting,
  not diagnosis.
- Define input, budget, output, abstention, and human action.
- Explain why detection alone may be insufficient, then test that explanation.
- Present the VLM as a hypothesis under evaluation, not an assumed necessity.
- Limit contributions to three completed contributions.

### Related work

Rebuild around closest alternatives, not model chronology:

1. high-resolution/sliced detection and counting;
2. adaptive region or token selection;
3. selective prediction and calibration under shift;
4. agricultural and aerial VLM evaluation.

Every subsection ends with a concrete distinction and the corresponding
baseline used in the paper.

### Method

- Formalize tile-level and source-level targets separately.
- Add a complete cost model.
- Correct the spatial baseline and gate fitting procedure.
- Implement the source-level reducer.
- Separate strict schema validity from constraint satisfaction.
- Replace arbitrary fixed-score weights with validation-only ablation or a
  clearly labeled heuristic baseline.
- Include detector-only and deterministic aggregation in the method diagram.

### Experiments

- Freeze manifests and source splits.
- Complete annotation and duplicate audits.
- Add detector-only and full-image/downsampled VLM controls.
- Complete directed crop transfer.
- Fit gates without reusing the same records for model fitting and threshold
  selection unless cross-fitting is used.
- Report source-level paired intervals and end-to-end cost.

### Results

Every subsection must answer a named scientific question. There will be no
"report X" or "analysis should" prose. Mixed results are reported as Pareto
trade-offs rather than hidden or rhetorically reversed.

### Discussion and conclusion

- State what worked, what did not, and where the detector dominates.
- Discuss private-data reproducibility and human oversight.
- End with one verified conclusion, not future experiments.

## 4. Acceptance-level evidence standard

The repaired paper should satisfy the following reviewer test:

### Correctness

- no leakage or duplicated source evidence across splits;
- no test-time tuning;
- unit of analysis is explicit;
- uncertainty respects source clustering;
- equations match implementations;
- all table values are artifact-generated.

### Completeness

- all central claims have results in the main paper;
- all methods used in results are fully defined;
- no planned component is described as deployed;
- no pending cell, placeholder, or incomplete sentence remains.

### Significance

- the paper explains why fixed-budget evidence allocation matters beyond this
  nursery;
- the VLM is retained only if it adds measurable value;
- the paper yields a general insight about allocating multimodal compute under
  spatial and domain shift.

### Comparative assessment

- detector-only and deterministic baselines;
- equal-budget routing baselines;
- diversity-aware alternative;
- raw/fixed/learned rejection baselines;
- transfer and efficiency comparisons.

### Reproducibility

- exact prompts, schema, bins, seeds, model revisions, hardware, commands, and
  manifest hashes;
- code snapshot that regenerates tables and figures;
- explicit data-access statement.

## 5. Main narrative after repair

1. A 5K source image cannot be represented faithfully by one downsampled VLM
   input, while exhaustive tiling is expensive.
2. A detector cheaply exposes local evidence but is imperfect under crop shift.
3. Selection policies allocate a fixed number of expensive semantic inspections
   across exploitation, spatial diversity, and negative evidence.
4. A structured VLM is tested against detector-only aggregation, not assumed
   superior.
5. A validation-fitted gate controls which source records are accepted and how
   much human review remains.
6. Directed transfer reveals what survives crop shift and which failures remain.

This is a stronger precision-agriculture story because it ties the AI method to
an operational scouting decision, review workload, and deployment budget.

# Table and Figure Decision Plan

## Main-paper figures

### Figure 1 - System and decision architecture

**Keep, but redesign.**

Must show:

- source-safe split and tiling;
- detector over all candidate tiles;
- equal-budget selection;
- detector-only baseline path;
- structured VLM path;
- post-generation gate;
- source-level reducer; and
- accepted source record versus human review.

Use solid arrows for deployment computation and dashed arrows for training or
validation-only fitting. Explicitly distinguish compute saving from safety.

### Figure 2 - Policy Pareto frontier

**Replace the descriptive domain-shift figure in the main paper.**

Plot source-level task utility or exact-record accuracy against accepted risk,
with marker size or labels for VLM calls/latency. Include random, spatial,
count, combined, exploit--explore, and diversity-aware policies. Domain-shift
statistics move to the supplement.

### Figure 3 - Risk--coverage and transfer

**Required.**

Panel A: held-out risk--coverage curves for raw confidence, schema-only, fixed
score, and learned gate. Mark the validation-selected operating point.

Panel B: directed transfer drops or crop-stratified accepted-risk comparison.

## Main-paper tables

### Table 1 - Dataset, split, and detector baseline

**Replace the current dataset-only table.**

Rows: Magnolia, Azalea, total. Columns: source train/val/test, boxes, negative
sources, median instances/source, median normalized box area, detector AP and
recall. Keep only values needed to understand the shift and evaluation.

### Table 2 - Equal-budget routing and source utility

**Replace current Tables 3 and 4 with one decision-oriented table.**

Columns:

- source exact-record accuracy or primary utility;
- evidence recall;
- spatial diversity/redundancy;
- hard-negative recall;
- AURC;
- p95 end-to-end latency.

Rows: random, spatial, confidence, count, combined, exploit--explore,
diversity-aware. Add paired differences or significance markers only when the
statistical rule is predeclared.

### Table 3 - VLM necessity

**New and mandatory.**

Rows:

- detector-only;
- detector plus deterministic source rules;
- full-image downsampled VLM;
- uniform tiled VLM;
- best validation-selected OrnaScout policy.

Columns: presence F1, count metric, density/coverage metric, exact record,
hallucination/FAR, review rate, latency, memory.

This table decides whether the VLM claim survives.

### Table 4 - Directed crop transfer

**New and mandatory.**

Use a 2x2 train/test block for Magnolia and Azalea, plus pooled training.
Report the primary source-level metric, accepted risk/coverage, and paired drop
from the corresponding within-crop model.

### Table 5 - Reliability operating point

**Required if space permits; otherwise merge with Figure 3.**

Rows: raw confidence, schema-only, fixed score, learned gate. Columns: AURC,
coverage at target risk, observed accepted risk, false-accept rate, accepted
sources, review burden.

## Tables to remove or demote

- Current model-generality table: move to supplement unless all rows are
  artifact-verified and it supports a central conclusion.
- Current hard-negative mining table: move to supplement unless HNM is claimed
  as a core contribution.
- Descriptive domain-shift table/figure: supplement after the transfer matrix
  exists.
- Any table containing pending, estimated, manually inferred, or unexplained
  degenerate values: remove.

## Supplementary material

1. Full data and annotation audit.
2. Crop-shift distributions.
3. K x rho selector surfaces.
4. Tile size and overlap sensitivity.
5. Prompt and generation-repeat sensitivity.
6. Full VLM ladder and hardware details.
7. Gate coefficient/signal ablations.
8. Failure taxonomy and frozen qualitative panels.
9. Exact prompts, schemas, bins, manifests, and commands.

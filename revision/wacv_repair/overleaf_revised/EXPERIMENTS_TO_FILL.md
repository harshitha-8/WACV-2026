# Required Experiments and Destination Cells

## Table 1: corpus and detector evidence

- source split by crop;
- human-audit sample and agreement;
- detector recall by crop;
- duplicate and leakage audit statement.

## Table 2: equal-budget allocation

For random, true 2D spatial, confidence, count, combined, exploit--explore, and
diversity-aware policies:

- strict source-record accuracy;
- evidence recall;
- spatial coverage;
- overlap redundancy;
- hard-negative recall;
- source-level AURC; and
- p95 end-to-end latency.

Use K in {1, 2, 4, 8, 16} and validation-only rho sweeps before freezing the
primary configuration. Report paired source-level comparisons.

## Table 3: VLM necessity

Compare detector-only, detector plus rules, whole-image VLM, uniform tiled VLM,
OrnaScout without gate, and OrnaScout with gate. Fill presence F1, continuous
count error, density F1, coverage F1, exact record, negative-source false
acceptance, review rate, and p95 latency.

## Table 4: directed crop transfer

Complete M->M, M->A, A->M, A->A, and pooled training. Report primary utility,
source-clustered interval, paired transfer drop, and selective operating point.

## Figure and Table 5: reliability

Compare raw confidence, strict schema, detector agreement, fixed score, and the
cross-fitted learned gate. Fill AURC, coverage at target risk, observed accepted
risk, false-accept rate, accepted-source count, and review rate.

## Efficiency and failure analysis

Measure tiling, detector, selection, transfer, VLM, parsing/gating, and reducer
time. Report named hardware, precision, warm-up, generation length, throughput,
peak memory, and model-load memory. Complete the frozen, stratified failure
taxonomy and qualitative panels.

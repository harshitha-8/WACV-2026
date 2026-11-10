# IJCAI Experiment Completion Matrix

## Frozen primary question

At a fixed source-image VLM budget, does a detector-guided allocation policy
combined with source-level selective prediction provide better utility--risk
trade-offs than detector-only, deterministic, and simpler equal-budget routing
baselines under directed crop shift?

## Primary configuration

The primary configuration must be frozen on validation data before final test
scoring. Values below are inherited candidates, not automatically approved:

- tile size: 1024;
- overlap: 0.25;
- budget K: 8;
- exploration rho: 0.25;
- primary VLM: SmolVLM2-2.2B;
- generation repeats: 3;
- bootstrap unit: source image;
- bootstrap repetitions: 1,000.

The validation report must justify any retained value.

## Mandatory experiment blocks

| Block | Train/test protocols | Comparators | Primary outputs | Required artifact |
|---|---|---|---|---|
| E0 Data integrity | All sources | N/A | source counts, boxes, negatives, duplicates, split leakage | `data_audit.json` |
| E1 Detector | M->M, A->A, M->A, A->M, pooled | baseline, +HNM | AP, recall, FP, size-stratified recall, latency | `detector_transfer.csv` |
| E2 Source baselines | Same protocols | detector-only, deterministic aggregation | source presence/count/density/coverage F1, exact record | `source_baselines.csv` |
| E3 Selector audit | Validation, K={1,2,4,8,16} | random, spatial, confidence, count, combined, exploit--explore, diversity-aware, shuffled, oracle | evidence recall, spatial coverage, redundancy, hard-negative recall | `selector_audit.csv` |
| E4 End-task routing | Test, primary model | deployable selectors | per-field F1, exact record, hallucination, paired differences | `selector_task_test.csv` |
| E5 Directed transfer | M->M, A->A, M->A, A->M, pooled | detector-only and primary OrnaScout | transfer matrix and paired transfer drops | `cross_crop_transfer.csv` |
| E6 Selective reliability | Validation fit, test once | raw confidence, schema-only, detector agreement, fixed score, learned gate | risk--coverage, AURC, coverage at target risk, FAR, accepted sources | `selective_risk.csv` |
| E7 Source reducer | All test protocols | vote, confidence-weighted, overlap-aware | source exact record, count error, conflict/review rate | `source_reducer.csv` |
| E8 Model ladder | Primary pooled protocol | SmolVLM2-500M, SmolVLM2-2.2B, Phi-3.5, LLaVA | utility, schema, hallucination, latency, memory | `model_ladder.csv` |
| E9 Efficiency | Primary configuration | detector-only, each selector/VLM | stage latency, peak memory, calls/source, throughput, review load | `efficiency.json` |
| E10 Failure audit | Frozen stratified sample | N/A | taxonomy counts, agreement, examples | `failure_audit.csv` |

## Required statistical comparisons

1. Exploit--explore minus combined top-K on the same source images.
2. Exploit--explore minus spatial uniform on the same source images.
3. OrnaScout minus detector-only source aggregation.
4. Each cross-crop direction minus its corresponding within-crop reference.
5. Learned gate minus raw confidence and fixed score at matched coverage.

Report the paired mean difference and source-clustered 95% interval. Do not call
a policy better when intervals and operational metrics show only a trade-off.

## Stop/go criteria

The IJCAI framing is viable only if all of the following are true:

- source-level reducer is complete and deterministic;
- no split leakage or unresolved duplicate contamination exists;
- at least one VLM configuration adds measurable value beyond detector-only;
- cross-crop results are complete, even if performance drops;
- the gate improves risk ranking or fixed-risk coverage over raw confidence;
- all primary numbers trace to immutable artifacts.

If VLM value is not demonstrated, pivot the paper to budgeted evidence routing
with selective source aggregation and remove broad VLM claims. If the learned
gate does not beat fixed baselines, report the negative result and use the
simplest validated gate.

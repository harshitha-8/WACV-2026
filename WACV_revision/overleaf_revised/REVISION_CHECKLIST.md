# Revision Checklist

## Scientific scope

- [ ] The task is inventory-oriented source-level scouting.
- [ ] Health, disease, stress, quality, mortality, treatment, and yield claims
      are absent unless supported by new labels.
- [ ] The primary source-level endpoint is approved and defined.
- [ ] Exploit--explore is presented as a trade-off policy, not an assumed winner.
- [ ] Cross-crop and reliability language matches completed evidence.
- [ ] A definitive schema table identifies every evaluated, audit-only, gate,
      and unsupported field.
- [ ] The source prediction, inspected-region union, and uninspected state are
      distinct.

## System definition

- [ ] Detector-only and deterministic aggregation baselines are implemented.
- [ ] The 2D spatial baseline uses actual tile coordinates.
- [ ] Random policies use order-invariant per-source seeds.
- [ ] The overlap-aware source reducer is implemented and unit-tested.
- [ ] Strict schema validity is separated from constraint satisfaction.
- [ ] The gate uses source-grouped validation cross-fitting.
- [ ] Selection cost savings and post-generation safety are reported separately.
- [ ] The executable implementation matches the corrected manuscript; planned
      components are not written in the past tense.
- [ ] The repeat-consensus rule and R=1 behavior are frozen.
- [ ] Empty accepted sets cannot be reported as zero empirical risk.

## Evaluation

- [ ] Annotation, duplicate, sequence, and split-leakage audits are complete.
- [ ] Human annotation audit reports sampling, agreement, and adjudication.
- [ ] M->M, A->A, M->A, A->M, and pooled protocols are complete.
- [ ] Whole-image, uniform, detector-only, and equal-budget controls are complete.
- [ ] Risk--coverage baselines and the predeclared operating point are complete.
- [ ] End-to-end latency, memory, throughput, VLM calls, and review burden are
      measured on named hardware.
- [ ] Failure taxonomy reports counts, denominators, and agreement.
- [ ] Protocol matrix names training, tuning, fitting, threshold, and test data
      for every directed transfer run.
- [ ] Method comparisons are paired only on shared target sources.

## Paper structure

- [ ] Abstract contains only verified findings.
- [ ] Figure 1 matches the implemented system.
- [ ] Main paper contains the VLM-necessity comparison.
- [ ] Main paper contains directed transfer and risk--coverage evidence.
- [ ] Descriptive and sensitivity details are moved to supplementary material.
- [ ] Discussion distinguishes demonstrated findings from limitations.
- [ ] Conclusion contains one verified result and one bounded implication.

## Numerical integrity

- [ ] The submitted-PDF/source mismatch has been resolved from raw artifacts.
- [ ] Every value has an artifact path, hash, command, seed, and code commit.
- [ ] Tables and figures are generated programmatically from immutable results.
- [ ] No value is estimated from another paper, model card, blog, or memory.
- [ ] All confidence intervals use source-level resampling where specified.
- [ ] Test data were not used to select policies, bins, prompts, thresholds, or
      checkpoints.
- [ ] Every table row and figure series has a completed row in
      `RESULT_PROVENANCE_REGISTRY.csv`.

## Data and reproducibility

- [ ] Image and annotation release permissions are documented.
- [ ] If data are private, access limitations and complete dataset details are
      stated.
- [ ] Exact prompts, schema, bins, seeds, model revisions, and software versions
      are included in the supplementary package.
- [ ] Anonymous code contains no identifying paths or metadata.

## Approval outcome

- [ ] Approved for experiment completion.
- [ ] Approved for scientific rewrite after result verification.
- [ ] Approved for final submission audit.

### Requested changes

```text

```

# OrnaScout Results Status

Snapshot audited on 2026-08-17. This ledger separates measured evidence from
planned experiments so that preliminary outputs are not reported as results.

## Completed and verified

- Relabeled Magnolia: 297 matched source images, 15,644 valid boxes.
- Relabeled Azalea: 121 matched source images, 14,198 valid boxes.
- Combined: 418 source images and 29,842 valid one-class annotations.
- Five zero-width annotation rows are rejected during preparation; raw labels
  remain unchanged. Three empty Azalea label files are retained as source-level
  negatives. One unmatched Azalea RGB frame is excluded.
- Source-image-safe preparation produced 14,630 tiles: 10,570 train, 2,030
  validation, and 2,030 test. No source image crosses a split.
- Prepared tiles include 1,328 hard negatives.
- Annotation-review sheets and a review manifest have been generated.
- The method architecture, data audit, and cross-crop shift figures are
  reproducibly generated from the relabeled snapshot.

## Implemented method components

1. Source-image-safe split before overlapping tiling.
2. Detector evidence model trained only on the training partition.
3. Equal-budget tile selection using detector evidence plus controlled random
   exploration. With the default budget, six tiles exploit ranked evidence and
   two explore the remaining candidates.
4. A model-agnostic VLM adapter and fixed structured-output schema.
5. A validation-only selective-risk gate whose threshold is frozen before test.
6. Within-crop, cross-crop, and pooled evaluation protocols with source-level
   clustered confidence intervals.

## Models in the registered comparison

- SmolVLM2-500M, smallest edge-oriented baseline.
- SmolVLM2-2.2B, primary compact VLM.
- Phi-3.5-Vision, intermediate-capacity Microsoft baseline.
- LLaVA-1.5-7B, larger historical reference baseline.

Smoke tests establish runtime compatibility only. They are not accuracy
results. No model comparison, ablation, or selective-risk claim is complete
until predictions exist for the frozen validation and test protocols.

The post-relabel SmolVLM2-500M smoke check completed on one combined-test tile
with approximately 3.50 s generation latency and 335.84 MB process RSS. Its
eight-token response was truncated and is therefore not a valid task result.
This check verifies the data-to-adapter execution path only.

## Required before reporting paper results

1. Complete the representative-random annotation audit and summarize it.
2. Audit acquisition sequence, flight, or row grouping. The current guarantee
   is source-image separation, not sequence-block separation.
3. Train the detector and generate validation/test evidence without exposing
   test annotations during selection.
4. Run all four VLMs with identical evidence budgets and decoding settings.
5. Fit the selective gate on validation outputs only, then freeze it for test.
6. Run random, uniform, top-ranked, and budgeted-selector ablations, plus budget
   and gate-signal ablations.
7. Report source-image-clustered confidence intervals, latency, peak memory,
   schema validity, count error, hallucination on verified negatives, and
   risk-coverage behavior.
8. Add an external nursery dataset or clearly limit the generalization claim to
   the two observed crops and acquisition domains.

## Metric boundary

Presence, continuous count error, and continuous box-coverage error are the
strongest current endpoints. Fixed coverage and density classes are diagnostic
because the present bins are highly imbalanced; they must be recalibrated using
training data only before being promoted to headline metrics.

## Recommended figure set

Main paper candidates:

- Method architecture.
- Annotation geometry and small-object regime.
- Cross-crop appearance and annotation shift.
- Main comparison, risk-coverage, efficiency Pareto, and transfer matrix after
  full inference.

Supplementary or internal audit:

- Dataset composition and prepared-tile summaries.
- Annotation-audit sampling design and review sheets.
- Fixed-bin coverage/density diagnostics.

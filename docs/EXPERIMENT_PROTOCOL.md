# WACV Experiment Protocol

## Research question

Can detector evidence and validation-calibrated selective prediction make
compact VLM outputs more reliable under crop shift and fixed inference budgets?

## Required protocols

1. Within Magnolia and within azalea.
2. Magnolia training to azalea testing.
3. Azalea training to Magnolia testing.
4. Combined-crop training with crop-stratified held-out source images.
5. At least one external high-resolution small-object dataset for evidence that
   the method is not specific to one nursery.

## Baselines

- Detector only.
- VLM only with uniform tiling.
- Confidence-threshold rejection.
- Uniformly spaced and random tiles under exactly the same per-image budget.
- Detector-ranked tiles without selective routing.
- Full detector-guided selection plus learned gate.

## Primary metrics

- Presence, count-bin, and density macro F1; count MAE and continuous annotated
  box-coverage error.
- Coverage-class macro F1 is diagnostic only unless thresholds fitted on the
  training split produce adequate support in every evaluated class.
- JSON schema validity and hard-negative hallucination rate.
- Accuracy-risk coverage curve, AURC, selective accuracy, and review rate.
- Mean and p95 latency, peak memory, throughput, and VLM calls per source image.
- Source-image-clustered 95% bootstrap confidence intervals.

## Ablations

- Tile size: 512, 768, 1024, 1280.
- Overlap: 0, 0.15, 0.25, 0.40.
- Budget: 2, 4, 8, 16 tiles per image.
- Exploration fraction: 0, 0.10, 0.25, 0.50.
- Remove detector agreement, repeat consistency, or schema validity.
- One versus three VLM generations.
- Zero-shot versus SmolVLM2 LoRA adaptation.
- 500M versus 2.2B scaling.

Thresholds, bins, prompts, and model revisions must be frozen before test-set
evaluation. Cross-crop calibration is empirical and must not be presented as a
distribution-free guarantee.

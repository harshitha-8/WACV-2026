# OrnaScout figure protocol

This document separates figures that support a scientific claim from figures
that are useful only during debugging. A figure is eligible for the paper only
when its statistical unit, ground truth, sample size, and plotted quantity are
explicit.

## Main-paper figure set

1. **Method architecture.** Show source-image splitting, overlapping tiling,
   detector evidence, fixed-budget tile selection, compact VLM inference, and
   the validation-calibrated accept/review gate. Dashed arrows denote
   training/calibration-only paths.
2. **Cross-crop data shift.** Use `06_cross_crop_shift.pdf`: normalized object
   area, excess-green/brightness appearance, and green-pixel fraction. Pair it
   with no more than two human-verified RGB examples per crop.
3. **Main comparison table.** Report SmolVLM2-500M, SmolVLM2-2.2B,
   Phi-3.5-Vision, and LLaVA-1.5-7B with per-crop task metrics, schema validity,
   hallucination on zero-center tiles, latency, and peak memory. Include 95%
   source-image-clustered confidence intervals.
4. **Accuracy-efficiency Pareto plot.** Plot task score against measured
   latency; encode peak memory by marker area and crop by marker shape. Show
   only measured runs under identical hardware, precision, and tile budget.
5. **Selective reliability.** Plot selective risk against retained coverage.
   Thresholds are fitted on validation data and frozen for test evaluation.
6. **Cross-crop transfer matrix.** Include in-domain, Magnolia-to-Azalea,
   Azalea-to-Magnolia, and pooled-training protocols for each model.
7. **Ablation table or compact plot.** Compare all tiles, uniform sampling,
   random sampling, detector-only ranking, and the complete adaptive selector
   at equal tile budgets. Add gate removal and evidence-component removals.
8. **Failure taxonomy.** Show a balanced set of human-verified errors:
   wrong-target mention, missed plant evidence, count-bin error, invalid schema,
   and unsafe false acceptance. Never select only visually dramatic examples.

## Supplementary data figures

- `01_dataset_overview.pdf`: source composition and annotation counts. Treat
  these as dataset statistics, not model results.
- `02_image_characteristics.pdf`: acquisition resolution, brightness, and
  sharpness shift.
- `03_object_geometry.pdf`: object-scale and aspect-ratio regime.
- `04_spatial_density.pdf`: per-crop annotation-center probability on a shared
  color scale.
- `05_count_coverage_labels.pdf`: source-image ground-truth count distribution
  and its association with summed normalized box area. This is an annotation
  quantity figure, not predicted-count accuracy.
- `09_tile_label_balance.pdf`: task-label imbalance.
- `10_tile_count_coverage.pdf`: count versus summed box-area proxy.
- `11_split_stability.pdf`: train/validation/test stability after source-level
  splitting.
- `12_spatial_positive_rate.pdf`: positive-tile probability by tile position.
- `14_tile_label_ecdfs.pdf`: cross-crop tile-label shift.
- `15_label_cooccurrence.pdf`: count-bin/coverage co-occurrence.
- `16_crop_imbalance.pdf`: crop imbalance and sampling implications.

## Diagnostic-only material

- Source contact sheets belong in `outputs/wacv/eda/diagnostics/` and are for
  annotation review, not performance claims.
- Random tile galleries, random hard-negative galleries, and the former
  boundary-truncation gallery are retired. Random montages do not establish a
  result, and the old boundary flag marks too many tiles to be discriminative.
- A zero-center tile is not automatically a true negative: it can contain a
  clipped or unlabeled plant. Human review is required before calling it a hard
  negative in the paper.

## Azalea annotation-quality protocol

Run `python wacv_pipeline.py audit-labels`. The generated manifest contains a
representative random subset for estimating annotation precision and a separate
geometry-stress subset for error discovery. A reviewer must label each sampled
box. Only the representative subset enters the reported precision estimate;
the stress subset is never treated as an unbiased error rate. The audit does
not estimate missed-label recall, which requires a separate full-image review.

Until this audit is complete, yellow rectangles in Azalea visualizations must
be described as **provided ground-truth boxes under review**, not detector false
positives.

## Quantity-result figure

The defensible quantity figure is not a montage. After detector inference, plot
source-image-level predicted count against ground-truth count separately for
Magnolia and Azalea, report MAE/RMSE and source-clustered confidence intervals,
and add a residual plot against ground-truth density. A model-output box is a
false positive only after matching against reviewed ground truth at a declared
IoU threshold.

## Rendering rules

- Save vector PDF plus 300-dpi PNG.
- Use Arial/Helvetica-compatible plot text, colorblind-safe colors, and a
  grayscale-distinguishable encoding.
- Put definitions, statistical unit, sample size, and uncertainty in the
  caption. Avoid decorative titles that repeat the caption.
- Use source images, not tiles, as the independent unit for confidence
  intervals and hypothesis tests.
- Never place proxy labels, unreviewed annotations, or fabricated values in a
  results figure.

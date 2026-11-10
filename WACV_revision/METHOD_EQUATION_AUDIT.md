# Method and Equation Audit

## Equation 1: detector evidence score

Current form:

```text
q_t = c_t + min(n_t, n_max) / n_max, n_max = 20
```

### Required clarification

- Define whether `c_t` is mean, maximum, or calibrated confidence.
- State the detector threshold and NMS settings used before `n_t` is counted.
- Justify `n_max=20` with validation-only sensitivity.
- State the score range and tie-breaking rule.
- Compare confidence, count, normalized combination, and learned validation-only
  ranking.
- Define zero detections, valid-footprint clipping, padding, truncated boxes,
  saturation frequency, and deterministic ties.

### Implementation issue

The implementation uses mean confidence plus clipped count but does not expose
score calibration by crop. Add crop-stratified score diagnostics.

## Equations 2--4: exploit--explore allocation

### Required clarification

- Define deterministic seed construction per source and repetition.
- Define behavior for fewer than K candidates.
- State whether random draws are independent across budgets and repetitions.
- Report K and rho selection using validation data only.
- Replace "exploration protects against detector errors" with a testable
  hypothesis.
- Define `K_i=min(K, |T_i|)`, rounding, pool shortages, candidate-manifest
  equality, and whether selected sets are nested across budgets.

### Implementation issue

The current RNG is global and therefore depends on manifest/source order.
Derive a per-source seed from the frozen study seed and source identifier so
selection is order invariant.

## Equation 5: evidence recall

- Define box visibility exactly as intersection area divided by original box
  area.
- Explain clipping at image boundaries.
- Report empty-source behavior separately.
- Use source-level aggregation and source-clustered intervals.
- Mark the metric undefined for empty sources and report negative-source
  behavior separately.

## Equations 6--7: spatial coverage and redundancy

### Missing definitions

Define `Omega_i` as the valid source-image pixel domain and `Omega_t` as the
tile footprint clipped to that domain before either equation appears.

### Implementation issue

The current "spatial uniform" policy selects evenly spaced entries after
sorting by tile ID. That is not guaranteed to be uniform in 2D geometry.
Replace it with a coordinate-aware policy, such as farthest-point sampling over
tile centers or a fixed spatial grid, and document its deterministic behavior.

Report negative retention and selected-negative fraction separately; their
denominators answer different questions. Define empty-union behavior and remove
padding from area calculations.

## Equation 8: schema score

Current quantity is the fraction of satisfied field constraints. It is not
strict whole-record schema validity.

### Correction

Report both:

- `constraint_score`: mean of the J checks; and
- `schema_valid`: one only if every required field, type, value constraint, and
  cross-field rule passes.

Do not label their mean as "Schema valid rate."

## Equation 9: repeat consistency

- Define the five categorical fields explicitly.
- State how malformed/missing values enter agreement.
- Report whether repeats are independently sampled and at what temperature.
- Compare one versus three generations as a cost/reliability ablation.
- When `R=1`, report consistency as unavailable rather than one.
- Freeze whether the delivered output is the first generation or a consensus.

## Equation 10: fixed reliability score

### Problem

Weights `.35/.25/.20/.20` are not justified. Schema validity also appears both
directly and indirectly through the constructed `gate_score` used by the
logistic model.

### Correction

- Treat Eq. 10 as a declared heuristic baseline.
- Add equal weights and validation-selected weights.
- Avoid feeding both raw components and a deterministic linear combination of
  the same components unless the redundancy is justified.
- Report sensitivity and coefficient stability.

## Equation 11: risk threshold

### Statistical issue

The current code fits the logistic failure model and chooses the risk threshold
on the same validation rows. This can underestimate accepted risk.

### Correction options

Preferred: cross-fitting within validation data, producing out-of-fold risk
scores for threshold selection, followed by refitting the predictor on all
validation records before one test evaluation.

Alternative: split validation into gate-fit and threshold-calibration source
subsets if sample size is adequate.

The target risk must be declared before test evaluation. Report uncertainty,
coverage, accepted errors, and accepted source count. Complete the sentence
after the equation.

Require a predeclared minimum accepted count or coverage. If no threshold meets
the target, report the target as unattained; never let an empty accepted set
appear to have zero empirical risk.

## Equation 12: AURC

- Define sort direction and tie handling.
- Define whether one error means any incorrect field or a task-specific error.
- Report AURC with source-clustered bootstrap intervals.
- Complement AURC with operational points; low AURC alone does not establish
  useful coverage.

## Algorithm 1

### Required changes

- Initialize accepted and review sets.
- Separate candidate detection cost from selected-tile VLM cost.
- Add source-level reduction.
- Return one source record, its acceptance decision, and tile-level audit trail.
- Include detector-only path for baseline evaluation.
- State failure behavior for malformed output and zero accepted records.
- Include prompt/schema version, repeat generation, raw-output preservation,
  tile coordinates, valid footprints, deterministic seed, and stage costs.
- Keep gate fitting and threshold calibration outside test-time pseudocode.

# Implementation and Test Plan

## Required implementation order

1. Freeze task/schema and source split.
2. Implement source ground-truth generation.
3. Implement detector-only source prediction.
4. Repair selector geometry, seeding, tie handling, and shortage behavior.
5. Implement strict output validation and a frozen repeat-consensus rule.
6. Implement overlap-aware source reduction.
7. Implement source-grouped cross-fitting and threshold selection.
8. Add artifact registry and programmatic table/figure generation.
9. Run decisive baselines before the full model ladder.

## Mandatory unit tests

- no detector responses;
- source with no verified plants;
- fewer candidates than budget;
- exploration pool smaller than requested;
- deterministic score ties;
- order-invariant random selection;
- clipped boundary tiles and padded pixels;
- overlapping detections of the same source instance;
- malformed JSON and missing fields;
- one repeat versus multiple repeats;
- conflicting tile records;
- no valid VLM records;
- all records referred for review;
- no validation threshold meeting minimum count and risk;
- uninspected region distinct from observed empty region; and
- identical table regeneration from the same artifact hashes.

## Integration acceptance tests

- every policy consumes the same candidate manifest and declared budget;
- detector-only and VLM systems predict the same source targets;
- train/validation/test source and acquisition groups are disjoint;
- target-test labels are never read by fitting code;
- Algorithm 1 feature names match executable keys;
- stage costs sum to measured end-to-end source cost; and
- final tables contain only registry-backed values.

## Decision checkpoint

After the detector-only, strongest simple selector, and primary VLM are compared
on identical validation sources, decide whether the VLM earns its role. If it
does not materially improve utility, selective behavior, or auditable evidence
at acceptable cost, narrow the paper to budgeted evidence allocation or adopt
the detector-only conclusion. Do not add complexity to rescue a preferred
narrative.

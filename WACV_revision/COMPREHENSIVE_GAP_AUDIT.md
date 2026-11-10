# Comprehensive Revision Gap Audit

## Verdict

The revised Overleaf package is a sound structural recovery of the rejected
paper, but it is not yet a submission-ready paper and cannot honestly be called
a clear accept. It now asks the right scientific questions and blocks invented
numbers. The decisive work that remains is implementation, frozen evaluation,
and evidence-backed rewriting.

This audit reconciles the submitted manuscript, reviewer concerns, the detailed
section/equation/table correction plan, the current repository code, and the
revised Overleaf draft.

## Status vocabulary

- **Resolved in draft**: corrected in the manuscript specification.
- **Specified, not implemented**: the intended correction is documented but the
  checked-in code does not yet implement it.
- **Experiment blocked**: requires a frozen run or human audit.
- **Author decision**: a scientific scope or release decision must be approved.

## Code truth discovered during audit

The current checked-in implementation still has the following limitations:

1. `adaptive_selector.py` implements “uniform” selection over sorted tile IDs,
   not true two-dimensional spatial selection.
2. Its random generator is global, so stochastic choices depend on source
   iteration order.
3. `run_vlm_wacv.py` stores prompt-generated text; generation is not
   grammar-constrained.
4. `ornascout_pipeline_v2.py` evaluates tile records, uses the first repeat as
   the prediction, and sets single-repeat consistency to one.
5. The repository has no completed overlap-aware source-record reducer.
6. `selective_gate.py` uses `schema_score`, `consistency_score`,
   `detector_agreement`, and a derived `gate_score`, then fits and thresholds on
   the same validation rows.

Therefore the corrected selector, reducer, and cross-fitted gate in the revised
paper are target specifications. They must not be described as completed until
implemented, unit-tested, and evaluated.

## Coverage of the detailed correction plan

| Area | Current status | Required completion evidence |
|---|---|---|
| Result provenance | Specified, not implemented | Registry row and immutable artifact for every table/figure series |
| Task labels and unit | Resolved in draft; author approval pending | Approved schema, frozen label script, class support report |
| Correlation and split audit | Experiment blocked | Source/group manifest, duplicate report, acquisition-group audit |
| Detector-only alternative | Specified, not implemented | Comparable source predictions and review baseline |
| Tile versus source claim | Resolved in draft | Tested source reducer and source-level metrics |
| Selector edge cases | Resolved in specification | Implementation plus unit tests |
| Schema validity | Resolved in draft | Versioned prompt/schema/parser and malformed-output tests |
| Gate fitting | Resolved in specification | Out-of-fold validation scores, frozen threshold, held-out test |
| Directed transfer | Experiment blocked | M->M, A->A, M->A, A->M, pooled artifacts |
| Efficiency | Experiment blocked | Synchronized stage and source timings on named hardware |
| Failure analysis | Experiment blocked | Frozen sampling rule, two-reviewer audit, adjudicated counts |
| Abstract/contributions | Intentionally blocked | Rewrite only from verified final results |

## Equation and algorithm closure

| Item | Correction now present | Still required |
|---|---|---|
| Detector score | Zero-detection rule, pre-processing, saturation and ties specified | Validate `n_max`; implement clipping/deduplication |
| Budget allocation | Per-source budget, shortage handling, order-invariant seed specified | Implement and test nested/non-nested budget policy |
| Evidence recall | Empty-source behavior and aggregation boundary specified | Generate source-macro and instance-micro diagnostics |
| Spatial diagnostics | Valid footprints and padding exclusion specified | Implement exact geometric union |
| Negative evidence | Two denominators separately named | Build verified negative sets and report both |
| Schema score | Constraint score separated from strict validity | Version exact checks and parser |
| Repeat consistency | Four fields fixed; R=1 marked unavailable | Freeze consensus rule and count repeat cost |
| Risk threshold | Minimum accepted count; empty set cannot mimic zero risk | Cross-fit and predeclare risk/coverage targets |
| Source reducer | Field-specific rules and unseen-region handling specified | Implement, test, and freeze |
| Algorithm 1 | Repeats, raw outputs, coordinates, audit trail, costs added | Match executable code line by line |

## Tables and figures

The old Tables 2--5 must not be cosmetically repaired. Their values must be
recovered or regenerated from raw artifacts. The revised table set correctly
prioritizes:

1. corpus/audit/detector evidence;
2. equal-budget policy comparison;
3. detector-only versus VLM value;
4. directed transfer;
5. selective reliability; and
6. efficiency/failure analysis.

The main-paper figures must contain the implemented architecture, a downstream
utility-risk-cost frontier, and held-out risk-coverage/transfer evidence. Domain
description and secondary sensitivity plots belong in supplementary material
when space is constrained.

## Five submission gates

### Gate 1: scientific definition

- approve the source-level task and field set;
- freeze label-generation rules and class thresholds;
- define the practical user and review action; and
- prohibit disease, health, yield, treatment, and segmentation claims.

### Gate 2: implementation parity

- corrected two-dimensional selector and order-invariant seeds;
- detector-only source baseline;
- overlap-aware source reducer;
- strict schema validator and frozen consensus rule; and
- source-grouped cross-fitted gate.

### Gate 3: frozen evaluation

- complete audit and leakage checks;
- decisive baselines before adding models or crops;
- directed transfer, reliability, cost, and failure experiments; and
- no test-driven choice of prompt, thresholds, policy, or endpoint.

### Gate 4: numerical integrity

- every number entered through `RESULT_PROVENANCE_REGISTRY.csv`;
- tables/figures generated from immutable artifacts;
- direct paired comparisons only on shared target sources; and
- independent value and claim verification.

### Gate 5: manuscript release

- rewrite title, abstract, contributions, discussion, and conclusion last;
- remove all pending markers and author-facing instructions;
- verify references, anonymity, venue format, and page limit; and
- compile and visually inspect the complete PDF and supplement.

Failure at any gate blocks submission. This is stricter than promising a clear
accept, but it is the defensible route to an acceptance-competitive paper.

# Reviewer-to-Action Matrix

## Consensus concerns

| Reviewer concern | Evidence in current paper | Required correction | Completion evidence |
|---|---|---|---|
| Cross-crop claim unsupported | Section 5.4 contains instructions | Run and report M->M, A->A, M->A, A->M plus pooled | 2x2 matrix, domain gaps, source CIs; paired method contrasts only on shared targets |
| Selective reliability unsupported | Section 5.5 contains instructions | Complete raw/schema/fixed/learned risk--coverage comparison | Curves, operating point, FAR, accepted sources |
| Source pipeline incomplete | Section 3.7 says reducer is planned | Implement frozen overlap-aware source reducer | Unit tests and source-level table |
| Exploit--explore not consistently best | Count/combined policies win direct metrics | Present Pareto trade-off and test diversity-aware alternatives | Paired utility-risk comparisons |
| VLM stage unjustified | Targets largely derive from boxes | Add detector-only and deterministic rule baselines | Incremental value table |
| Gate does not save inference cost | Rejection occurs after VLM generation | Separate cost-saving selection from safety-oriented rejection | Stage-level latency/cost diagram |
| Missing operational efficiency | Only model latency/memory reported | Measure full source pipeline and review burden | Detector-to-decision timing table |
| Insufficient reproducibility | Prompts/schema/hardware not fully specified | Publish exact protocol and artifact ledger | Anonymous reproducibility package |
| Agricultural task unclear | Monitoring language broader than labels | Define inventory/scouting task and prohibited claims | Revised problem statement |
| Manuscript unfinished | Placeholders and incomplete sentences | Zero-placeholder release gate | Automated scan and independent proofread |

## Reviewer-specific preservation decisions

### Positive reviewer: retain and substantiate

The strong-accept review identifies four valuable elements:

1. fixed-budget informative tile selection;
2. exploitation plus exploration;
3. structured compact-VLM scouting records; and
4. detector hard-negative mining.

These remain the core system components, but the revision must not convert
positive language into unsupported superiority claims. Each component receives
one direct ablation and one operational interpretation.

### Rejecting reviewers: resolve rather than rebut

The rejecting reviews are correct that the submitted version was incomplete.
The repair should not argue that intended analyses were sufficient. It should
replace every intended analysis with evidence and make the source-level system
complete.

## Claim disposition

| Existing claim | Decision | Reason |
|---|---|---|
| Fixed-budget inference is practically relevant | KEEP | Clear systems motivation |
| Source split before tiling is necessary | KEEP + VERIFY | Sound protocol; publish leakage audit |
| Exploit--explore is the best selector | DELETE | Not supported by current direct metrics |
| Exploit--explore exposes a utility/diversity/risk trade-off | TEST | Potentially defensible with paired analysis |
| Reliable cross-crop monitoring | HOLD | Requires transfer and selective-risk results |
| VLM provides richer scouting than detection | TEST | Requires detector-only comparison |
| Gate reduces unsafe accepted decisions | TEST | Requires held-out fixed-risk evaluation |
| Gate reduces VLM compute | DELETE | Gate acts after generation |
| Dataset is a broad nursery benchmark | DELETE/NARROW | Two crops, private corpus, one-class labels |
| Hard-negative mining improves detector evidence | VERIFY | Current matched result needs provenance |

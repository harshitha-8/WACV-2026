# WACV and CVPR Rubric Alignment

Official guidance consulted:

- WACV 2026 Reviewer Guidelines:
  <https://wacv.thecvf.com/Conferences/2026/ReviewerGuidelines>
- CVPR 2026 Reviewer Guidelines:
  <https://cvpr.thecvf.com/Conferences/2026/ReviewerGuidelines>
- CVPR 2026 Reviewer Training Material:
  <https://cvpr.thecvf.com/Conferences/2026/ReviewerTrainingMaterial>

## WACV application-track standard

WACV explicitly allows application papers to be evaluated on systems-level
innovation, novelty of the domain or task/formulation, and comparative
assessment rather than algorithmic novelty alone.

### Current paper alignment

| Criterion | Current position | Required repair |
|---|---|---|
| New or meaningfully reformulated application | Strong | Define fixed-budget source-level scouting precisely |
| Systems-level innovation | Promising | Complete reducer and detector-to-decision system |
| Comparative assessment | Insufficient | Add detector-only, deterministic, spatial/diversity, and reliability baselines |
| Technical soundness | Unresolved | Correct gate validation, spatial baseline, metric definitions, provenance |
| Complete evidence | Failed | Replace all planned analyses with results |
| Practical relevance | Strong | Quantify latency, review burden, and operational decision |

The positive reviewer score is consistent with the first, second, and sixth
criteria. The rejection is consistent with failure on comparative assessment,
technical completion, and evidential support.

## CVPR-style quality standard

CVPR guidance emphasizes a technically sound paper that makes a meaningful
methodological, empirical, or conceptual contribution. It asks reviewers to
balance novelty, significance, potential impact, correctness, completeness,
clarity, positioning, and reproducibility rather than judging only a state-of-
the-art accuracy table.

### Current paper alignment

| Criterion | Current position | Required repair |
|---|---|---|
| Novelty/insight | Moderate to strong | Articulate joint evidence-allocation and acceptance problem |
| Correctness | Unresolved | Trace numbers, repair baselines, avoid calibration optimism |
| Completeness | Weak | Finish transfer, reliability, failure analysis, source reduction |
| Significance | Plausible | Demonstrate general compute-allocation insight beyond two crops |
| Clarity | Weak in submitted version | Remove instructions, incomplete prose, and ambiguous metrics |
| Reproducibility | Weak to moderate | Publish exact artifacts, prompts, hashes, hardware, and commands |
| Empirical depth | Weak for central claims | Add source baselines, directed shift, risk operating points |

## Top-paper threshold for this project

A strong paper is not created by adding more plots indiscriminately. It should
deliver three memorable insights:

1. **Allocation insight:** policies occupy a measurable Pareto frontier among
   foreground evidence, spatial diversity, negative evidence, and compute.
2. **Model-value insight:** structured VLM inference either adds source-level
   utility beyond detection or the paper honestly identifies where it does not.
3. **Reliability insight:** risk signals and abstention are evaluated at useful
   coverage under directed domain shift, with explicit human-review burden.

The system becomes compelling when these insights are supported by complete,
paired, source-level evidence and when the precision-agriculture task is stated
without exceeding the annotations.

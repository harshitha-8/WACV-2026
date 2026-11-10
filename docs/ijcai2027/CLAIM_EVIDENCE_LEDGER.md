# Claim--Evidence Ledger

No claim may enter the abstract, contribution list, or conclusion unless its
status is VERIFIED and its artifact path is recorded here.

| ID | Candidate claim | Required evidence | Current status | Action |
|---|---|---|---|---|
| C1 | Source-before-tiling prevents source leakage | Split generator, source IDs, duplicate audit, manifest hash | PARTIAL | Re-run audit and publish hashes |
| C2 | Detector-guided routing beats random at equal K | Source-level paired bootstrap across K | PARTIAL | Verify from frozen selector artifacts |
| C3 | Exploit--explore improves the operational trade-off | Paired task utility, diversity, hard-negative recall, AURC, and latency versus combined top-K and spatial uniform | UNSUPPORTED | Run full paired evaluation; describe Pareto trade-off if mixed |
| C4 | The VLM adds value beyond detection/counting | Detector-only and deterministic reducer baselines on identical source tests | MISSING | Implement and evaluate baselines |
| C5 | The system generalizes across crops | M->M, A->A, M->A, A->M matrix with paired transfer drops | MISSING | Complete all directed protocols |
| C6 | The selective gate improves reliability | Held-out risk--coverage curves and fixed-risk operating point | MISSING | Fit on validation only; evaluate once on test |
| C7 | The system produces deployable source records | Frozen overlap-aware reducer and source-level metrics | MISSING | Implement reducer and tests |
| C8 | Structured decoding is auditable | Exact schema, strict validity, constraint satisfaction, parser failures | PARTIAL | Publish schema/prompt; separate metrics |
| C9 | The approach is resource efficient | End-to-end detector-to-decision timing, memory, throughput, calls, and review load | MISSING | Benchmark complete pipeline on named hardware |
| C10 | Hard-negative mining improves detector evidence | Matched training/validation protocol and repeated or uncertainty-aware comparison | PARTIAL | Recover exact artifacts and verify table |

## Numerical provenance record

For every final table row, record:

```text
claim_id:
table_or_figure:
artifact_path:
artifact_sha256:
git_commit:
dataset_manifest_sha256:
split_sha256:
model_id_and_revision:
checkpoint_sha256:
command:
seed_or_seed_set:
hardware:
software_environment:
evaluation_script:
bootstrap_unit_and_repetitions:
verified_by:
verification_date:
```

## Known source inconsistency

The WACV PDF and the checked-in LaTeX-generated rows are not numerically
identical. In particular, the repository contains pending Phi/LLaVA entries and
selector rows with zero-valued task fields, whereas the PDF shown to reviewers
contains different completed tables. This must be resolved by tracing raw
prediction artifacts. Manual reconciliation or number estimation is forbidden.

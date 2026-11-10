# Ten-Day Completion Plan

The goal is a scientifically complete internal draft in ten days, leaving the
remaining time for advisor review, reruns, and writing refinement. Each day has
a hard exit criterion. Work that fails the criterion rolls forward; prose does
not conceal missing evidence.

## Day 1 - Freeze history and recover provenance

- Preserve WACV submission on `main`.
- Inventory datasets, manifests, predictions, checkpoints, prompts, and logs.
- Reconcile the PDF/source table mismatch.
- Hash every recoverable primary artifact.
- Freeze IJCAI research question and primary metrics.

**Exit:** provenance report identifies the source of every retained WACV number
or marks it unusable.

## Day 2 - Data, split, and detector audit

- Re-run annotation, duplicate, and source-leakage checks.
- Freeze source splits and manifests.
- Produce crop- and size-stratified detector transfer results.
- Implement detector-only source predictions.

**Exit:** `data_audit.json`, split hashes, and detector baseline table pass
automated validation.

## Day 3 - Source reducer and deterministic baselines

- Implement overlap-aware count fusion and per-field source aggregation.
- Add no-accepted-tile review behavior and conflict tests.
- Evaluate detector-only and deterministic rule baselines.

**Exit:** source reducer is unit-tested, frozen, and produces one record per
source.

## Day 4 - Selector policies

- Verify existing selector audit.
- Add diversity-aware/uncertainty-aware policy.
- Run K and rho validation sweeps with paired source bootstrap.
- Freeze the primary routing policy without test feedback.

**Exit:** complete validation Pareto plot and signed policy-freeze record.

## Day 5 - Directed transfer

- Run or recover M->M, A->A, M->A, A->M, and pooled experiments.
- Generate paired transfer drops and scale/density diagnostics.

**Exit:** complete transfer matrix with no pending cells and immutable artifacts.

## Day 6 - Reliability

- Fit all gates on validation records only.
- Freeze the accepted-risk target.
- Evaluate test risk--coverage once.
- Report accepted sources and human-review burden.

**Exit:** main-paper risk--coverage figure and fixed-risk table are complete.

## Day 7 - VLM necessity and efficiency

- Compare detector-only, deterministic, and detector+VLM systems.
- Complete the model ladder only where artifacts are valid.
- Measure detector-to-decision latency, memory, calls, and throughput.

**Exit:** the paper either demonstrates VLM value or adopts the predeclared
narrower routing-only framing.

## Day 8 - Failure audit and first full paper

- Complete frozen balanced failure sampling and adjudication.
- Generate qualitative panels from the frozen rule.
- Write the full seven-page IJCAI draft with no placeholders.

**Exit:** every claim maps to a verified ledger entry; the paper compiles in the
official template within the page limit.

## Day 9 - Internal red-team review

- Conduct reviewer-style checks for novelty, correctness, baselines, leakage,
  reproducibility, anonymity, and overclaiming.
- Verify all table/figure values against artifacts.
- Run an independent compile and PDF visual audit.

**Exit:** zero unresolved critical findings and zero untraceable numbers.

## Day 10 - Advisor package

- Deliver manuscript, supplement, anonymous code snapshot, result ledger,
  response-to-WACV-review matrix, and open-risk list.
- Record advisor questions without editing results defensively.

**Exit:** advisor receives one reproducible package and a short list of genuine
scientific decisions, not unfinished experiments.

## Daily cadence

- 09:00: artifact/status check and compute allocation.
- 13:00: midpoint verification; stop invalid runs early.
- 18:00: commit artifacts, update ledger, and write only supported findings.
- 20:00: independent sanity check and next-day queue.

## Final pre-submission gates

- Abstract registered by January 4, 2027, 23:59 AoE.
- Full paper submitted by January 11, 2027, 23:59 AoE.
- Seven body pages and at most two reference pages.
- Anonymous PDF metadata, paper, supplement, paths, and code.
- No acknowledgements or contribution statement in the review submission.
- No dual submission during the IJCAI review period.
- Reproducibility checklist completed.
- Every numerical claim verified against a hashed artifact.

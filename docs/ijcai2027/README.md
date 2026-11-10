# OrnaScout IJCAI 2027 Revision Control Center

This directory governs the revision of the WACV 2027 OrnaScout submission for
possible submission to IJCAI 2027. It is deliberately separate from
`submission/wacv2027/`, which is preserved as a historical snapshot.

Manuscript rewriting is currently gated by the WACV repair review in
`WACV_revision/`. That package must be approved before the IJCAI paper
inherits any scientific claim, table, or method description.

## Non-negotiable submission constraints

- Abstract registration deadline: **January 4, 2027, 23:59 AoE**.
- Full paper deadline: **January 11, 2027, 23:59 AoE**.
- Main-track length: **7 body pages plus at most 2 reference pages**.
- Review is double blind. The paper, metadata, supplementary files, code, and
  paths must not disclose authors or institutions.
- The paper must be self-contained. Supplementary material may support the
  paper, but reviewers are not required to read it.
- IJCAI uses a summary-reject phase. The decisive evidence must therefore be
  visible in the seven-page main paper.

Official sources:

- <https://2027.ijcai.org/ijcai-2027-call-for-papers-main-track/>
- <https://2027.ijcai.org/reproducibility/>
- <https://www.ijcai.org/authors_kit>

The unmodified official template is stored in
`submission/ijcai2027/template/`.

## Scientific decision

The revision will not argue that exploit--explore is universally superior.
The defensible contribution is a **fixed-budget evidence-allocation and
selective-decision framework** that exposes and controls a Pareto trade-off
among task utility, spatial diversity, negative evidence, accepted risk, and
compute.

The paper can make a cross-crop reliability claim only after it contains:

1. a completed M->M, A->A, M->A, and A->M transfer matrix;
2. a completed risk--coverage evaluation with predeclared operating points;
3. a frozen, evaluated source-level reducer;
4. detector-only and deterministic aggregation baselines; and
5. a result ledger proving the provenance of every number.

## Files in this directory

- `SECTION_AUDIT.md`: required revisions for every paper section.
- `CLAIM_EVIDENCE_LEDGER.md`: claim-to-result contract and claim status.
- `EXPERIMENT_MATRIX.md`: mandatory runs, controls, metrics, and artifacts.
- `TEN_DAY_PLAN.md`: execution schedule and daily acceptance gates.

## Integrity rule

The attached WACV PDF is the historical record of what reviewers saw. The
repository source currently contains numerical rows that do not match that
PDF, including pending model rows and degenerate selector values. Neither is
to be copied into the IJCAI paper without regeneration from frozen prediction
artifacts. Each final value must be imported from a versioned result file and
must carry its generating command, commit, manifest hash, split hash, model
identifier, seed, and evaluation-script version.

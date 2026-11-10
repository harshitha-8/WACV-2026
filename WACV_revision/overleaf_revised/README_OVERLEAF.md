# OrnaScout Reviewer-Driven WACV Revision

Upload the contents of this folder directly to Overleaf and set `main.tex` as
the main document.

## Status

This is a scientifically restructured working draft, not a submission-ready
paper. Red `[PENDING: ...]` markers and red dashes identify required experiment
artifacts. They must never be interpreted as zero and must never be replaced by
estimated values.

`IMPLEMENTATION_STATUS.md` records the boundary between checked-in code and the
corrected target method. Method text is not completion evidence. Every final
number or figure series must have a completed row in
`RESULT_PROVENANCE_REGISTRY.csv`.

The WACV architecture, figures, bibliography style, references, and official
style file are included. The manuscript now contains:

- a bounded precision-agriculture task definition;
- detector-only and deterministic source baselines;
- coordinate-aware spatial and diversity-aware selection policies;
- distinct constraint-satisfaction and strict-schema metrics;
- overlap-aware source reduction;
- validation cross-fitting for the reliability gate;
- directed M->M, A->A, M->A, and A->M evaluation;
- risk--coverage and fixed-risk operating-point tables;
- end-to-end efficiency and review-workload requirements; and
- explicit numerical provenance rules.

## Before submission

1. Complete every item in `REVISION_CHECKLIST.md`.
2. Fill every required artifact in `EXPERIMENTS_TO_FILL.md`.
3. Follow `NUMERICAL_INTEGRITY.md` for every number.
4. Reconcile every method statement with `IMPLEMENTATION_STATUS.md` and tests.
5. Complete `RESULT_PROVENANCE_REGISTRY.csv`.
6. Remove every `\pending`, `\pendingcell`, and `\draftnote` occurrence.
7. Regenerate the PDF and independently verify all claims, tables, figures,
   references, anonymity, page limit, and metadata.

## Preserved history

The original WACV source is not modified by this project. This folder is a
separate revision workspace created from the submitted Overleaf package.

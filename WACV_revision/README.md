# WACV Revision Workspace

This is the authoritative workspace for revising the rejected WACV manuscript.
It converts the reviews, submitted PDF, checked-in LaTeX, and implementation
audit into a concrete repair specification and a reviewer-driven Overleaf
draft.

The historical manuscript under `submission/wacv2027/` remains unchanged.
Continue manuscript edits only in `overleaf_revised/`. The ZIP in this folder
is an export snapshot and must be regenerated after source changes; it is not
the editing source.

## Workspace map

| Location | Role | Edit? |
|---|---|---|
| `submission/wacv2027/` | Frozen record of the submitted paper and supplement | No |
| `WACV_revision/overleaf_revised/` | Active WACV revision manuscript | Yes |
| `WACV_revision/*.md` | Review, experiment, equation, table, and approval specifications | Yes |
| `WACV_revision/OrnaScout_WACV_Revised_Overleaf_Draft.zip` | Last verified Overleaf export | Regenerate only |
| Repository Python modules | Version-controlled implementation | Edit through reviewed changes |
| `../WACV_project_pipeline/` | Large local datasets, outputs, model runs, and recovery notebooks | Run experiments; do not treat as manuscript source |
| `../WACV_project_archive/` | Obsolete pre-relabel environment snapshot | Do not use |
| `../WACV-2026-public/` | Older clone of the public repository | Do not continue revision there |

## Why the work remains viable

The positive reviews correctly identify a publishable systems idea: fixed-
budget evidence allocation for high-resolution UAV imagery, structured compact-
VLM outputs, hard-negative evaluation, and abstention. This aligns with the
WACV application-track criteria of systems-level innovation, a novel or
reformulated application, and comparative assessment.

The rejection was driven by completeness and evidential support, not by a
finding that the central problem was unimportant. The repair must therefore
turn the paper from a promising system description into a complete,
source-level, reproducible evaluation.

## Review order

1. `COMPREHENSIVE_GAP_AUDIT.md`
2. `MASTER_REPAIR_BLUEPRINT.md`
3. `TASK_SCHEMA_AND_UNIT_FREEZE.md`
4. `VENUE_RUBRIC_ALIGNMENT.md`
5. `REVIEW_TO_ACTION_MATRIX.md`
6. `METHOD_EQUATION_AUDIT.md`
7. `IMPLEMENTATION_AND_TEST_PLAN.md`
8. `TABLE_FIGURE_PLAN.md`
9. `EXPERIMENT_EXECUTION_SPEC.md`
10. `RESULT_PROVENANCE_REGISTRY.csv`
11. `SCIENTIFIC_WRITING_STANDARD.md`
12. `AUTHOR_APPROVAL_CHECKLIST.md`

## Governing rule

The draft may be revised structurally, but no result claim is promoted and no
pending cell is filled until the scientific task, primary endpoint,
source-level reducer, baseline set, and claim boundaries are approved. No
numerical value is copied from the submitted source or PDF unless it is traced
to a frozen artifact.

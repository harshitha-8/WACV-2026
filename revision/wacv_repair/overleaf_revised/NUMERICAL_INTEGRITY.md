# Numerical Integrity Contract

The submitted WACV PDF and the previous checked-in generated rows are not a
consistent numerical record. The revised paper must not choose between them by
inspection. Each result must be regenerated or recovered from raw predictions.

For every table row or figure series, record:

```text
table_or_figure:
artifact_path:
artifact_sha256:
git_commit:
dataset_manifest_sha256:
source_split_sha256:
model_id_and_revision:
checkpoint_sha256:
command:
seed_or_seed_set:
hardware:
software_environment:
evaluation_script_and_version:
bootstrap_unit_and_repetitions:
verified_by:
verification_date:
```

## Prohibited practices

- estimating missing model performance from publications or model cards;
- changing a value to make the narrative more attractive;
- treating a missing result as zero;
- manually copying numbers without a checked artifact;
- selecting hyperparameters on the test set;
- changing metrics after inspecting test outcomes; and
- reporting tile-level uncertainty as source-level uncertainty.

## Release check

Before export, run a project-wide search for `PENDING`, `pendingcell`,
`draftnote`, `TBD`, `TODO`, and `--` in numeric cells. The submission is blocked
until each occurrence is resolved and independently verified.

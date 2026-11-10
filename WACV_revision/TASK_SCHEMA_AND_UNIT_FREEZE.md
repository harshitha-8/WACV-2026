# Task, Schema, and Evaluation-Unit Freeze

## Proposed scientific unit

One prediction is made per **source UAV image**. The detector observes every
candidate tile; the VLM observes only the selected budget. The output concerns
the complete source image, while the inspected VLM footprint is recorded
separately. Uninspected area is unknown to the VLM and must never be encoded as
empty evidence.

This proposal requires author approval and a tested source reducer. Until then,
the existing implementation supports only tile-level claims.

## Frozen field contract to approve

| Field | Reference | Evaluated | Gate candidate | Important boundary |
|---|---|---:|---:|---|
| Plant presence | any verified source box | yes | yes | inventory presence only |
| Continuous count | unique fused source boxes | yes | yes | numerical error required |
| Count interval | training-frozen count bins | yes | yes | intervals published |
| Density class | training-frozen count/valid-area rule | yes | yes | not plant health |
| Annotated coverage | clipped box union/valid source area | yes | yes | not canopy segmentation |
| Crop identity | metadata/evaluation stratum | no task claim | optional diagnostic | disclose whether supplied to VLM |
| Visible evidence text | no independent label | audit only | no | never scored as semantic truth |
| Self-reported confidence | model output | calibration diagnostic | candidate | not a calibrated probability by default |
| Priority/recommendation | unsupported | no | no | remove from scientific claims |
| Human review | gate decision | risk/coverage output | output | not a biological label |

## Freeze questions

- [ ] Are count bins retained, and what are the training-only cut points?
- [ ] Is density redundant with count, or does valid area create a distinct task?
- [ ] Is box-union coverage scientifically useful enough to retain?
- [ ] Is crop identity visible to the VLM prompt?
- [ ] Is the source output a census estimate, an evidence summary, or both?
- [ ] What minimum accepted-source count and target risk are operationally useful?
- [ ] Which fields define strict source-record error?

## Required generated artifacts

- `task_schema.json` with field types, values, versions, and constraints;
- `label_rules.json` with thresholds and fitting split;
- `source_ground_truth.jsonl` with one row per source;
- `class_support.csv` by crop and partition;
- `prompt.txt`, `parser_version.json`, and `consensus_rule.json`; and
- tests proving that missing, malformed, unknown, and uninspected states remain
  distinct.

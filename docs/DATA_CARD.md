# Dataset Card

The relabeled dataset snapshot contains 297 matched Magnolia RGB/YOLO pairs and
121 matched Azalea pairs, for 418 labeled source images and 29,842 usable
one-class boxes. Magnolia contributes 15,644 boxes and Azalea contributes
14,198. Five zero-width rows are rejected without modifying the reviewed source
labels. One additional original Azalea RGB frame has no reviewed label and is
excluded. Three reviewed Azalea source images have empty label files; these are
valid negative images rather than missing annotations.

Magnolia uses the 5184 x 3888 RGB images and v3 reviewed labels. Azalea uses
the original 5280 x 3956 RGB frames paired by filename with the normalized
labels from `model_relabeled_review_azalea`; the 1024 x 767 review images are
excluded from model input. Normalized YOLO coordinates are resolution
independent because the original and review images preserve the same aspect
ratio.

Annotations provide one-class bounding boxes. Derived tile labels include
presence, count bin, density class, coverage class, boundary status, and hard
negative status. Annotated previews, `classes.txt`, macOS resource forks, and
unmatched files are excluded.

All splits occur at source-image level before tiling. Dataset versions should
record acquisition source, image dimensions, annotation counts, split seed,
and cryptographic or perceptual hashes used for leakage checks.

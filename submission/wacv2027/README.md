# OrnaScout WACV 2027 submission release

This directory is the canonical, source-only submission release. It replaces
the draft, recovery, Colab, and intermediate Overleaf archives that previously
accumulated throughout the project tree.

## Canonical packages

- `OrnaScout_Submission.zip`: main-paper Overleaf package. Compile `main.tex`.
- `OrnaScout__Supplementary_Submission.zip`: supplementary Overleaf package.
  Compile `supplementary.tex`.

The unpacked `main/` and `supplementary/` directories contain the exact source
trees used to produce those packages. Generated PDFs, LaTeX build products,
model weights, virtual environments, datasets, and experiment outputs are not
part of this release.

## Verification

Run the following commands from this directory before uploading:

```sh
unzip -t OrnaScout_Submission.zip
unzip -t OrnaScout__Supplementary_Submission.zip
shasum -a 256 OrnaScout_Submission.zip OrnaScout__Supplementary_Submission.zip
```

Checksums are recorded in `SHA256SUMS` and should be regenerated whenever a
package is intentionally changed.

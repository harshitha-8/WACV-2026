# Implementation Status Boundary

This Overleaf tree is a reviewer-driven target manuscript, not evidence that
every described correction is implemented.

## Confirmed in the current code

- source images are split before tiling;
- detector evidence and fixed tile budgets exist;
- prompt-based VLM generation and post-generation JSON extraction exist;
- repeated generations can be stored; and
- tile-level task and gate diagnostics exist.

## Required before final-result language

- true coordinate-aware spatial selection;
- order-invariant per-source stochastic seeds;
- strict schema validity distinct from partial constraint satisfaction;
- a frozen repeat-consensus rule where one repeat is not perfect consistency;
- detector-only source-record prediction;
- overlap-aware source-level reduction;
- source-grouped cross-fitted gate scoring and threshold selection;
- directed transfer and source-level risk/coverage evaluation; and
- programmatic tables/figures backed by the provenance registry.

Until these are complete, corrected method text is a specification and every
result placeholder remains a submission blocker.

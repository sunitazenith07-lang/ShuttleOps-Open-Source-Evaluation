# Approach

## Baseline

I installed the development dependency and ran `python -m pytest -q` and `python -m main` before changing the starter. The baseline was 164 passed and 65 failed. The demo did return an assignment, which showed that the basic ETA path worked while validation and cancellation cases did not.

## Codebase understanding

I traced `main.py` through `fixtures.sample_inputs()` to `assign_order()`. `estimate_eta()` calculated both travel legs and `process_cancellation()` copied and changed partner state. I also read the acceptance matrix, edge-case tests, data schema, and CI workflow. The larger synthetic dataset confirms that missing routes, capacity limits, invalid values, ties, and duplicate cancellations are intentional cases.

## Implementation

The root cause was that the starter accepted every partner with two route keys, regardless of active state, capacity, malformed values, or invalid times. It also appended every cancellation event even when the same event had already been processed.

I added small validation helpers for identifiers and finite, non-negative time values. Assignment now requires an explicitly active partner, a positive integer capacity, a list of active orders below that capacity, and a valid ETA. Selection still uses ETA then partner ID. Cancellation now returns early for an already-recorded event and keeps the input record unchanged.

## Decisions and verification

I kept the existing dictionary API and did not add a batch feature because the required behaviour is per-order dispatch. I treated truthy values such as `"yes"` as invalid active states and missing data as unknown rather than zero.

I added regression tests for malformed records, strict active state, and non-mutating duplicate cancellation. The final run was 232 passed in 0.49s; `python -m main` returned `P-2` with pickup 13 and ETA 35. The remaining limitation is that this in-memory module does not make concurrent capacity reservations atomic.

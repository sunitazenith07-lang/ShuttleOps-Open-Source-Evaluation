# Approach

## 1. Setup and baseline
- Created and activated a Python 3.10+ virtual environment, installed `requirements-dev.txt`.
- Ran the untouched starter: `65 failed, 164 passed`.
- Read `models.py`, `fixtures.py`, `main.py` and `service.py` before editing anything.

## 2. ETA trace (sample fixture, now = 0)
Order O-7: restaurant R-2, destination Z-9, prep 10.
- P-2 (zone Z-1): pickup = 0 + 8 + 5 = 13, ETA = 13 + 10 + 12 = 35
- P-1 (zone Z-3): pickup = 0 + 12 + 2 = 14, ETA = 14 + 10 + 12 = 36
- P-2 wins. `python -m main` prints exactly this result.

## 3. Diagnosis: grouping failures by root cause
The 65 failures reduced to five causes, found by reading the tracebacks and the
starter's own comments rather than fixing tests one by one:
1. Travel times checked for presence only, never for validity.
2. Prep time never validated, and a missing value defaulted to 0.
3. `now` never validated.
4. `assign_order` ignored order IDs, the `active` flag and capacity.
5. `process_cancellation` recorded `event_id` but never checked it.

## 4. Fix
Each cause was fixed in the function that owns it:
- `estimate_eta`: validate `now`, prep, workload and both legs.
- `assign_order`: validate the order, filter inactive and full partners, tolerate
  empty/None/malformed input, return per-partner rejection reasons in `details`.
- `process_cancellation`: return early when `event_id` was already processed.

The ETA formulas and the tie-break key `(eta, partner_id)` were left unchanged,
because the formula tests and tie-break tests already passed on the starter.

## 5. Verification
- Added `tests/test_regression.py` (21 tests); no existing test was edited.
- Final run: `250 passed`.
- `python -m main` still prints P-2, pickup 13, ETA 35.
- Ran a no-eligible scenario (P-2 full, P-1 without a route) and recorded the real
  output in `DISPATCH_NOTES.md`.

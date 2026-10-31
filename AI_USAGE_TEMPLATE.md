# AI-Use Declaration

For each tool/model or source, state the purpose, what you independently verified or changed, any displayed credits/tokens (or “not available”), and one suggestion accepted, changed or rejected with your reason. Never include secrets or private personal data.

## Tool / Model Used
- **Model:** Google Gemini
- **Displayed Credits / Tokens:** Not available

## Purpose
- Used to review the starter codebase (`models.py`, `service.py`, `fixtures.py`, `main.py`), structure input and eligibility validation in `estimate_eta` and `assign_order`, implement idempotency in `process_cancellation`, handle edge cases (`bool`, `inf`, `nan`, malformed dictionaries), and organize changes across incremental Git branches.

## What Was Independently Verified or Changed
- Independently verified all arithmetic formulas for pickup (`now + leg1 + workload`) and total ETA (`pickup + prep + leg2`) against the sample data in `fixtures.py`.
- Ran `python -m pytest -q` against `tests/test_acceptance_matrix.py`, discovered two failing edge-case tests (`test_invalid_or_missing_travel_time_rejected[1-inf]` and `test_preparation_time_validation[inf]`), and verified that adding `math.isfinite(val)` resolved both failures.
- Checked that `process_cancellation` uses `deepcopy` to avoid mutating the caller's original partner dictionary and clamps `workload_minutes` at `0`.

## Suggestion Accepted, Changed, or Rejected
- **Accepted Suggestion:** Checking `not isinstance(val, bool)` and `math.isfinite(val)` inside `_is_non_neg_num(val)`.
  - **Reason:** In Python, `bool` is a subclass of `int` (`True == 1`) and `float('inf') >= 0` evaluates to `True`. Accepting both guards prevented boolean values and infinite floats (`inf` / `nan`) from bypassing numeric time validation.
- **Changed Suggestion:** Initially, `_is_non_neg_num(val)` only checked `not isinstance(val, bool) and isinstance(val, (int, float)) and val >= 0`. After running the acceptance test matrix, I updated this helper to also enforce `math.isfinite(val)`.
  - **Reason:** Without `math.isfinite(val)`, `float('inf')` passed the `>= 0` check in `estimate_eta` and `assign_order`, causing `test_acceptance_matrix.py` to fail on infinite preparation and travel times.
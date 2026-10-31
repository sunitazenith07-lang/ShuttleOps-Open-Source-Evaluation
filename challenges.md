# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
What candidate-selection, ETA, capacity, missing-data, tie-breaking, or cancellation case was difficult to understand?

- **Challenge 1 (Time Validation Edge Cases with `float('inf')` and `bool`):** When validating preparation and travel times in `estimate_eta` and `assign_order`, checking that a value is a non-negative number (`isinstance(val, (int, float)) and val >= 0`) appeared sufficient at first, but still allowed `True`/`False` booleans and positive infinity (`float('inf')`) to pass validation as eligible time values.
- **Challenge 2 (Guard Clause Polarity in Partner Filtering):** When writing `continue` guard clauses inside `assign_order` for partner active status (`if not partner.get('active', False): continue`) and capacity (`if len(active_order_ids) >= capacity: continue`), it was initially confusing why capacity used `>=` instead of `<=` and how `not` interacted with the default `False` fallback in `.get('active', False)`.

## 2. Evidence
Summarize the relevant assertion, log, output, or minimal reproducible example.

- After implementing initial numeric checks (`not isinstance(val, bool) and isinstance(val, (int, float)) and val >= 0`), running `python -m pytest -q` produced the following 2 failures in the acceptance matrix:
  ```text
  FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[1-inf] - assert True is False
  FAILED tests/test_acceptance_matrix.py::test_preparation_time_validation[inf] - assert True is False
  ```
- Additionally, while refactoring the validation logic into helper functions (`_valid_id` and `_valid_time`), running the tests when the helper definitions were missing from the top of `service.py` raised a `NameError` (`valid_id and valid_time not defined`).

## 3. What I tried
List debugging steps or experiments you actually performed and what each one showed.

1. **Step 1 — Basic `< 0` and `None` checks:** Initially checked `min(now, leg1, leg2, workload, prep) < 0` in `estimate_eta` alongside `if not partner.get('active', False)` and `len(active_order_ids) >= capacity` in `assign_order`. Testing showed this failed when order fields were invalid, when booleans were passed as times, or when `None` was passed into `min()`.
2. **Step 2 — Adding `isinstance` and boolean exclusion:** Added `not isinstance(val, bool) and isinstance(val, (int, float)) and val >= 0` and pre-loop order ID validation. This passed almost the entire test suite, except for the two parameterized `[inf]` test cases in `test_acceptance_matrix.py`.
3. **Step 3 — Inspecting `float('inf')` behavior in Python:** Verified that in Python, `isinstance(float('inf'), float)` is `True` and `float('inf') >= 0` is also `True`, which meant `pickup + prep + leg2` evaluated to `inf` and returned `'eligible': True` instead of `'eligible': False`.

## 4. Resolution
What was the root cause? What did you change, and why did it address the cause rather than hide the symptom?

- **Root Cause:** Python's `float` type includes IEEE 754 special values (`inf`, `-inf`, and `nan`), and `float('inf') >= 0` evaluates to `True`. Similarly, Python's `bool` type is a subclass of `int` (`True == 1`, `False == 0`). Standard type and `>= 0` comparisons do not filter out infinite floats or booleans.
- **Change Made:** Imported `math` in `service.py` and updated the centralized validation helper `_is_non_neg_num(val)` to check `math.isfinite(val)`:
  ```python
  def _is_non_neg_num(val):
      return not isinstance(val, bool) and isinstance(val, (int, float)) and math.isfinite(val) and val >= 0
  ```
- **Why this addresses the root cause:** Instead of hardcoding a check for `val != float('inf')` in one place, adding `math.isfinite(val)` inside `_is_non_neg_num(val)` guarantees that every numeric time field across the entire service (`now`, `leg1`, `leg2`, `workload_minutes`, `prep_minutes`, and `minutes_by_order`) rejects `inf`, `-inf`, and `nan` at the validation boundary.

## 5. Proof and regression prevention
Which test(s) demonstrate the fix? What related case might still break?

- **Tests demonstrating the fix:**
  - `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[1-inf]`
  - `tests/test_acceptance_matrix.py::test_preparation_time_validation[inf]`
  - Re-running `python -m pytest -q` after adding `math.isfinite(val)` resulted in all acceptance matrix tests passing with `0 failed, 0 errors`.
- **Related case that could still break if not careful:**
  - Stringified numbers (e.g., `prep_minutes = "10"`) or `Decimal` objects from external JSON/database payloads: `_is_non_neg_num` strictly checks `isinstance(val, (int, float))`, so `Decimal('10')` or `"10"` will be rejected unless converted at the API boundary.
  - Lexicographic tie-breaking with multi-digit IDs: `str(item['partner_id'])` sorts `'P-10'` before `'P-2'` because `'1' < '2'` in ASCII order (which matches the specification's ascending lexicographic requirement, but differs from natural numeric sorting).

## 6. Unresolved challenge or next step
State remaining limitations and how you would investigate them next.

- **State Mutation vs. Pure Return in `assign_order`:** `assign_order` returns the assignment decision dictionary (`{'order_id': ..., 'partner_id': ..., 'pickup_minutes': ..., 'eta_minutes': ..., 'reason': 'assigned'}`) without mutating the selected partner's `active_order_ids`, `workload_minutes`, or `minutes_by_order`. Next, I would investigate adding a state-committing function (e.g., `apply_assignment(partner, order, estimate)`) so that sequential calls to `assign_order` automatically reflect updated partner capacity and per-order workload minutes that `process_cancellation` later relies on.
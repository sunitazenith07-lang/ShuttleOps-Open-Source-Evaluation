# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
What candidate-selection, ETA, capacity, missing-data, tie-breaking, or cancellation case was difficult to understand?
- I did not hit a major blocker, so the trickiest edge case was handling Python's type edge cases across `estimate_eta` and `assign_order`—specifically why `True`, `False`, `float("nan")`, and `float("inf")` were passing numeric checks, and why truthy values for `active` or `capacity` behaved differently in the acceptance matrix tests.

## 2. Evidence
Summarize the relevant assertion, log, output, or minimal reproducible example.
- In `test_acceptance_matrix.py`, tests like `test_capacity_boundary_matrix[True-0]`, `test_current_time_validation[True]`, `test_preparation_time_validation[nan]`, and `test_invalid_or_missing_travel_time_rejected[1-inf]` all failed with `assert True is False` or `AssertionError: assert 'P' is None` because Python's `isinstance(True, int)` evaluates to `True` and `NaN`/`inf` are valid `float` instances. Also, `test_duplicate_cancellation_is_idempotent_across_workloads` failed with `AssertionError: assert ['C', 'C'] == ['C']`.

## 3. What I tried
List debugging steps or experiments you actually performed and what each one showed.
- First, I ran `python -m pytest -q` from the root directory and got a file-not-found error until I moved into the `SmartDispatch-Open-Source-Evaluation` subfolder.
- Next, I inspected the 65 failure tracebacks and checked how `isinstance(val, (int, float))` behaves with `True`, `NaN`, and `inf`, which showed that standard `isinstance` checks let booleans and non-finite floats slip through.
- I also checked `test_inactive_partners_never_selected` and `test_capacity_boundary_matrix` to see exact parameter lists (`[False, True, 0, 1, None, "no", "yes"]` and capacities like `1.5`, `True`, `0`, `-1`).

## 4. Resolution
What was the root cause? What did you change, and why did it address the cause rather than hide the symptom?
- The root cause was that `service.py` performed arithmetic and candidate selection without strict type/domain guards, and `process_cancellation` appended `event_id` before checking if it was already processed.
- I added centralized helper functions (`_is_valid_number`, `_is_valid_time`, `_valid_order`, `_valid_partner_for_assignment`) that explicitly exclude `isinstance(value, bool)`, check `value == value` and `abs(value) != float("inf")` to block `NaN`/`inf`, enforce `capacity >= 1` as an `int`, and added an early return in `process_cancellation` if `event_id in processed_cancellation_ids`. This fixed the underlying validation logic across all functions rather than hard-coding test values.

## 5. Proof and regression prevention
Which test(s) demonstrate the fix? What related case might still break?
- Running `python -m pytest -q` passed all tests in `test_contract.py`, `test_edge_cases.py`, and `test_acceptance_matrix.py` (including `test_capacity_boundary_matrix`, `test_current_time_validation`, `test_preparation_time_validation`, and `test_duplicate_cancellation_is_idempotent_across_workloads`).
- A related case that could still break in production is if a partner's `workload_minutes` is out of sync with the sum of `minutes_by_order` before a cancellation arrives.

## 6. Unresolved challenge or next step
State remaining limitations and how you would investigate them next.
- Currently, `assign_order` evaluates one order at a time greedily and does not mutate the assigned partner's `active_order_ids` or `workload_minutes` in place. Next, I would investigate how sequential multi-order dispatches update partner state between calls and test batch assignment scenarios.

If you did not encounter a major blocker, say so honestly and describe the hardest edge case you deliberately tested and what it taught you. Do not manufacture a story.
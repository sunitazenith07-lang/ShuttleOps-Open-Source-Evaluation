# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
What candidate-selection, ETA, capacity, missing-data, tie-breaking, or cancellation case was difficult to understand?
The biggest challenge was dealing with Python's quirky type system, missing data, and special numeric values (`float('nan'`, `float('inf'`) during ETA and capacity checks. 
Two major issues popped up:
1. The `nan` Trap: Standard checks like `leg1 < 0` failed because in Python, any comparison with `nan` always returns `False`, allowing invalid numbers to slip through.
2. The Boolean Subclass Trap: Python treats booleans like `True` as numbers (`isinstance(True, int)` is `True`). Because of this, invalid values like `True` or floats (`1.5`) were incorrectly accepted as valid partner capacities or delivery times.
## 2. Evidence
Summarize the relevant assertion, log, output, or minimal reproducible example.
When running the test suite initially, several test cases failed due to edge-case inputs:
- Travel time validation failed when `nan` or `inf` was passed instead of valid numbers.
- Partner capacity checks failed when invalid types like boolean `True` or decimal `1.5` were passed instead of a whole number
- some more testcase failure:
- `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[nan-1]` -> `assert True is False`
- `tests/test_acceptance_matrix.py::test_preparation_time_validation[inf]` -> `assert True is False`
- `tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[True-0]` -> `AssertionError: assert 'P' is None`
- `tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[1.5-0]` -> `AssertionError: assert 'P' is None`

## 3. What I tried
List debugging steps or experiments you actually performed and what each one showed.
-Attempt 1: I got nothing and analysed the failure and code after many attempts
Attempt approx 10: Initially used basic comparison operators (`< 0` and `>=`) on travel times and capacity values assuming standard numeric inputs. This failed because `nan` bypassed the `< 0` check and boolean/float capacities bypassed integer checks.
- Attempts approx 25: Added basic `isinstance(..., (int, float))` checks, which helped filter out strings, but still allowed `bool` values (due to Python inheritance) and special floats (`nan`/`inf`) to pass through.
-  Attempts even i am not able to recognize how many attempts: Investigated missing travel route behavior and whitespace-only IDs (`"   "`), which initially bypassed basic truthiness checks like `if not order.get(...)`.
## 4. Resolution
What was the root cause? What did you change, and why did it address the cause rather than hide the symptom?
To fix these issues cleanly without side effects, I implemented:
- Finite Time Checks: Used `math.isfinite()` combined with boolean guards to block invalid `nan` and `inf` time values.
- Strict Capacity Rules: Enforced that partner capacity must be a true integer (rejecting decimals like `1.5` and booleans like `True`).
- ID Sanitization/ finder: Applied `.strip()` to correctly catch and reject blank or whitespace-only ID strings.
- Idempotent Cancellations or cancellations merge of a cancellation: Added an early-return check for `event_id` to prevent duplicate cancellations from releasing workload twice
## 5. Proof and regression prevention
Which test(s) demonstrate the fix? What related case might still break?
After applying these specific guards, running `python -m pytest -q` resulted in all 229 test cases passing successfully, confirming that malformed types, boundary violations, and duplicate cancellations are  handled perfectly.
## 6. Unresolved challenge or next step
State remaining limitations and how you would investigate them next.
## 6. Unresolved challenge or next step
No major blockers remain for the current scope. Agar koi edge-case ya scaling requirement future mein aati hai jise abhi handle nahi kiya gaya, toh main use aur better tareeke se design patterns aur data structures (jaise `set` lookups) ke sath handle karne ki koshish karunga. 
If you did not encounter a major blocker, say so honestly and describe the hardest edge case you deliberately tested and what it taught you. Do not manufacture a story.
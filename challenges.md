# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
The most subtle and confusing challenge encountered was **Python's numeric type hierarchy regarding booleans and non-finite floats (`NaN` / `inf`) in time validation**, alongside ensuring **cancellation idempotency across both active and unknown order identifiers**.

Specifically:
1. In Python, `bool` is a direct subclass of `int` (`issubclass(bool, int) is True`). Consequently, a standard type check such as `isinstance(val, (int, float)) and val >= 0` evaluates to `True` when `val` is `True` or `False`. This caused boolean flags passed into time parameters (`leg1=True`, `prep=True`, `now=True`) to be silently coerced to $1$ or $0$ minutes instead of being rejected as malformed data.
2. Floating-point `float("nan")` satisfies `isinstance(val, float)`, but comparing `val >= 0` evaluates to `False`, while `float("inf")` satisfies `val >= 0` and produces infinite ETAs.
3. In `process_cancellation`, the interaction between duplicate events and non-existent orders required ensuring that duplicate event IDs are never appended twice, while distinct event IDs for orders not currently active must record the event without corrupting the workload.

## 2. Evidence
During initial test execution, multiple parameterized matrix tests failed with unexpected type coercion and unhandled operations:
```text
FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[True-1] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[1-False] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_preparation_time_validation[True] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_current_time_validation[True] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_preparation_time_validation[inf] - assert True is False
FAILED tests/test_contract.py::test_duplicate_cancellation_is_idempotent - AssertionError: assert (0 == 0 and ['C1', 'C1'] == ['C1']
```

## 3. What I tried
1. **Initial attempt with `try...except TypeError`**: Attempted to let arithmetic run and catch errors.
   - *Result*: Failed because `True + 10` succeeds without raising an exception in Python, producing `11` instead of marking the candidate ineligible.
2. **Simple `isinstance(x, (int, float))`**:
   - *Result*: Failed because `isinstance(True, int)` is `True`, and `float("inf")` passed the non-negative check.
3. **Dedicated validation helper**:
   - Implemented `_is_valid_non_negative_number(val)`:
     ```python
     if val is None or isinstance(val, bool):
         return False
     if not isinstance(val, (int, float)):
         return False
     if not math.isfinite(val):
         return False
     return val >= 0
     ```
   - Tested systematically against `0`, `1.5`, `-1`, `None`, `"10"`, `True`, `False`, `float("nan")`, and `float("inf")`.

## 4. Resolution
- **Root Cause**: The starter code lacked explicit type guards and relied on Python's dynamic typing, which permits boolean-to-integer coercion and infinite float values. Furthermore, `process_cancellation` appended `event_id` unconditionally to `processed_cancellation_ids` without verifying if that event had already been processed.
- **Changes Made**:
  1. Guarded all time inputs (`now`, `prep_minutes`, `workload_minutes`, `leg1`, `leg2`) using `_is_valid_non_negative_number`.
  2. In `process_cancellation`, added an immediate guard:
     ```python
     if event_id in out['processed_cancellation_ids']:
         return out
     ```
  3. Ensured that `order_id` is only removed if present in `active_order_ids`, and that workload decrements are bounded by `max(0, current_workload - deduct)`.

## 5. Proof and regression prevention
- **Verifying Tests**:
  - `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected` (12 test combinations including booleans, `NaN`, and `inf`).
  - `tests/test_acceptance_matrix.py::test_current_time_validation` (13 test cases).
  - `tests/test_contract.py::test_duplicate_cancellation_is_idempotent`.
  - `tests/test_regression.py::test_edge_case_boolean_workload_rejected` and `test_regression.py::test_edge_case_cancellation_unknown_order_and_idempotency`.
- All 235 tests pass deterministically.

## 6. Unresolved challenge or next step
- **Future Scale**: In a high-throughput production environment with millions of events, searching `event_id in processed_cancellation_ids` (a list) scales with $O(N)$. For scale, `processed_cancellation_ids` should be backed by an $O(1)$ set or a distributed cache with TTL (e.g., Redis `SETNX`).
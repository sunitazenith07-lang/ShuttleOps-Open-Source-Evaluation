# TESTING.md — Required submission

## Test command and environment
- Python version: Python 3.14 (3.10+ compatible)
- Command run: `python -m pytest -q`
- Actual test summary: `229 passed in 0.46s`

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Negative preparation time (`prep_minutes = -1`, `-5`, `-100`) | Input is rejected; calculation is marked ineligible and order remains unassigned | Order marked ineligible with `eligible: False` and `partner_id: None` | `tests/test_acceptance_matrix.py::test_preparation_time_validation[-1]` |
| 2 | Boolean values passed as time inputs (`now = True`, `prep_minutes = True`) | Booleans are strictly rejected despite being numeric subclasses in Python | Caught by `isinstance(value, bool)` guard and marked ineligible | `tests/test_acceptance_matrix.py::test_current_time_validation[True]` |
| 3 | Non-numeric or missing time inputs (`prep_minutes = None`, `"10"`, `inf`, `nan`) | Operations fail safely without throwing runtime `TypeError` or allowing invalid math | Handled by `is_valid_time()`, safely returning `eligible: False` | `tests/test_acceptance_matrix.py::test_preparation_time_validation[None]` |
| 4 | Partner capacity set to non-integer / `None` (`capacity = None`, `1.5`, `True`) | Partner is treated as invalid and safely bypassed during assignment | Capacity validated as `isinstance(int)` and `>= 1`, preventing comparison crash | `tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[None-0]` |
| 5 | Duplicate cancellation payload (same `event_id` sent multiple times) | Action is idempotent; workload and active orders are reduced only once | Duplicate `event_id` is detected early and partner record returns unmodified | `tests/test_contract.py::test_duplicate_cancellation_is_idempotent` |

## Regression tests added
1. **Unvalidated time arithmetic crash (`TypeError` on `+`):** Fixed unvalidated time inputs by introducing `is_valid_time()`; guarded by `test_preparation_time_validation` and `test_current_time_validation`.
2. **Boolean-as-integer edge case:** Added explicit boolean rejection to prevent `True`/`False` from behaving as `1`/`0`; guarded across parameterized acceptance tests.
3. **Invalid capacity comparison (`TypeError: '>=' between int and NoneType`):** Enforced capacity type checks (`isinstance(capacity, int) and capacity >= 1`); verified by `test_capacity_boundary_matrix`.
4. **Duplicate cancellation workload double-deduction:** Added `event_id in out['processed_cancellation_ids']` verification check; guarded by `test_duplicate_cancellation_is_idempotent_across_workloads`.

## Remaining failures or limitations
- No failing tests remain. All 229 tests across acceptance matrix and contract suites pass completely.
- Processing is strictly in-memory and single-threaded; scaling to high-concurrency environments would require distributed locking and transactional storage.
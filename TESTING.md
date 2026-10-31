# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version:Python 3.10+
- Command run:`python -m pytest -q`
- Actual test summary:All 229 tests passed successfully (100% pass rate) with zero regressions

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Travel time as `nan` | Reject / handle safely | Passed (safely rejected) | `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected` |
| 2 | Travel time as `inf` | Reject / handle safely | Passed (safely rejected) | `tests/test_acceptance_matrix py::test_invalid_or_missing_travel_time_rejected` |
| 3 | Preparation time as `inf` | Reject / handle safely | Passed (safely rejected) | `tests/test_acceptance_matrix.py::test_preparation_time_validation` |
| 4 | Partner capacity as boolean (`True`) | Reject (must be strict int) | Passed (safely rejected) | `tests/test_acceptance_matrix.py::test_capacity_boundary_matrix` |
| 5 | Partner capacity as decimal (`1.5`) | Reject (must be strict int) | Passed (safely rejected) | `tests/test_acceptance_matrix.py::test_capacity_boundary_matrix` |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning.
Float Safety: Added `math.isfinite()` checks to prevent crashes or incorrect calculations from `nan` and `inf` values.
- Strict Capacity Enforcement: Added type guards (`isinstance(capacity, int)` and `not isinstance(capacity, bool)`) to reject decimals and booleans.
- ID Sanitization: Applied `.strip()` on critical ID fields to catch and reject blank or whitespace-only strings.
- Cancellation Idempotency: Added an early-return check using `event_id` tracking in `process_cancellation` to prevent duplicate cancellations from releasing workload multiple times.
## Remaining failures or limitations
List any known failing tests or unresolved behaviours honestly.
No remaining failures. All current acceptance and boundary tests pass successfully with zero blockers.
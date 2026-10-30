# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version: Python 3.13.3
- Command run: `python -m pytest -q`
- Actual test summary: 235 passed in 0.95s (100% pass rate, 0 failures, 0 errors)

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Negative preparation time (`prep_minutes = -5`) | Order rejected; partner not assigned (`partner_id is None`) | `partner_id: None, reason: invalid order or time fields` | `tests/test_contract.py::test_negative_prep_time_is_rejected` |
| 2 | Boolean passed as travel time (`leg1 = True`) | Route treated as invalid; candidate marked ineligible | `eligible: False, eta_minutes: None` | `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[True-1]` |
| 3 | Partner at full capacity (`len(active_order_ids) >= capacity`) | Partner excluded from assignment | Order unassigned (`partner_id: None`) | `tests/test_contract.py::test_full_partner_not_assigned` |
| 4 | Identical ETAs tie-breaking (`PARTNER-A` vs `PARTNER-B` both ETA 30) | Ties broken lexicographically by partner ID in ascending order | `PARTNER-A` selected consistently regardless of input list order | `tests/test_regression.py::test_regression_tie_breaking_lexicographical_stability` |
| 5 | Duplicate cancellation event (`event_id = "C-01"` processed 3 times) | Workload deducted once; event ID stored once; subsequent calls idempotent | `workload_minutes: 25, processed_cancellation_ids: ['C-01']` | `tests/test_regression.py::test_regression_cancellation_idempotency_multi_call` |

## Regression tests added
- Added `tests/test_regression.py` containing 6 comprehensive test functions:
  1. `test_regression_invalid_and_malformed_order_inputs`: Validates non-dict orders, empty IDs, whitespace IDs, negative/boolean prep times.
  2. `test_regression_partner_capacity_and_status`: Validates inactive partner variations, capacity boundary conditions, and invalid capacity values.
  3. `test_regression_missing_routes_never_zero`: Validates missing legs, negative travel times, and empty dictionaries.
  4. `test_regression_tie_breaking_lexicographical_stability`: Validates order-independent tie-breaking across permutations.
  5. `test_regression_cancellation_idempotency_multi_call`: Validates multiple repeat cancellation events and unknown order cancellations.
  6. `test_regression_synthetic_dataset_integration`: Validates end-to-end dispatch across synthetic records from `data/records.json`.

## Remaining failures or limitations
- None. All 235 tests pass cleanly.

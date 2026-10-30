# TESTING.md — Test Execution & Edge-Case Evidence

## Test command and environment
- **Python version:** Python 3.14.5 (tags/v3.14.5:5aa3ea7, Feb 10 2026, 17:16:36) [MSC v.1944 64 bit (AMD64)]
- **Command run:** `python -m pytest -q`
- **Actual test summary:** `238 passed, 1 warning in 0.44s`

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | **Boolean preparation time:** `prep_minutes=True` in `new_order("ORD-1", "REST-1", "DEST-1", prep_minutes=True)` | Rejected as invalid time (`eligible: False`, `eta_minutes: None`). Must not be treated as 1 minute. | `eligible: False`, `eta_minutes: None` | `tests/test_regression.py::test_regression_boolean_time_values_rejected` |
| 2 | **Invalid partner capacity types:** `capacity=True`, `capacity=1.5`, `capacity=0`, `capacity=-2` | Rejected as ineligible. Valid capacity must be strict integer >= 1. Order unassigned (`partner_id: None`). | `partner_id: None` across all invalid types | `tests/test_regression.py::test_regression_partner_capacity_type_safety` |
| 3 | **Duplicate cancellation event replay:** Replaying same `event_id="EVT-100"` twice for partner with active orders | Idempotent operation: workload deducted exactly once, event recorded only once in `processed_cancellation_ids`. | `workload_minutes: 15`, `processed_cancellation_ids: ["EVT-100"]` | `tests/test_regression.py::test_regression_cancellation_duplicate_id_and_different_order` |
| 4 | **Workload reduction exceeding current workload:** Partner `workload_minutes=5`, cancelled order has `minutes_by_order={"ORD-1": 20}` | Workload is safely floored at 0 and does not underflow to negative values. | `workload_minutes: 0` | `tests/test_regression.py::test_regression_cancellation_workload_clamped_to_zero` |
| 5 | **Missing travel route entry:** `travel` contains `(ZONE-A, REST-1)` but missing `(REST-1, DEST-1)` | Missing route is never treated as zero; candidate marked ineligible, order unassigned with reason. | `eligible: False`, `partner_id: None`, `reason: 'no eligible partner or missing time data'` | `tests/test_contract.py::test_missing_travel_is_not_zero` |
| 6 | **Ties with identical ETA:** 4 partners (ALPHA, BRAVO, CHARLIE, DELTA) all yield ETA = 25 | Break ties deterministically by partner ID in ascending lexicographical order regardless of input list sequence. | `partner_id: "P-ALPHA"`, `eta_minutes: 25` | `tests/test_regression.py::test_regression_stable_tie_breaking_multiple_partners` |
| 7 | **Whitespace-only identifiers:** `order_id="   "`, `restaurant_id="   "`, or `destination_zone="  "` | Rejected upfront as malformed order data (`partner_id: None`). | `partner_id: None`, `reason: 'invalid order or time data'` | `tests/test_regression.py::test_regression_empty_and_whitespace_ids_rejected` |
| 8 | **Negative travel time & non-finite values:** `leg1=-1`, `leg2=float("nan")`, `leg2=float("inf")` | Ineligible for dispatch; arithmetic not performed. | `eligible: False`, `eta_minutes: None` | `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected` |

## Regression tests added
To prevent identified defects from reoccurring, `tests/test_regression.py` was created with 9 focused test suites:
1. `test_regression_boolean_time_values_rejected`: Verifies boolean `True`/`False` flags are rejected for `prep_minutes`, `now`, and route travel legs.
2. `test_regression_partner_capacity_type_safety`: Verifies strict integer capacity validation (rejects floats, bools, zeros, negatives).
3. `test_regression_cancellation_duplicate_id_and_different_order`: Verifies replay idempotency even when event ID is reused with a different order payload.
4. `test_regression_cancellation_unassigned_order_safe`: Verifies cancellation of unassigned orders safely preserves partner state while auditing the event ID.
5. `test_regression_cancellation_workload_clamped_to_zero`: Prevents workload underflow below zero.
6. `test_regression_empty_and_whitespace_ids_rejected`: Ensures empty/whitespace strings are not treated as valid entity IDs.
7. `test_regression_stable_tie_breaking_multiple_partners`: Validates lexicographical ordering over 4 candidates with identical ETAs.
8. `test_regression_synthetic_dataset_batch_dispatch`: End-to-end integration test dispatching synthetic orders and processing cancellation events from `data/records.json`.
9. `test_regression_explain_candidates`: Tests candidate explanation reporting for operational visibility.

## Remaining failures or limitations
- **Remaining failures:** None. 238 out of 238 tests pass.
- **Known limitations:**
  - In-memory execution assumes single-threaded, local runtime. Distributed environments would require concurrency controls for partner state updates.

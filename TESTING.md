# TESTING.md — Test Execution and Edge-Case Evidence

## Test command and environment
- **Python version:** Python 3.14.7
- **Operating System:** macOS (darwin 25.1.0)
- **Command run:** `python3 -m pytest -q`
- **Actual test summary:** `238 passed in 0.11s` (Initial baseline: `65 failed, 164 passed in 0.39s` across 229 tests)

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Boolean travel time: `leg1 = True, leg2 = 1` | `True` must not be coerced to numeric `1`; reject as invalid route time. | `eligible: False`, `eta_minutes: None` | `test_invalid_or_missing_travel_time_rejected[True-1]` |
| 2 | Inactive partner: `partner['active'] = False` | Candidate must be excluded from assignment regardless of workload or distance. | `partner_id: None`, `reason: 'no eligible partner or missing time data'` | `test_inactive_partners_never_selected[False0]` and `test_inactive_partner_not_assigned` |
| 3 | Capacity boundary: `capacity = 2`, `active_order_ids = ['OLD0', 'OLD1']` | Candidate is at maximum capacity (`len == capacity`); must not be assigned another order. | `partner_id: None` | `test_capacity_boundary_matrix[2-2]` and `test_full_partner_not_assigned` |
| 4 | Duplicate cancellation event: `process_cancellation(partner, 'O', 'C')` called twice | Deduct workload once; duplicate invocation must be idempotent and not append duplicate event IDs. | `workload_minutes: 0`, `processed_cancellation_ids: ['C']` | `test_duplicate_cancellation_is_idempotent_across_workloads[10]` |
| 5 | Missing travel route in dataset: Order `DSP-ORD-0001` missing route `('REST-101', 'DEST-01')` | Must never treat missing route as zero; leave order unassigned with explanatory reason. | `partner_id: None`, `eta_minutes: None`, `reason: 'no eligible partner or missing time data'` | `test_regression_synthetic_records_dataset_integration` |
| 6 | Negative prep time: `order['prep_minutes'] = -5` | Reject negative preparation duration; order is invalid/ineligible. | `partner_id: None` | `test_negative_prep_time_is_rejected` and `test_preparation_time_validation[-5]` |
| 7 | Lexicographic tie-breaking: Partners `PARTNER-A` and `PARTNER-B` both yield ETA = 25 minutes | Select `PARTNER-A` because `'PARTNER-A' < 'PARTNER-B'` lexicographically. | `partner_id: 'PARTNER-A'`, `eta_minutes: 25` | `test_regression_lexicographic_tie_breaking` and `test_tie_break_by_partner_id` |

## Regression tests added
The following regression tests were implemented in `tests/test_regression.py` to protect against past defects and ensure contract compliance:

1. `test_regression_travel_time_non_numeric_and_special_floats`:
   Validates that strings (`"10"`), booleans (`True`/`False`), NaN (`float("nan")`), and infinity (`float("inf")`) in travel times are rejected without throwing exceptions.
2. `test_regression_negative_travel_and_prep_times`:
   Ensures negative values for prep minutes or travel legs are rejected.
3. `test_regression_inactive_partner_filtering`:
   Ensures partners with `active` set to `False`, `None`, `0`, or `"active"` are never assigned.
4. `test_regression_capacity_boundary_and_validation`:
   Guarantees that partner capacity must be an integer $\ge 1$ and rejects full partners as well as non-integer/boolean capacity values.
5. `test_regression_lexicographic_tie_breaking`:
   Verifies that multi-candidate ties on ETA are broken deterministically by partner ID in lexicographical order regardless of list input order.
6. `test_regression_cancellation_idempotency_and_clamping`:
   Confirms duplicate cancellation IDs are deduplicated and workload is floored at 0 even if order minutes exceed total workload.
7. `test_regression_malformed_inputs_gracefully_handled`:
   Verifies safe dictionary output for empty/None partners list, missing travel dictionary, and malformed order records.
8. `test_regression_synthetic_records_dataset_integration`:
   Loads the 180 orders, 60 partners, 387 travel routes from `data/records.json` and verifies that all 170 valid orders assign and the 10 missing-route orders safely unassign.
9. `test_regression_batch_assignment_stretch_feature`:
   Verifies that sequential batch dispatch updates partner capacity and workload across assignments.

## Remaining failures or limitations
- **Remaining failures:** None. 238 out of 238 tests pass cleanly.
- **Known limitations:**
  - Route matrix is in-memory; for extremely large cities ($>10^5$ zones), travel times should be backed by a spatial index or routing service rather than an in-memory dictionary.

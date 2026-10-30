# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version: Python 3.10+ (replace with your exact output from `python --version`, e.g., `Python 3.12.x`)
- Command run: `python -m pytest -q`
- Actual test summary: Baseline before fixes: `65 failed, 164 passed in 4.41s`. Final after fixes: `229 passed in 1.12s` (`0 failed`).

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Inactive partner (`active=False`, `0`, `None`, `"no"`) | Never assign order to inactive partner | `result["partner_id"] is None` | `test_inactive_partners_never_selected` |
| 2 | Full or invalid capacity (`capacity=1, active=1` or `capacity=True`/`0`/`-1`/`1.5`) | Reject partner when `len(active_order_ids) >= capacity` or capacity is not `int >= 1` | `result["partner_id"] is None` | `test_capacity_boundary_matrix` |
| 3 | Duplicate cancellation (`process_cancellation` called twice with same `event_id="C"`) | Subtract workload once and append `"C"` only once | `workload_minutes == 0`, `processed_cancellation_ids == ["C"]` | `test_duplicate_cancellation_is_idempotent_across_workloads` |
| 4 | Invalid time values (`now=-1`, `"5"`, `True`, `None` or `prep_minutes=-5`, `nan`, `inf`) | Do not crash; mark candidate ineligible and do not assign | `eligible is False`, `partner_id is None` | `test_current_time_validation`, `test_preparation_time_validation` |
| 5 | Missing or invalid travel routes (`travel` missing leg or leg value is `-1`, `True`, `nan`) | Reject route and return unassigned without treating missing time as `0` | `eligible is False`, `eta_minutes is None` | `test_invalid_or_missing_travel_time_rejected` |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning.
- Fixed unvalidated boolean/NaN/negative time inputs and missing travel maps in `estimate_eta` (protected by `test_current_time_validation` and regression test for `None` travel map / malformed partner dicts).
- Fixed inactive and full-capacity partner assignment in `assign_order` (protected by `test_inactive_partners_never_selected` and `test_capacity_boundary_matrix`).
- Fixed duplicate cancellation ID appending in `process_cancellation` (protected by `test_duplicate_cancellation_is_idempotent`).

## Remaining failures or limitations
List any known failing tests or unresolved behaviours honestly.
- 0 failing tests remain. A known limitation is that `assign_order` assigns orders one by one greedily without mutating the partner list in place or optimizing multi-order batches globally.
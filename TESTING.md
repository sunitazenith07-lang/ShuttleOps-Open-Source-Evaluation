# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment

- Python version: Python 3.15.2
- Command run: `python3 -m pytest -q`
- Actual test summary: **237 passed** in the latest run. The earlier **229 passed** run was before adding six workload cases and two dataset integration tests; pytest counts each parameter case separately.
- Demo command: `python3 -m main`
- Demo result: assigned order `O-7` to `P-2`, pickup time `13`, ETA `35`.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Partner-to-restaurant travel is `-1`; other leg is `1` | Reject the ETA and return `eligible=False` | Passed | `test_invalid_or_missing_travel_time_rejected[-1-1]`; travel validation group: 12 passed |
| 2 | Preparation time is `-1` | Do not assign an ETA | Passed | `test_preparation_time_validation[-1]`; preparation-time group: 13 passed |
| 3 | Partner has `active=False` | Do not select the partner | Passed | `test_inactive_partners_never_selected[False0]`; inactive-partner group: 11 passed |
| 4 | Capacity is `1` and there is already `1` active order | Leave the order unassigned | Passed | `test_capacity_boundary_matrix[1-1]`; capacity group: 15 passed |
| 5 | The same cancellation event `C` is processed twice | Remove the order once and record `C` only once | Passed | `test_duplicate_cancellation_is_idempotent_across_workloads[0]`; workload group: 15 passed |
| 6 | Current time is `-1` | Reject the ETA | Passed | `test_current_time_validation[-1]`; current-time group: 13 passed |
| 7 | Order ID is an empty string | Do not assign a partner | Passed | `test_invalid_order_fields_do_not_assign_partner[order_id-]`; invalid-order group: 14 passed |
| 8 | Partner workload is `-1`, `None`, `"5"`, `True`, NaN or infinity | Reject the ETA without doing invalid arithmetic | Passed | Added `test_invalid_partner_workload_is_rejected`; all 6 cases passed |
| 9 | All 180 dataset orders, with travel times converted to tuple keys | Do not assign cancelled orders; give other orders valid assignments or explicit unassigned results | Passed; 115 assigned, 5 unassigned and 60 cancelled orders unassigned | `test_dataset_orders_are_handled_with_converted_travel_times` |
| 10 | All 177 cancellation events, including 7 without IDs and repeated IDs | Missing IDs do not change partner data; duplicate IDs are only recorded once | Passed; 161 distinct event IDs recorded | `test_dataset_cancellation_events_handle_missing_and_duplicate_ids` |

## Regression tests added

I added `test_invalid_partner_workload_is_rejected` in `tests/test_acceptance_matrix.py` to cover six invalid workload values. I also added two integration tests in `tests/test_dataset_records.py` that run the full order and cancellation event lists from `data/records.json` through the service using tuple-key travel data.

## Remaining failures or limitations

- Full visible test suite: **237 passed**; no visible test failures in that run.
- `python3 -m main` completed successfully.
- Dataset integration tests covered all 180 orders and 177 cancellation events.
- Hidden tests are not available in this repository.

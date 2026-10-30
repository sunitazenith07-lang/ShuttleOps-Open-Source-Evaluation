# TESTING.md — test evidence

## Environment and commands
- Local Python: **3.13.5**.
- Baseline command on untouched starter: `python -m pytest -q` → **164 passed, 65 failed**.
- Final command after fixes: `python -m pytest -q` → **245 passed, 0 failed**.
- Demo command: `python -m main` → completed successfully.
- GitHub Actions runs Python 3.11; its result must be checked on the pull request.

## Test progression
| Stage | Result | Remaining failures |
|---|---:|---|
| Untouched starter | 164 passed, 65 failed | ETA validation, assignment eligibility/capacity, cancellation deduplication |
| After `estimate_eta()` | 201 passed, 34 failed | Assignment eligibility/capacity and cancellation deduplication |
| After `assign_order()` | 219 passed, 16 failed | Cancellation deduplication |
| Final implementation | **245 passed, 0 failed** | None in local suite |

## Edge cases verified
| # | Input / case | Expected behaviour | Actual result / evidence |
|---|---|---|---|
| 1 | Missing partner-to-restaurant or restaurant-to-destination route | Partner is ineligible; ETA is `None` | Passed — `test_invalid_or_missing_travel_time_rejected`, `test_eta_is_ineligible_when_either_required_route_is_missing` |
| 2 | Negative, string, Boolean, NaN or infinite travel/preparation/current/workload time | Ineligible; no arithmetic crash | Passed — `test_invalid_or_missing_travel_time_rejected`, `test_preparation_time_validation`, `test_current_time_validation`, `test_invalid_partner_workload_is_rejected` |
| 3 | Inactive partner | Never selected | Passed — `test_inactive_partner_not_assigned`, `test_inactive_partners_never_selected` |
| 4 | Partner at or above capacity; invalid capacity values | Never selected | Passed — `test_full_partner_not_assigned`, `test_capacity_boundary_matrix` |
| 5 | Equal ETA across partners | Lowest partner ID wins regardless of input order | Passed — `test_tie_break_by_partner_id`, `test_ties_break_by_partner_id_independent_of_input_order` |
| 6 | Same cancellation event submitted twice | Workload/order released once; event ID stored once | Passed — `test_duplicate_cancellation_is_idempotent`, `test_duplicate_cancellation_is_idempotent_across_workloads` |
| 7 | Same event ID replayed with a different order ID | Replay is ignored; second order remains active | Passed — `test_reused_event_id_with_different_order_payload_is_ignored` |
| 8 | Cancellation references an unknown order | No active order/workload is removed; event is recorded once | Passed — `test_unknown_order_event_is_recorded_once_and_replay_is_ignored` |
| 9 | Cancellation would reduce workload below zero | Workload is clamped to zero | Passed — `test_cancellation_workload_never_goes_below_zero` and invalid-workload regression |
| 10 | Blank event ID or malformed partner input | Safe no-op; no exception | Passed — `test_invalid_event_id_is_a_safe_no_op`, `test_non_dictionary_partner_is_returned_without_crashing` |
| 11 | Malformed order, partner or travel container passed to ETA | Ineligible result, no exception | Passed — `test_eta_rejects_malformed_top_level_records`, `test_eta_rejects_missing_partner_identifier` |

## Focused test commands
- ETA matrix and validation: `python -m pytest -q tests/test_acceptance_matrix.py -k 'eta_calculation_matrix or invalid_or_missing_travel_time_rejected or preparation_time_validation or current_time_validation or invalid_order_fields_do_not_assign_partner or invalid_partner_workload_is_rejected'` → **78 passed**.
- ETA contract: `python -m pytest -q tests/test_contract.py -k 'eta_formula or missing_travel_is_not_zero or negative_prep_time_is_rejected'` → **3 passed**.
- Expanded ETA scenarios: `python -m pytest -q tests/test_edge_cases.py` → **31 passed**. The three ETA groups total **112 passed**; malformed-record tests add another **5 passed**.
- Assignment matrix/contract selection: **30 passed**.
- Malformed-record regressions: `python -m pytest -q tests/test_malformed_records.py` → **5 passed**.
- New cancellation regressions: `python -m pytest -q tests/test_cancellation_regressions.py` → **5 passed**.

## Notes
No tests were deleted, skipped or weakened. The original visible tests remain in place. The final local suite is green; the CI run on the PR is still required because it uses Python 3.11.

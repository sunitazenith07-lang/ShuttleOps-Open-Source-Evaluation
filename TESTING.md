# Testing notes

## Test command and environment

- Python version: 3.14.7
- Command: `python -m pytest -q`
- Untouched baseline: 229 cases; 164 passed and 65 failed.
- After implementation: **235 passed, 0 failed, 0 errors, 0 skipped**.
- Offline demo: `python -m main` assigned `O-7` to `P-2` with pickup minute 13 and ETA minute 35.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | All route, workload, preparation, and current-time values are zero | Candidate is eligible; pickup and ETA are zero | Passed | `test_eta_formula_for_expanded_scenario_matrix` zero-value case |
| 2 | Either required travel route is absent | Candidate is ineligible and ETA is `None` | Passed | `test_eta_is_ineligible_when_either_required_route_is_missing` |
| 3 | Negative, string, boolean, `NaN`, or infinite time value | Candidate is rejected without unsafe arithmetic | Passed | `test_invalid_or_missing_travel_time_rejected`, `test_preparation_time_validation`, `test_current_time_validation` |
| 4 | Partner is inactive or has `active_order_ids` at capacity | Partner is not selected | Passed | `test_inactive_partners_never_selected`, `test_capacity_boundary_matrix` |
| 5 | Two partners have equal ETA and the input list puts the later ID first | Lexicographically smaller partner ID wins | Passed | `test_dispatch_selects_lowest_eta_and_stable_tie`, `test_ties_break_by_partner_id_independent_of_input_order` |
| 6 | Cancellation event `C` is applied twice to the same order | Workload is released once and `C` appears once | Passed | `test_duplicate_cancellation_is_idempotent_across_workloads` |
| 7 | Malformed order/partner records, non-mapping travel data, unknown order cancellation | Fail closed; unknown order does not release workload; caller input remains unchanged | Passed | `tests/test_service_validation.py` |

## Regression coverage added

`tests/test_service_validation.py` adds six cases covering malformed inputs, invalid capacity and active-order lists, invalid workload and travel container, copy-on-write cancellation, unknown order and invalid event behavior, and rejection reasons. Existing tests were not changed or weakened.

## Remaining limitations

The service has no persistent event store or concurrency control. Cancellation workload release relies on a valid `minutes_by_order` entry; without it, the service cannot infer how much workload to subtract. The full JSON dataset was inspected for schema and edge-case categories, but is not loaded by the demo or exercised as an integration suite.

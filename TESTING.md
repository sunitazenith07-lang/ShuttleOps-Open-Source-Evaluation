# 🧪 Testing Notes

## Test command and environment

- **Python version:** 3.14.7 (project requirement: Python 3.10+)
- **Command run:** `python -m pytest -q`
- **Actual final test summary:** `233 passed`
- **Baseline before implementation changes:** `65 failed, 164 passed`
- **Dependency setup:** Ran `python -m pip install -r requirements-dev.txt`; pytest 9.1.1 was already installed and satisfied the requirement.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---:|---|---|---|---|
| 1 | One or both travel-time routes are missing | Candidate is ineligible; missing travel is never treated as zero. | Passed; no ETA is returned for the candidate. | `test_missing_travel_is_not_zero`; `test_eta_is_ineligible_when_either_required_route_is_missing` |
| 2 | Travel time is negative, a string, boolean, NaN, or infinity | Reject the candidate without invalid ETA arithmetic. | Passed; invalid travel values are rejected. | `test_invalid_or_missing_travel_time_rejected` |
| 3 | Partner is inactive | Do not assign the order to that partner. | Passed; inactive partner is not selected. | `test_inactive_partner_not_assigned`; `test_inactive_partners_never_selected` |
| 4 | Partner has reached its order capacity | Do not assign another order to that partner. | Passed; full partner is filtered out. | `test_full_partner_not_assigned`; `test_capacity_boundary_matrix` |
| 5 | Two eligible candidates have the same ETA; input order is varied | Choose the lexicographically smaller partner ID consistently. | Passed; tie-break is independent of candidate order. | `test_tie_break_by_partner_id`; `test_ties_break_by_partner_id_independent_of_input_order` |
| 6 | The same cancellation event ID is received again with a different order payload | Apply the cancellation only once; do not release workload twice. | Passed; second event is ignored and the original partner input remains unchanged. | `test_duplicate_cancellation_is_idempotent`; `test_duplicate_cancellation_is_idempotent_across_workloads`; `test_cancellation_duplicate_event_with_different_payload_is_ignored` |
| 7 | Preparation time or current time is invalid | Candidate is ineligible and no invalid ETA is produced. | Passed; invalid time input is rejected. | `test_preparation_time_validation`; `test_current_time_validation` |
| 8 | Extremely large integer is supplied as current time | Handle it safely instead of raising during finite-number validation. | Passed; result is ineligible with no ETA. | `test_huge_integer_time_is_rejected_without_raising` in `tests/test_regressions.py` |
| 9 | Malformed order, partner list, or travel mapping is supplied | Return safe unassigned/ineligible results rather than crashing. | Passed; malformed inputs are handled safely. | `test_malformed_assignment_and_travel_inputs_are_safe` in `tests/test_regressions.py` |
| 10 | Travel rows from `data/records.json` are converted to tuple keys | Service can use a complete route from the dataset and calculate its ETA. | Passed; the test selects a valid eligible order/partner pair and checks the calculated result. | `test_expanded_dataset_routes_work_with_service_tuple_keys` in `tests/test_regressions.py` |

## Other recorded checks

- `python -m main` completed and assigned O-7 to P-2 (pickup: 13 minutes; ETA: 35 minutes).
- `git diff --check` passed.
- GitHub Actions / pull-request CI and hidden evaluation checks have not been run; those results are not claimed here.


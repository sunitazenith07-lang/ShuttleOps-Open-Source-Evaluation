# 🧪 Testing Notes

## Environment and commands

| Item | Recorded result |
|---|---|
| Python | 3.14.7 (project requirement: 3.10+) |
| Baseline | python -m pytest -q → 65 failed, 164 passed |
| Final visible suite | python -m pytest -q → 233 passed |
| Offline demo | python -m main → O-7 assigned to P-2; pickup 13 min; ETA 35 min |
| Whitespace check | git diff --check → passed |

Ran python -m pip install -r requirements-dev.txt; pytest 9.1.1 was already installed and satisfied the declared range.

## Edge-case coverage

| Case | Expected behavior | Result | Visible test evidence |
|---|---|---|---|
| One or both travel routes are missing | Candidate is ineligible; missing time is not treated as zero | Passed | test_missing_travel_is_not_zero; test_eta_is_ineligible_when_either_required_route_is_missing |
| Travel time is negative, a string, boolean, NaN, or infinity | Candidate is rejected without invalid arithmetic | Passed | test_invalid_or_missing_travel_time_rejected |
| Partner is inactive | Partner is not assigned | Passed | test_inactive_partner_not_assigned; test_inactive_partners_never_selected |
| Partner has reached capacity | Partner is not assigned | Passed | test_full_partner_not_assigned; test_capacity_boundary_matrix |
| Two candidates have the same ETA | Lowest partner ID in lexicographic order wins, independent of input order | Passed | test_tie_break_by_partner_id; test_ties_break_by_partner_id_independent_of_input_order |
| Same cancellation event is repeated with a different order payload | Workload is released once and event ID is recorded once | Passed | test_duplicate_cancellation_is_idempotent; test_duplicate_cancellation_is_idempotent_across_workloads; test_cancellation_duplicate_event_with_different_payload_is_ignored |
| Preparation time or current time is invalid | Candidate is ineligible | Passed | test_preparation_time_validation; test_current_time_validation |

## Regression tests

Added tests/test_regressions.py with four cases: duplicate cancellation IDs with different payloads and original-input preservation, huge integer time rejection, malformed assignment/travel inputs, and assignment using routes converted from data/records.json. Existing test files were not changed.

## Remaining checks

No visible test failures remain. GitHub Actions/PR CI and hidden evaluation checks have not been run.

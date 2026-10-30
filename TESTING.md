# Testing Notes

## Test command and environment

- Python version: 3.12.14
- Commands run: `python -m pytest -q` and `python -m main`
- Baseline: 164 passed, 65 failed.
- Final result: 232 passed in 0.49s.
- Demo result: `O-7` was assigned to `P-2` with pickup at 13 minutes and ETA at 35 minutes.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Either required travel leg is missing | Candidate is ineligible; no route is assumed to take zero minutes. | Ineligible with no ETA. | `test_eta_is_ineligible_when_either_required_route_is_missing` |
| 2 | Negative, infinite, boolean, text, or NaN travel time | Invalid time is rejected safely. | Ineligible with no exception. | `test_invalid_or_missing_travel_time_rejected` |
| 3 | Inactive or full partner | Partner cannot receive another order. | Order remains unassigned when no other partner qualifies. | `test_inactive_partner_not_assigned`, `test_full_partner_not_assigned` |
| 4 | Equal candidate ETAs in reversed input order | Lexicographically smallest partner ID wins. | `A`/`P0` selected consistently. | `test_tie_break_by_partner_id`, `test_ties_break_by_partner_id_independent_of_input_order` |
| 5 | A cancellation event is sent twice | Workload and capacity are released once only. | One event ID remains and workload is not decremented twice. | `test_duplicate_cancellation_is_idempotent` |
| 6 | Malformed partner record or non-boolean active field | Input is rejected without a crash or accidental assignment. | Order remains unassigned. | `test_malformed_records_are_rejected_without_an_exception`, `test_assignment_requires_a_real_boolean_active_flag` |

## Regression tests added

`tests/test_service_regressions.py` covers malformed records, strict active-state handling, and non-mutating, idempotent cancellation. The existing matrix tests cover finite time validation, capacity boundaries, tie-breaking, and duplicate events.

## Remaining limitations

The module is an in-memory decision engine. It does not persist assignments, reserve capacity atomically across concurrent callers, or validate a full batch of external JSON records.

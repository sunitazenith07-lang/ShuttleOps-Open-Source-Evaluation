# TESTING.md — Test evidence

## Test command and environment
- Python version: 3.14.7
- pytest version: 9.2.0
- Baseline command: `python3 -m pytest -q --tb=no`
- Baseline result: 65 failed, 164 passed.
- Final command: `python3 -m pytest -q`
- Final result: **235 passed in 0.07s**.
- The requested `python` executable was not available in this terminal; `python3` was used instead.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Travel time is negative, a numeric string, Boolean, NaN, infinity, or missing | Reject ETA; do not treat invalid or missing travel as zero | Rejected; suite passed | `test_invalid_or_missing_travel_time_rejected` |
| 2 | Preparation time is negative, missing, a string, Boolean, NaN, or infinity | Candidate is ineligible | Candidate rejected; suite passed | `test_preparation_time_validation` |
| 3 | Partner is inactive or its active order count reaches capacity | Do not assign that partner | No assignment for those candidates; suite passed | `test_inactive_partner_not_assigned`, `test_capacity_boundary_matrix` |
| 4 | Two eligible partners have equal ETAs, supplied in reverse ID order | Select the lexicographically smaller partner ID | Stable tie-break verified; suite passed | `test_tie_break_by_partner_id`, `test_ties_break_by_partner_id_independent_of_input_order` |
| 5 | Same cancellation event is processed twice | Release the order/workload only once and record the event once | Verified; suite passed | `test_duplicate_cancellation_is_idempotent`, `test_duplicate_cancellation_is_idempotent_across_workloads` |
| 6 | Malformed partner/order record appears alongside valid dispatch input | Do not raise or let malformed data block a valid candidate | Malformed records were skipped; suite passed | `tests/test_regressions.py` |
| 7 | Finite floating-point inputs overflow during ETA addition | Return an ineligible ETA, not infinity | Candidate remained unassigned; suite passed | `test_finite_inputs_that_overflow_eta_are_ineligible` |

## Regression tests added
`tests/test_regressions.py` covers malformed partner records, malformed orders, arithmetic overflow, and ensuring cancellation processing does not mutate its input partner. Existing tests cover the original eligibility, time-validation and duplicate-event defects.

## Remaining failures or limitations
No test failures remain. Cancellation event history is held in the partner record; persistence across process restarts is outside this repository's scope.

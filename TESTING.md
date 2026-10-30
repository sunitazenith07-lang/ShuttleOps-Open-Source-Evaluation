# TESTING

## Test command and environment
- Python version: `3.14.7`
- Command run: `. .venv/bin/activate && python -m pytest -q`
- Actual test summary: `229 passed in 0.05s`

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Missing route entry, e.g. only one of the two travel legs exists | Reject the partner and return `eligible == False` with `eta_minutes is None` | Correct | `test_eta_is_ineligible_when_either_required_route_is_missing` |
| 2 | Negative prep time such as `-5` | Reject ETA and block assignment | Correct | `test_negative_prep_time_is_rejected` |
| 3 | Inactive partner with `active = False` | Partner must never be selected | Correct | `test_inactive_partner_not_assigned` |
| 4 | Capacity reached, e.g. `active_order_ids` at the limit | Partner must not be assigned | Correct | `test_full_partner_not_assigned` |
| 5 | Duplicate cancellation event for the same order and event ID | Second cancellation should be ignored; workload remains stable | Correct | `test_duplicate_cancellation_is_idempotent` |
| 6 | Workload reduction would drop below zero | Workload should be clamped at `0` | Correct | `test_cancellation_workload_never_goes_below_zero` |
| 7 | Invalid current time like `None`, `-1`, or `True` | ETA must be rejected | Correct | `test_current_time_validation` |
| 8 | Tie in ETA between two candidates | Break tie by partner ID ascending | Correct | `test_tie_break_by_partner_id` |

## Regression tests added
The project already contains the relevant acceptance and edge-case checks. The fix was validated against those tests rather than weakening them. The regression coverage protects:
- invalid route handling
- negative prep time rejection
- inactive and full partner exclusion
- tie-break stability
- duplicate cancellation safety
- workload floor at zero
- invalid field rejection

## Remaining failures or limitations
None. The visible suite passed after the fix.

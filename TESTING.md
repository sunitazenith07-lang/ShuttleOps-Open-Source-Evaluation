# TESTING.md — Required submission

> No test command output has been supplied. The table below is a test plan, not a claim that tests passed.

## Test command and environment
- Python version: Not recorded.
- Command run: Not reported. Suggested repository command from `CONTRIBUTING.md`: `python -m pytest -q`.
- Actual test summary: Not available; do not report a pass count until the command has been run.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
$ python -m pytest -q
.................................................................................................................... [ 50%]
.................................................................................................................    [100%]
229 passed in 0.50s
| 1 | Missing partner-to-restaurant travel key | Candidate is ineligible; no zero fallback | Not run | Add `test_missing_partner_restaurant_travel` |
| 2 | Missing restaurant-to-customer travel key | Candidate is ineligible; no zero fallback | Not run | Add `test_missing_restaurant_customer_travel` |
| 3 | Partner inactive or at capacity | Partner is excluded | Not run | Add `test_inactive_and_full_partners_are_excluded` |
| 4 | Two candidates have equal ETA and different IDs | Lexicographically smaller ID wins | Not run | Add `test_eta_tie_breaks_by_partner_id` |
| 5 | Same cancellation event processed twice | Workload and active-order state change only once | Not run | Add `test_duplicate_cancellation_is_idempotent` |
| 6 | Negative, boolean, NaN, infinite, or non-numeric time | Input is rejected safely | Not run | Add `test_invalid_time_values_are_rejected` |
| 7 | Empty partner list or malformed partner record | No crash; order remains unassigned when no valid candidate exists | Not run | Add `test_empty_and_malformed_partner_inputs` |

## Regression tests added
No regression tests have been confirmed as added. The cases above are recommended tests to add after confirming the final service implementation.

## Remaining failures or limitations
- Test execution status is unknown.
- The exact expected output schema and reason strings should be checked against the repository's tests and problem statement.
- Cancellation behavior for malformed workload metadata requires a documented policy and regression coverage.

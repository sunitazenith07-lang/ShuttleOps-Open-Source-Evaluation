# Testing

## Test command and environment
- Python version: Python 3.14.7
- Commands run: `./.venv/bin/python -m pytest -q`; `python3 -m main`
- Actual test summary: 229 passed in 0.05s.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Preparation time `-5` | Order must not be assigned | `partner_id` was `None` | `test_negative_prep_time_is_rejected` |
| 2 | Missing one of two required travel routes | ETA must be ineligible; missing data is not zero | `eligible=False`, `eta_minutes=None` | `test_eta_is_ineligible_when_either_required_route_is_missing` |
| 3 | Partner capacity 1 with one active order | Partner must be rejected as full | `partner_id` was `None` | `test_full_partner_not_assigned` and capacity matrix |
| 4 | Equal ETA for partners `Z` and `A` | Lexicographically smallest ID `A` wins | `A` selected | `test_tie_break_by_partner_id` |
| 5 | Duplicate cancellation `C1` for order `O1` | Workload released once and event recorded once | Workload `0`, IDs `['C1']` | `test_duplicate_cancellation_is_idempotent` |
| 6 | Negative or non-finite travel time | Route must be rejected safely | Ineligible with `eta_minutes=None` | `test_invalid_or_missing_travel_time_rejected` |
| 7 | Current time `-1`, string, or boolean | Invalid current time must not calculate an ETA | ETA ineligible | `test_current_time_validation` |
| 8 | Cancellation of `UNKNOWN` | Existing workload and active orders remain unchanged | Workload unchanged | `test_cancellation_only_releases_present_order` |

## Regression tests added
No repository tests were changed or weakened. Existing parameterized regressions cover partner eligibility, capacity, time validation, deterministic selection, route missingness, cancellation duplication, and workload floors.

## Remaining failures or limitations
None are known in the visible suite. The suite does not exercise live GPS, database persistence, or third-party integrations; these are outside the simulated challenge.

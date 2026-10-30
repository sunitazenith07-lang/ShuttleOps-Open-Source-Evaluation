# Testing Notes

## Test command and environment
- Python version: 3.14.7
- Command: `.venv/bin/python -m pytest -q`
- Actual final summary: **239 passed in 0.05s**
- Baseline before implementation: **65 failed, 164 passed**
- Demo command: `.venv/bin/python -m main`
- Demo result: `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Missing route or negative, boolean, string, `NaN`, or infinite route time | ETA is ineligible; missing/invalid data is not treated as zero | Passed; result is ineligible with `eta_minutes=None` | `test_invalid_or_missing_travel_time_rejected`; `test_eta_is_ineligible_when_either_required_route_is_missing` |
| 2 | Negative, boolean, string, missing, or non-finite preparation time | Order cannot be assigned | Passed | `test_preparation_time_validation`; `test_negative_prep_time_is_rejected` |
| 3 | Partner inactive, at capacity, or capacity malformed | Candidate is not assigned | Passed | `test_inactive_partners_never_selected`; `test_capacity_boundary_matrix`; `test_inactive_partner_not_assigned`; `test_full_partner_not_assigned` |
| 4 | Equal valid ETAs, partners supplied in reverse ID order | Lowest lexicographic partner ID is selected regardless of input order | Passed | `test_tie_break_by_partner_id`; `test_ties_break_by_partner_id_independent_of_input_order` |
| 5 | Same cancellation event replayed for another order | Second replay does not alter active orders or workload; event ID remains once | Passed | `test_duplicate_cancellation_is_idempotent`; `test_duplicate_cancellation_event_cannot_cancel_another_order` |
| 6 | Invalid order fields, `None` partner collection, and missing workload | Return unassigned/ineligible results without raising during assignment or ETA calculation | Passed | `test_malformed_order_and_partner_collection_are_unassigned_safely`; `test_invalid_partner_workload_makes_eta_ineligible` |

## Regression tests added
Added `tests/test_regressions.py` for invalid partner workload, malformed order/partner collection, reason accuracy, reuse of a cancellation event ID, preservation of the input partner, and repeated active-order entries. No existing tests were changed, deleted, skipped, or weakened.

## Remaining failures or limitations
No test failures remain in the local suite. Local validation used Python 3.14.7; the repository's GitHub Actions workflow uses Python 3.11, and that environment was not run locally.

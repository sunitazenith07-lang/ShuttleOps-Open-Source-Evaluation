# Testing

Run: `python -m pytest -q` (250 tests: 229 provided, 21 in `tests/test_regression.py`).
Before the fix: 65 failed, 164 passed. After: 250 passed. No existing test was
edited, skipped or weakened, and the workflows are untouched.

## Edge cases
| # | Case | Expected | Test |
|---|---|---|---|
| 1 | Travel leg missing (either one) | Partner ineligible, never counted as 0 | `test_missing_travel_is_not_treated_as_zero` |
| 2 | Travel/prep/now/workload is negative, nan, inf, bool, string or None | Ineligible or order unassigned, no exception | acceptance matrix, `test_invalid_partner_workload_is_ineligible` |
| 3 | `active_order_ids == capacity`, or capacity is 0, -1, True, 1.5, None | Partner not selected | `test_capacity_boundary_matrix` |
| 4 | ETA tie | Smallest partner ID wins, whatever the input order | `test_tie_broken_by_partner_id_regardless_of_input_order` |
| 5 | Duplicate cancellation event | Released once, ID recorded once | `test_duplicate_cancellation_is_idempotent_across_workloads` |
| 6 | Same order cancelled under a new event ID | No second release, workload not below 0 | `test_cancellation_releases_once_and_never_below_zero` |
| 7 | Cancelling an unknown order | Safe no-op | `test_cancellation_of_unknown_order_is_a_safe_noop` |
| 8 | Empty/None/junk partner list; malformed order; unknown restaurant/zone | Unassigned with a reason, no exception | `test_empty_or_malformed_partner_lists_do_not_raise` and related |
| 9 | Fast partner with missing route vs slower complete partner | Slower complete partner wins | `test_fast_partner_with_missing_route_loses_to_slower_complete_partner` |
| 10 | Repeated calls and input mutation | Identical results, inputs unchanged | `test_inputs_are_not_mutated_and_results_are_deterministic` |
| 11 | Duplicate cancellation then reassign | Capacity freed exactly once | `test_capacity_freed_exactly_once_by_duplicate_cancellation` |

## Known limitations
- `active` is truthiness-based.
- No `max(arrival, food ready)` model, as the spec defines.
- `str(partner_id)` is used for tie-breaking, so non-string IDs compare by text.

# TESTING.md — Required submission

## Test command and environment
- Python version: 3.14.7 (local). CI uses 3.11; I did not run 3.11 locally.
- Command run: `python -m pytest -q`
- Baseline (untouched starter): 229 tests, 65 failed, 164 passed.
- Final: 267 passed, 0 failed, 0 errors, 0 skipped (229 original + 38 new).
- Demo: `python -m main` -> P-2, pickup 13, ETA 35.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test |
|---|---|---|---|---|
| 1 | Partner A has no partner->restaurant route; B has 50 | A excluded, not treated as 0; B wins with ETA 51 | B assigned, ETA 51 | test_missing_partner_leg_is_not_zero |
| 2 | Only partner->restaurant travel present | Unassigned, reason names the partner | "P: missing travel time" | test_missing_customer_leg_blocks_eta |
| 3 | Load 1 of 2 vs load 2 of 2 | Included vs excluded | P / None | test_capacity_boundary |
| 4 | Inactive partner | Excluded with reason | "P: inactive" | test_inactive_partner_excluded |
| 5 | P2 and P10 tie on ETA, both input orders | P10 wins (string order) | P10 both times | test_eta_tie_breaks_by_string_partner_id |
| 6 | Same cancellation twice | Released once; second call changes nothing | twice == once, workload 20 | test_duplicate_cancellation_releases_once |
| 7 | Same event ID for a different order | Second event ignored | order B stays active | test_same_event_id_for_another_order_is_ignored |
| 8 | Cancel unknown / None / "" order | No change, no crash | unchanged | test_cancelling_unknown_order_changes_nothing |
| 9 | Blank/None IDs, negative or str prep | Rejected with "order rejected: invalid <field>" | as expected | test_invalid_order_is_rejected_with_reason |
| 10 | Negative or str travel time | "invalid travel time" | as expected | test_negative_or_non_numeric_travel_is_rejected |
| 11 | now = -1, "5", None, True | "invalid current time" | as expected | test_invalid_current_time_is_rejected |
| 12 | Empty partner list; empty order | Clean unassigned result | as expected | test_empty_partner_list_is_unassigned_with_reason, test_empty_order_is_rejected |
| 13 | Partners shuffled | Identical result | identical | test_result_is_independent_of_partner_order |
| 14 | Partner zone is a list, not a string | Excluded with a reason, no crash | "P: invalid zone" | test_invalid_partner_zone_is_excluded_not_a_crash |
| 15 | Two cancellations with no event ID, different orders | Both applied, nothing stored as processed | both orders released, processed list empty | test_cancellations_without_event_id_are_each_applied |


## Regression tests added
tests/test_dispatch_regressions.py (38 test cases). Defects fixed:
- Missing validation of order fields, now and travel times (31 starter failures).
- Inactive and at-capacity partners were assignable (18 failures).
- Cancellation event IDs were recorded without being checked (16 failures).
- A non-string partner zone crashed the travel lookup with TypeError (found by a manual probe).

## Remaining failures or limitations
None failing. Known gaps: see DISPATCH_NOTES.md section 4.
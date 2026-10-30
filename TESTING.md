# TESTING.md

## Test command and environment
- Python version: `Python 3.14.7`
- Command run: `python -m pytest -q`
- Actual test summary: `231 passed in 0.25s`
- Offline demo command: `python -m main`
- Demo result: `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Missing route in `travel` (for example, no `("ZONE-A", "REST-101")`) | `estimate_eta()` should mark the candidate as ineligible and return `eta_minutes is None` | Pass; route missing is rejected before ETA is computed | `test_eta_is_ineligible_when_either_required_route_is_missing` |
| 2 | Negative `prep_minutes` such as `-5` | The order should be rejected and not assigned | Pass; invalid prep time is treated as ineligible | `test_negative_prep_time_is_rejected` |
| 3 | Inactive partner (`active=False`) with valid route data | The partner should never be selected | Pass; `assign_order()` returns no partner | `test_inactive_partner_not_assigned` |
| 4 | Full partner (`len(active_order_ids) >= capacity`) | Assignment should skip the partner | Pass; full partner is rejected | `test_full_partner_not_assigned` and `test_capacity_boundary_matrix` |
| 5 | Duplicate cancellation event for the same order | Workload must be released once only; second call should be ignored | Pass; `workload_minutes` stays at 0 and `processed_cancellation_ids` contains one event | `test_duplicate_cancellation_is_idempotent` |
| 6 | Same ETA for different partners | Partner ID should break the tie in ascending lexicographic order | Pass; lower partner ID wins | `test_tie_break_by_partner_id` |

## Regression tests added
I added two focused regression checks in `tests/test_edge_cases.py`:
- `test_eta_rejects_missing_partner_id`
- `test_assign_order_rejects_invalid_capacity_even_when_active`

These cover malformed partner metadata and invalid capacity values that were not explicitly protected by the starter contract.

## Remaining failures or limitations
No current failing tests or unresolved issues are present in this repository. The visible suite passes and the offline demo runs successfully.

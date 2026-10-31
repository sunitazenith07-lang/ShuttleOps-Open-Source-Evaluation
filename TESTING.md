# TESTING.md — Required submission

## Test command and environment
- Python version: 3.13.15
- Command run: `python -m pytest -q`
- Actual test summary: **300 passed** (baseline before fixes: 65 failed, 164 passed)

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Travel time is a negative integer (e.g. `leg1=-1`) | Partner should be ineligible; ETA must be `None` | `eligible=False`, `eta_minutes=None` | `test_invalid_or_missing_travel_time_rejected[-1-1]`, `TestTravelTimeValidation::test_bad_leg1_rejected[-5-3]` |
| 2 | Partner at full capacity (`capacity=1`, one active order) | Partner must not be assigned | `partner_id=None` | `test_capacity_boundary_matrix[1-1]`, `TestCapacityCheck::test_at_capacity_rejected` |
| 3 | Duplicate cancellation with same `event_id` | Workload and order list must not change a second time; `processed_cancellation_ids` has event once | `workload_minutes=0`, `processed_cancellation_ids=['C']` | `test_duplicate_cancellation_is_idempotent_across_workloads[*]`, `TestCancellationIdempotency::test_duplicate_event_id_no_double_release` |
| 4 | Order with empty `order_id=""` | Assignment must be rejected (no partner assigned) | `partner_id=None`, `reason='invalid order fields'` | `test_invalid_order_fields_do_not_assign_partner[order_id-]`, `TestOrderFieldValidation::test_invalid_field_rejects_assignment` |
| 5 | `now` parameter is negative (`now=-10`) | Estimate must be ineligible | `eligible=False` | `test_current_time_validation[-10]`, `TestNowValidation::test_invalid_now_rejected[-100]` |
| 6 | All partners have missing travel routes | No partner assigned; reason provided | `partner_id=None`, `eta_minutes=None` | `test_no_partner_and_missing_route_cases_are_safe[*]`, `TestNoPartners::test_all_missing_routes` |
| 7 | Two partners with identical ETA, different IDs | Lexicographically smaller partner_id wins (deterministic) | Lower ID selected regardless of input order | `test_dispatch_selects_lowest_eta_and_stable_tie[*]`, `TestTieBreaking::test_tie_selects_lower_id` |
| 8 | `prep_minutes` is `True` (boolean) | Must be rejected — `True` is not a valid numeric time | `partner_id=None` | `test_preparation_time_validation[True]`, `TestPrepTimeValidation::test_invalid_prep_rejected_in_estimate` |
| 9 | Partner `active` is `1` (int, not `True`) | Must be rejected — only boolean `True` counts as active | `partner_id=None` | `test_inactive_partners_never_selected[1]`, `TestActivePartnerFiltering::test_non_true_active_not_assigned[1]` |
| 10 | Travel time is `float("inf")` | Must be rejected — infinite travel is not valid | `eligible=False` | `test_invalid_or_missing_travel_time_rejected[1-inf]`, `TestTravelTimeValidation::test_bad_leg2_rejected[3-inf]` |

## Regression tests added

All regression tests are in [`tests/test_regressions.py`](tests/test_regressions.py). Defects fixed and corresponding test classes:

| Defect | Regression test class |
|---|---|
| Negative/string/bool/NaN/inf travel times accepted | `TestTravelTimeValidation` (13 cases) |
| Invalid prep_minutes accepted | `TestPrepTimeValidation` (8 cases) |
| Invalid `now` accepted | `TestNowValidation` (7 cases) |
| Invalid order fields (empty/None IDs, bad prep) not rejected | `TestOrderFieldValidation` (14 cases) |
| Inactive partners (active ≠ True) still assigned | `TestActivePartnerFiltering` (7 cases) |
| Partners at/over capacity not rejected | `TestCapacityCheck` (11 cases) |
| Duplicate cancellation reduces workload twice | `TestCancellationIdempotency` (3 cases) |
| Tie-breaking by partner_id | `TestTieBreaking` (2 cases) |
| Empty/all-ineligible partner lists | `TestNoPartners` (4 cases) |
| ETA formula correctness | `TestETAFormulaSanity` (3 cases) |

## Remaining failures or limitations

No known failing tests. All 300 tests pass. Potential limitations:
- Float workload_minutes values are not validated (inherited from the starter; no test requires this).
- The `minutes_by_order` map is trusted during cancellation — a missing entry defaults to 0 reduction.

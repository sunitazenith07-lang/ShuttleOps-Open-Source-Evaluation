# TESTING.md — Required submission

## Test command and environment

- **Python version:** 3.14.7
- **pytest version:** 9.2.0
- **Command run:** `python -m pytest -q`
- **Actual test summary (final):** `235 passed in 0.21s`
- **Baseline (before fixes):** `65 failed, 164 passed in 0.68s`

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `travel[('Z','R')] = -1` (negative travel time) | `eligible=False`, `eta_minutes=None` | `eligible=False`, `eta_minutes=None` ✅ | `test_invalid_or_missing_travel_time_rejected[-1-1]` |
| 2 | `partner['active'] = False`, valid routes exist | `partner_id=None` — not assigned | `partner_id=None` ✅ | `test_inactive_partner_not_assigned` |
| 3 | `capacity=1`, `active_order_ids=['A']` (partner is full) | `partner_id=None` — at capacity | `partner_id=None` ✅ | `test_full_partner_not_assigned` |
| 4 | Two partners, identical ETA, input list order `[Z, A]` | Winner is `A` — alphabetically first ID | `partner_id='A'` ✅ | `test_tie_break_by_partner_id` |
| 5 | Same cancellation event `C1` applied twice to same partner | `processed_cancellation_ids=['C1']` — not `['C1','C1']` | `['C1']`, `workload=0` ✅ | `test_duplicate_cancellation_is_idempotent` |
| 6 | `prep_minutes=True` (boolean passed as prep time) | `eligible=False` — boolean is not valid | `eligible=False` ✅ | `test_preparation_time_validation[True]` |
| 7 | `travel[('Z','R')] = float('nan')` | `eligible=False` — NaN is not usable | `eligible=False` ✅ | `test_invalid_or_missing_travel_time_rejected[nan-1]` |
| 8 | `order_id=None` passed to `assign_order` | `partner_id=None`, reason string returned | `partner_id=None` ✅ | `test_invalid_order_fields_do_not_assign_partner[order_id-None]` |
| 9 | Empty `partners` list passed to `assign_order` | `partner_id=None`, non-empty reason string | `partner_id=None`, `reason='no eligible partner or missing time data'` ✅ | `test_no_candidate_returns_reason` |
| 10 | `now=-1` (negative current time) passed to `estimate_eta` | `eligible=False` — negative time invalid | `eligible=False` ✅ | `test_current_time_validation[-1]` |

## Regression tests added

| Defect fixed | Regression test added | File |
|---|---|---|
| Sequential cancellations of two orders could corrupt workload | `test_sequential_cancellations_of_different_orders` | `tests/test_regression.py` |
| `now` parameter not verified to flow through `assign_order` | `test_assign_order_uses_nonzero_now_correctly` | `tests/test_regression.py` |
| Mixed partner pool — one eligibility rule could silently fail | `test_correct_partner_selected_from_mixed_pool` | `tests/test_regression.py` |
| Idempotency guard could incorrectly key on `order_id` not `event_id` | `test_already_processed_event_blocks_different_order` | `tests/test_regression.py` |
| Partner with missing `active` key not treated as inactive | `test_partner_missing_active_key_is_not_assigned` | `tests/test_regression.py` |
| Partner with missing `workload_minutes` key not defaulting to zero | `test_missing_workload_minutes_key_defaults_to_zero` | `tests/test_regression.py` |

## Remaining failures or limitations

**No failing tests.** Final result: `235 passed, 0 failed`.

Known limitation: the `data/records.json` dataset (180 orders, 60 partners,
387 travel-time records) is not covered by automated tests. The travel-time
rows in that file would need to be converted from JSON list format into the
tuple-key dictionary expected by `service.py` before they could be used in
tests. Integration tests that load and exercise this dataset would be the
natural next addition.

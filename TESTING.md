# TESTING.md — Required submission

## Test command and environment
- Python version: 3.14.3 (macOS, Darwin 25.6.0)
- Commands run: `python -m pip install -r requirements-dev.txt`, `python -m pytest -q`, `python -m main`
- Baseline (before edits): **65 failed, 164 passed** — 229 tests total
- Final (after fixes): **274 passed, 0 failed** — 229 original + 45 added tests
- Demo: `python -m main` → `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Inactive partner (`active=False`) with full travel data | Never assigned | `partner_id=None` | `test_inactive_partner_not_assigned`, `test_all_partners_inactive_leaves_order_unassigned` |
| 2 | Partner at capacity (`capacity=1`, 1 active order) | Cannot receive another order | `partner_id=None`; a second free partner still gets it | `test_full_partner_not_assigned`, `test_full_partner_cannot_receive_extra_order_but_others_can` |
| 3 | Missing partner→restaurant leg (only restaurant→customer exists) | Ineligible, `eta_minutes=None`, never treated as 0 | Ineligible | `test_missing_partner_to_restaurant_route_ineligible`, `test_missing_travel_is_never_treated_as_zero` |
| 4 | Negative travel time `-1` on either leg | Rejected | `eligible=False` | `test_negative_travel_time_rejected`, `test_invalid_or_missing_travel_time_rejected` |
| 5 | Negative `prep_minutes=-5` / `prep_minutes="10"` / `None` / `True` / NaN | Order rejected, no assignment | `partner_id=None` | `test_negative_prep_time_is_rejected`, `test_preparation_time_validation` |
| 6 | Equal ETA for partners `A` and `Z` (both legs equal) | Lexicographically smaller `partner_id` wins, regardless of input order | `A` selected in both orders | `test_tie_break_by_partner_id`, `test_equal_eta_tie_broken_by_partner_id` |
| 7 | Duplicate cancellation `C1` replayed | Second event releases nothing | `workload_minutes` stays 0, `processed_cancellation_ids==['C1']` | `test_duplicate_cancellation_is_idempotent`, `test_duplicate_event_id_with_different_order_still_ignored` |
| 8 | Cancellation for unknown order `NO-SUCH-ORDER` | Safe no-op, event still recorded | State unchanged | `test_cancellation_of_unknown_order_is_safe`, dataset replay |
| 9 | `minutes_by_order` release > `workload_minutes` (10 > 3) | Workload floors at 0, never negative | `workload_minutes=0` | `test_workload_never_negative_when_release_exceeds_workload` |
| 10 | Malformed records (`order=None`, partner string, `capacity=True/1.5/0`) | No crash, no assignment | `partner_id=None` | `test_malformed_order_record_is_safe`, `test_malformed_partner_record_is_safe`, `test_invalid_capacity_partner_ineligible` |
| 11 | Full dataset: 180 orders × 60 partners, 177 cancellations replayed twice | Deterministic, idempotent, no negative workload | Identical results across replays | `test_all_dataset_orders_assign_deterministically`, `test_full_cancellation_stream_replay_is_idempotent` |

## Regression tests added
- `tests/test_regression.py` — 38 tests covering: empty partner list; all-inactive; all-at-capacity; invalid capacity values; missing each travel leg; missing-travel-never-zero; negative travel/prep; malformed order and partner records; negative workload; pickup/ETA formula; lowest-ETA selection; equal-ETA tie-break both input orders; repeated-call determinism; demo fixture pin; duplicate cancellation; duplicate `event_id` with different payload; unknown-order cancellation; workload floor; `minutes_by_order` consistency; non-mutation of the input record; ordered distinct events; `explain_assignment` stretch feature.
- `tests/test_dataset.py` — 5 tests over `data/records.json`: tuple-key conversion, deterministic assignment of all 180 orders, chosen partner always eligible, idempotent full-stream cancellation replay, no double release on the 9 duplicated `event_id`s.

## Remaining failures or limitations
None — 274/274 pass locally. Assumption documented in DISPATCH_NOTES.md: `event_id`-less cancellations are deduplicated per partner (only the first applies).

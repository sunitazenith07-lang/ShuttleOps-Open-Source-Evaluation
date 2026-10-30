# TESTING.md — Required submission

> Testing rules for this project: never weaken or skip a test, never report a result that was not actually run, and add a regression test for every fix. AI-use declaration: `AI_USAGE_TEMPLATE.md`.

## Test command and environment
- Python version: 3.14.3 (macOS, Darwin 25.6.0)
- Commands run: `python -m pip install -r requirements-dev.txt`, `python -m pytest -q`, `python -m pytest --collect-only -q`, `python -m main`
- Baseline (before edits): **65 failed, 164 passed** — 229 tests total
- Final (commit `3ddc5d2`): **288 passed, 0 failed, 0 skipped, 0 xfail**. That is the 229 original tests plus 59 added:

  | File | Cases |
  |---|---|
  | `test_acceptance_matrix.py` | 189 |
  | `test_edge_cases.py` | 31 |
  | `test_contract.py` | 9 |
  | `test_regression.py` | 54 |
  | `test_dataset.py` | 5 |

- The three original test files are byte-identical to `upstream/main`. The suite also passes with the test files run in reverse order.
- Demo: `python -m main` → `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

## Additional verification (temporary scripts outside the repository)
- **Dataset replay:** all 180 orders → 170 assigned, 10 unassigned, with 0 mismatches against an independently written eligibility and ETA checker. Every unassigned order has no partner that is active, below capacity and has both travel legs.
- **Cancellation replay:** 177 events → 0 accounting mismatches against an independent checker, no negative workloads, and a second full replay leaves the state unchanged (idempotent).
- **Determinism:** identical results across 5 random shufflings of the partner list and of the travel rows.
- **Hostile inputs:** about 400 calls with `None`, empty values, bools, NaN, infinity, unhashable values, wrong types and missing fields on every argument and record field produced 0 crashes.

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
| 9 | `minutes_by_order` release > `workload_minutes` (10 > 3) | Valid workload floors at 0, never negative | `workload_minutes=0` | `test_workload_never_negative_when_release_exceeds_workload` |
| 10 | Malformed records (`order=None`, partner string, `capacity=True/1.5/0`) | No crash, no assignment | `partner_id=None` | `test_malformed_order_record_is_safe`, `test_malformed_partner_record_is_safe`, `test_invalid_capacity_partner_ineligible` |
| 11 | Full dataset: 180 orders × 60 partners, 177 cancellations replayed twice | Deterministic, idempotent, no negative workload | Identical results across replays | `test_all_dataset_orders_assign_deterministically`, `test_full_cancellation_stream_replay_is_idempotent` |
| 12 | Cancellation with unhashable `order_id` (a list) present in `active_order_ids` | No crash; order removed; workload unchanged | `active_order_ids==[]`, `workload_minutes==10` | `test_cancellation_with_unhashable_order_id_is_safe` |
| 13 | Cancellation on a partner whose `workload_minutes` is malformed (`'20'`) | Order removed and event recorded, but malformed workload kept as-is (not coerced to 0); partner still ineligible | `workload_minutes=='20'`, later `assign_order` → `partner_id=None` | `test_cancellation_preserves_malformed_workload_instead_of_zeroing` |
| 14 | Result schema for assigned, no-partner and invalid-order cases | Same five keys every time; unassigned has `pickup_minutes=None`, `eta_minutes=None`, reason ≠ `'assigned'` | Matches | `test_assigned_and_unassigned_results_share_one_schema` |
| 15 | Int too large for a float (`10**400`) as prep, travel leg, workload or `now` | Rejected as invalid, no `OverflowError` | `eligible=False`, `partner_id=None` | `test_int_too_large_for_float_is_rejected_without_crashing` (4 cases), `test_cancellation_with_int_too_large_for_float_does_not_crash` |
| 16 | Finite inputs whose sum overflows (`1e308` prep and legs) | ETA `inf` is not reliable, so not assigned | `eligible=False` with reason `'ETA out of range'`; `partner_id=None` | `test_eta_overflowing_to_infinity_is_not_assigned` |
| 17 | Cancellation when `processed_cancellation_ids` is the tuple `('C1',)`, or `active_order_ids` is the tuple `('O1','O2')` | Malformed state is preserved and the event skipped: no double release, no erased orders | Workload unchanged; tuples unchanged | `test_malformed_event_history_cannot_cause_double_release`, `test_malformed_active_orders_are_not_erased_by_cancellation`, `test_missing_list_fields_still_default_to_empty_on_cancellation` |

## Regression tests added
- `tests/test_regression.py` — 54 test cases (37 functions, some parametrized) covering: empty partner list; all-inactive; all-at-capacity; invalid capacity values; missing each travel leg; missing-travel-never-zero; negative travel/prep; malformed order and partner records; negative workload; pickup/ETA formula; lowest-ETA selection; equal-ETA tie-break both input orders; repeated-call determinism; one shared result schema for assigned and unassigned outputs; demo fixture pin; duplicate cancellation; duplicate `event_id` with different payload; unknown-order cancellation; workload floor; `minutes_by_order` consistency; unhashable `order_id` safety; malformed workload preserved (not zeroed); huge-int and infinite-ETA rejection; malformed cancellation list fields preserved and the event skipped; missing list fields still defaulting to `[]`; non-mutation of the input record; ordered distinct events; `explain_assignment` stretch feature.
- `tests/test_dataset.py` — 5 tests over `data/records.json`: tuple-key conversion, deterministic assignment of all 180 orders, chosen partner always eligible, idempotent full-stream cancellation replay, no double release on the 9 duplicated `event_id`s.

## Remaining failures or limitations
None — 288/288 pass locally. Assumptions documented in DISPATCH_NOTES.md:
- Cancellations without an `event_id` are deduplicated per partner, so only the first applies.
- An event against a malformed list field is skipped rather than "repaired".

The GitHub Actions result will be checked once the pull request is opened.

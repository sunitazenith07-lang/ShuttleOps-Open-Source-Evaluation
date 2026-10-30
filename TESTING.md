# TESTING.md — Required submission

## Test command and environment
- Python version: 3.11.9
- Command run: `python -m pytest -q` (also `python -m main` for the demo)
- Actual test summary: **266 passed, 0 failed** (baseline before the fix was 164 passed, 65 failed)

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `now="5"` (string current time) | `estimate_eta` returns `eligible=False`, `eta_minutes=None`; no crash | `eligible=False`, `eta_minutes=None` | `test_estimate_eta_rejects_invalid_now` |
| 2 | `now=None` and `now=True` | ineligible (non-numeric / boolean time) | ineligible | `test_estimate_eta_rejects_invalid_now` |
| 3 | travel leg `-1` or `"2"` or `True` or `NaN` or `inf` | ineligible (missing/invalid travel never treated as zero) | ineligible | `test_estimate_eta_rejects_invalid_travel_times` |
| 4 | `prep_minutes=-1` / `None` / `"2"` / `True` / `NaN` / `inf` | ineligible preparation time | ineligible | `test_estimate_eta_rejects_invalid_prep_time` |
| 5 | inactive partner (`active=False`) | not assigned | `partner_id=None` | `test_assign_order_skips_inactive_partner` |
| 6 | partner at full capacity (`len(active_order_ids) >= capacity`) | not assigned | `partner_id=None` | `test_assign_order_skips_full_capacity_partner` |
| 7 | invalid capacity (`0`, `-1`, `True`, `1.5`, `None`) | not assigned | `partner_id=None` | `test_assign_order_rejects_invalid_capacity` |
| 8 | order id `""` / `None` / `0` | not assigned | `partner_id=None` | `test_assign_order_rejects_malformed_order_identifiers` |
| 9 | ETA tie between partners | tie breaks by partner id ascending | `P0` selected | `test_assign_order_breaks_eta_ties_by_partner_id_ascending` |
| 10 | duplicate cancellation (same `event_id` twice) | workload released once, event id recorded once | workload 0, ids `['C1']` | `test_duplicate_cancellation_does_not_release_twice` |
| 11 | cancellation of an order not in `active_order_ids` | workload and active orders unchanged | workload 20, active `['ACTIVE']` | `test_cancellation_of_unknown_order_releases_nothing` |

## Regression tests added
Added `tests/test_regressions.py` (37 tests) covering every defect fixed:
- invalid `now`, invalid travel legs, invalid `prep` rejected by `estimate_eta`;
- inactive / full-capacity / invalid-capacity partners skipped by `assign_order`;
- malformed order identifiers rejected;
- ETA tie-breaking by partner id ascending;
- cancellation idempotency and unknown-order cancellation;
- deterministic dispatch over a bounded sample of `data/records.json` (converting the 387 travel-time rows to the tuple-key map).

No existing test was deleted, skipped, weakened, or bypassed, and CI was not edited.

## Remaining failures or limitations
None visible — all 266 tests pass. The stretch work (batch assignment, per-candidate explanation, ETA recalculation on prep change) was intentionally not attempted, per the problem statement's "choose at most one after the core works" guidance, because correctness and the required documentation took priority.

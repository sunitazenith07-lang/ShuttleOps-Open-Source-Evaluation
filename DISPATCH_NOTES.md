# DISPATCH_NOTES.md

Formula implemented in `service.estimate_eta`:

```
pickup = now + travel(partner.zone → restaurant) + partner.workload_minutes
ETA    = pickup + order.prep_minutes + travel(restaurant → destination_zone)
```

All outputs below were produced by running the current `service.py`.

## 1. Worked ETA example

Input: `fixtures.sample_inputs()` (the demo data) with `now = 5`.

- Order `O-7`: restaurant `R-2`, destination `Z-9`, prep **10** min
- Travel: `(Z-1, R-2) = 8`, `(Z-3, R-2) = 12`, `(R-2, Z-9) = 12`

| | P-2 (zone Z-1) | P-1 (zone Z-3) |
|---|---|---|
| active / capacity / active orders | True / 2 / 1 (`OLD-1`) → eligible | True / 2 / 0 → eligible |
| now | 5 | 5 |
| partner → restaurant | 8 | 12 |
| workload | 5 | 2 |
| **pickup** | 5 + 8 + 5 = **18** | 5 + 12 + 2 = **19** |
| prep | 10 | 10 |
| restaurant → customer | 12 | 12 |
| **ETA** | 18 + 10 + 12 = **40** | 19 + 10 + 12 = **41** |

Actual result of `assign_order(order, partners, travel, now=5)`:
```
{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 18, 'eta_minutes': 40, 'reason': 'assigned', 'rejected': []}
```
P-2 wins (40 < 41) even though it has more workload, because its shorter route outweighs the 3 extra workload minutes. With `now = 0` (what `python -m main` uses) the same result is pickup 13 / ETA 35.

Dataset example: `DSP-ORD-0002` (REST-102 → DEST-08, prep 1) → `PARTNER-013` (ZONE-C, workload 0): pickup = 0 + 1 + 0 = 1, ETA = 1 + 1 + 50 = **52**. `PARTNER-033` also has ETA 52; `PARTNER-013` is chosen because `"PARTNER-013" < "PARTNER-033"`.

## 2. No-eligible-partner example

Order `O-99` (`R → D`, prep 8), travel `{(Z1,R):3, (Z2,R):4, (R,D):10}`:

| Partner | State | Why ineligible |
|---|---|---|
| A (Z1) | `active = False` | partner is not active |
| B (Z2) | capacity 1, `active_order_ids = ['OLD']` | partner at capacity |
| C (Z3) | active, free | no `(Z3, R)` route → missing travel-time data (not treated as 0) |

Actual result:
```
{'order_id': 'O-99', 'partner_id': None, 'eta_minutes': None,
 'rejected': [{'partner_id': 'A', 'reason': 'partner is not active'},
              {'partner_id': 'B', 'reason': 'partner at capacity'},
              {'partner_id': 'C', 'reason': 'missing travel-time data'}],
 'reason': 'no eligible partner (missing travel-time data; partner at capacity; partner is not active)'}
```
Note that A and B had valid routes (3 and 4 min) — a starter-style implementation would have assigned A with ETA 21.

The same happens on real data: `DSP-ORD-0001` (REST-101 → DEST-01) is unassigned because the `REST-101 → DEST-01` route is absent; all 60 partners are rejected (28 at capacity, 27 missing travel data, 5 inactive). 10 of 180 dataset orders end up unassigned, all for this reason.

## 3. Three edge cases

1. **Negative preparation time**
   - Input: `new_order('O-1','R','D',-5)`, valid partner `P`, routes `{(Z,R):1,(R,D):1}`
   - Expected: no assignment; invalid data must not produce an ETA.
   - Actual: `{'order_id': 'O-1', 'partner_id': None, 'eta_minutes': None, 'rejected': [], 'reason': 'invalid order: invalid or missing prep_minutes'}`
   - Reasoning: the order is rejected before any partner is evaluated, because no partner could produce a reliable ETA for it.
   - Test: `test_negative_prep_time_is_rejected`, `test_preparation_time_validation`

2. **Duplicate cancellation event**
   - Input: partner with `active_order_ids=['O1']`, workload 9, `minutes_by_order={'O1': 9}`; `process_cancellation(p,'O1','C1')` applied twice.
   - Expected: workload released once; event recorded once.
   - Actual (after both calls): `active_order_ids: []`, `workload_minutes: 0`, `minutes_by_order: {}`, `processed_cancellation_ids: ['C1']`. The starter recorded `['C1', 'C1']`.
   - Reasoning: `event_id` is the idempotency key; a seen ID returns the record unchanged, so a retry can never release capacity twice — even if the retry names a different order (`test_reused_event_id_with_different_payload_is_ignored`).
   - Test: `test_duplicate_cancellation_is_idempotent`, `test_duplicate_cancellation_is_idempotent_across_workloads`

3. **Non-finite travel time (NaN)**
   - Input: routes `{(Z,R): 1, (R,D): float('nan')}`
   - Expected: ineligible. NaN compares false with everything, so if accepted it would corrupt `min()` and make selection order-dependent.
   - Actual: `{'partner_id': 'P', 'eta_minutes': None, 'eligible': False, 'reason': 'invalid travel-time data'}`
   - Test: `test_invalid_or_missing_travel_time_rejected[1-nan]`, `[nan-1]`, `[1-inf]`

## 4. Assumptions and limitations
- **Tie-breaking:** lowest ETA, then `partner_id` in ascending string (lexicographic) order — so `P10` beats `P2`. `partner_id` must be a non-empty string. Result is independent of input order (verified by shuffling all 60 dataset partners).
- **Eligibility:** `active` must be exactly `True`; `capacity` must be an `int >= 1` (not bool); eligible iff `len(active_order_ids) < capacity`.
- **Valid times:** `int`/`float`, not bool, finite, `>= 0`. Applies to `now`, prep, workload and both travel legs. Floats are allowed (e.g. prep 1.5).
- **Workload accounting:** cancelling an active order subtracts `minutes_by_order[order_id]` from workload (clamped at 0) and removes that entry. Cancelling an unknown order records the event but changes nothing else.
- **Cancellation idempotency:** keyed on `event_id`. Events with no `event_id` are not applied (7 in the dataset), since they can't be de-duplicated.
- **Not handled (outside the stated contract):** order `status` is ignored; `assign_order` does not add the order to the chosen partner's load, so assigning several orders in a row needs a caller to update partner state.

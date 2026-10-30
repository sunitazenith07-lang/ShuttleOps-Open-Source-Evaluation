# DISPATCH_NOTES.md — Required submission

## 1. Worked ETA example
From `fixtures.py` / `python -m main`:
- Order: `O-7`, restaurant `R-2`, destination zone `Z-9`, preparation 10 min.
- Candidate partner `P-2`: zone `Z-1`, workload 5 min, active, capacity 2 (0 of 2 orders used after ignoring the stale `OLD-1` reference for ETA purposes — capacity check counts `active_order_ids`, which here contains one existing order so 1 < 2, still eligible).
- Partner-to-restaurant travel `leg1` = 8 min (`Z-1` → `R-2`).
- Pickup time = now(0) + leg1(8) + workload(5) = 13 min.
- Restaurant-to-customer travel `leg2` = 12 min (`R-2` → `Z-9`).
- ETA = pickup(13) + prep(10) + leg2(12) = 35 min.
- The other candidate `P-1` (zone `Z-3`, workload 2) would be pickup 14, ETA 36, so `P-2` wins on lowest ETA.
- Actual result from `python -m main`:
  `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.

## 2. No-eligible-partner example
Example: order `O-99` with restaurant `R-X` and destination `Z-Y`, `now=0`.
- Partner `P-A` (zone `Z-1`): `active=False` → ineligible (inactive).
- Partner `P-B` (zone `Z-2`): `active=True`, capacity 1, `active_order_ids=['OLD-1']` → 1 >= 1, at capacity → ineligible.
- Partner `P-C` (zone `Z-3`): active and under capacity, but travel map has no entry for `(Z-3, R-X)` (partner-to-restaurant route missing) → ineligible; missing travel data is never treated as zero.
Result: `{'order_id': 'O-99', 'partner_id': None, 'pickup_minutes': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}` — the order is left unassigned with an explanatory reason.

## 3. Three edge cases
1. Duplicate cancellation.
   - Input: partner with `active_order_ids=['O1']`, `workload_minutes=18`, `minutes_by_order={'O1':18}`; call `process_cancellation(partner, 'O1', 'C1')` twice.
   - Expected: workload released once (0), active orders emptied, `processed_cancellation_ids == ['C1']` (duplicate ignored).
   - Actual: workload 0, active `[]`, ids `['C1']`. Verified by `test_duplicate_cancellation_does_not_release_twice`.
2. Invalid current time (`now="5"`).
   - Input: `estimate_eta(order, partner, travel, now="5")`.
   - Expected: `eligible=False`, `eta_minutes=None`, no crash (string time is not a valid timestamp).
   - Actual: `eligible=False`, `eta_minutes=None`. Verified by `test_estimate_eta_rejects_invalid_now` (previously raised `TypeError`).
3. Missing required travel route.
   - Input: partner zone `Z-3`, order restaurant `R-X`, travel map missing `(Z-3, R-X)`.
   - Expected: `eligible=False` (missing travel never treated as zero).
   - Actual: `eligible=False`, `eta_minutes=None`. Verified by `test_estimate_eta_rejects_invalid_travel_times` and `test_dataset_travel_conversion_and_dispatch_is_safe` over `data/records.json`.

## 4. Assumptions and limitations
- Tie-breaking: lowest ETA wins; ETA ties break by partner id in ascending lexicographic order (`str(partner_id)`), independent of input order.
- Workload accounting: cancellation reduces `workload_minutes` by `minutes_by_order[order_id]`, floored at zero; only active orders in `active_order_ids` are released.
- Cancellation idempotency: each `event_id` is processed once; duplicates are ignored and do not release workload or capacity twice.
- Eligibility: only partners with `active is True`, valid non-bool int capacity >= 1, and `len(active_order_ids) < capacity` are candidates; missing/invalid travel legs make a candidate ineligible.
- Data is synthetic; no live GPS, mobile app, or real delivery-partner data is used.
- No known remaining failures: `python -m pytest -q` → 266 passed, 0 failed.

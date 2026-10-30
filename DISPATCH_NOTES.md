# DISPATCH_NOTES.md — Required submission

## 1. Worked ETA example

From `fixtures.py` / `python -m main`:

- **Order:** `O-7`, restaurant `R-2`, destination zone `Z-9`, preparation 10 min.
- **Candidate partner P-2:** zone `Z-1`, workload 5 min, active, capacity 2 (`active_order_ids=['OLD-1']`, so 1 of 2 used; still eligible).
- **Candidate partner P-1:** zone `Z-3`, workload 2 min, active, capacity 2 (0 of 2 used; still eligible).

**Travel map (from `fixtures.py`):**
- `("Z-1", "R-2")` → 8 min (P-2 → restaurant)
- `("Z-3", "R-2")` → 12 min (P-1 → restaurant)
- `("R-2", "Z-9")` → 12 min (restaurant → destination)

**ETA calculation for P-2:**
- Pickup time = now(0) + leg1(8) + workload(5) = 13 min
- ETA = pickup(13) + prep(10) + leg2(12) = 35 min

**ETA calculation for P-1 (for comparison):**
- Pickup time = now(0) + leg1(12) + workload(2) = 14 min
- ETA = pickup(14) + prep(10) + leg2(12) = 36 min

**Result:** P-2 wins on lowest ETA (35 < 36).

**Actual result from `python -m main`:**
```
{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
```

## 2. No-eligible-partner example

**Scenario:** Order `O-99` with restaurant `R-X`, destination `Z-Y`, `now=0`.

| Partner | Zone | Active | Capacity | Active orders | Travel route `(zone, R-X)` | Eligible? | Reason |
|---------|------|--------|----------|---------------|---------------------------|-----------|--------|
| P-A | Z-1 | False | 2 | [] | exists (8 min) | No | `active is not True` |
| P-B | Z-2 | True | 1 | `['OLD-1']` | exists (5 min) | No | 1 >= 1 (at capacity) |
| P-C | Z-3 | True | 2 | [] | **missing** | No | travel route not in map; missing data never treated as zero |

**Result:**
```
{'order_id': 'O-99', 'partner_id': None, 'pickup_minutes': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}
```

The order is left unassigned with an explanatory reason. No partner is silently assigned based on a missing travel route treated as zero.

## 3. Three edge cases

### Edge case 1 — Duplicate cancellation

**Input:** Partner with `active_order_ids=['O1']`, `workload_minutes=18`, `minutes_by_order={'O1':18}`.
Call `process_cancellation(partner, 'O1', 'C1')` twice.

**Expected:** Workload released once (0), active orders emptied, `processed_cancellation_ids == ['C1']` (duplicate ignored).

**Actual:** Workload 0, active `[]`, ids `['C1']`.

**Evidence:** Verified by `test_duplicate_cancellation_does_not_release_twice` and `test_duplicate_cancellation_is_idempotent_across_workloads` (parametrized over workloads 0–999).

### Edge case 2 — Invalid current time (`now="5"`)

**Input:** `estimate_eta(order, partner, travel, now="5")` with valid travel legs and prep.

**Expected:** `eligible=False`, `eta_minutes=None`, no crash (string time is not a valid timestamp; the starter crashed with `TypeError` here).

**Actual:** `eligible=False`, `eta_minutes=None`.

**Evidence:** Verified by `test_estimate_eta_rejects_invalid_now`. Previously raised `TypeError: can only concatenate str (not "int") to str` at `service.py:9`.

### Edge case 3 — Missing required travel route

**Input:** Partner zone `Z-3`, order restaurant `R-X`, travel map missing `("Z-3", "R-X")`.

**Expected:** `eligible=False` (missing travel never treated as zero).

**Actual:** `eligible=False`, `eta_minutes=None`.

**Evidence:** Verified by `test_estimate_eta_rejects_invalid_travel_times` and `test_dataset_travel_conversion_and_dispatch_is_safe` over `data/records.json` (which contains deliberately missing routes).

## 4. Assumptions and limitations

- **Tie-breaking:** Lowest ETA wins; ETA ties break by partner ID in ascending lexicographic order (`str(partner_id)`), independent of input order.
- **Workload accounting:** Cancellation reduces `workload_minutes` by `minutes_by_order[order_id]`, floored at zero; only orders actually in `active_order_ids` are released.
- **Cancellation idempotency:** Each `event_id` is processed once; duplicates are ignored and do not release workload or capacity twice.
- **Eligibility:** Only partners with `active is True`, valid non-bool `int` capacity >= 1, and `len(active_order_ids) < capacity` are candidates. Missing or invalid travel legs make a candidate ineligible.
- **Data is synthetic:** No live GPS, mobile app, or real delivery-partner data is used.
- **No known remaining failures:** `python -m pytest -q` → 266 passed, 0 failed.

## 5. Demo result

`python -m main` output:
```
{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
```

# DISPATCH_NOTES.md — Required submission

## 1. Worked ETA example

**Order:** `O-7`, restaurant `R-2`, destination zone `Z-9`, prep_minutes = 10
**Partner:** `P-2`, zone `Z-1`, workload_minutes = 5, one active order

**Travel times:**
- Partner-to-restaurant: `(Z-1, R-2)` = 8 minutes
- Restaurant-to-customer: `(R-2, Z-9)` = 12 minutes

**Calculation:**
```
pickup_minutes = now + leg1 + workload
               = 0   + 8    + 5
               = 13

eta_minutes    = pickup_minutes + prep_minutes + leg2
               = 13            + 10           + 12
               = 35
```

**Actual result from `python -m main`:**
```python
{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
```

**Why P-2 was selected over P-1:**
- P-1 (zone `Z-3`): leg1 = `(Z-3, R-2)` = 12, but leg2 = `(R-2, Z-9)` = 12. However, `(Z-3, R-2)` travel exists but note the travel dict only has `('Z-3','R-2'):12` — and `('R-2','Z-9'):12` is present. P-1 workload = 2, so pickup = 0 + 12 + 2 = 14, ETA = 14 + 10 + 12 = 36.
- P-2 ETA (35) < P-1 ETA (36), so P-2 is selected.

## 2. No-eligible-partner example

**Order:** `O-99`, restaurant `R-5`, destination zone `Z-4`, prep_minutes = 10

**Partners:**
1. `P-A` (zone `Z-1`, capacity 1, active_order_ids = `['X']`) — **rejected: at capacity** (1 active order = capacity of 1).
2. `P-B` (zone `Z-2`, active = `False`) — **rejected: inactive**.
3. `P-C` (zone `Z-3`, active = `True`, capacity 2, 0 active orders) — has route `(Z-3, R-5)` = 5, but `(R-5, Z-4)` is **missing** from the travel map — **rejected: missing travel data**.

**Result:**
```python
{'order_id': 'O-99', 'partner_id': None, 'eta_minutes': None,
 'reason': 'no eligible partner or missing time data'}
```

No partner can receive a reliable ETA, so the order stays unassigned.

## 3. Three edge cases

### Edge case 1: Duplicate cancellation idempotency

**Input:** Partner `P` has `active_order_ids=['O1']`, `workload_minutes=15`, `minutes_by_order={'O1':15}`. Call `process_cancellation(partner, 'O1', 'C1')` twice.

**Expected:** After the first call, workload drops to 0 and `O1` is removed. The second call with the same event_id `C1` is a no-op — workload stays 0, `processed_cancellation_ids` contains exactly `['C1']`.

**Actual:** Matches expected. Verified by `test_duplicate_cancellation_is_idempotent` and `TestCancellationIdempotency::test_duplicate_event_id_no_double_release`.

### Edge case 2: Boolean `True` as travel time

**Input:** `travel = {('Z','R'): True, ('R','D'): 5}`. `True` is a subclass of `int` in Python.

**Expected:** Since `True` is a `bool`, it must be rejected — travel times must be plain `int` or `float`, not boolean. Partner should be ineligible.

**Actual:** `eligible=False`, `eta_minutes=None`. Verified by `test_invalid_or_missing_travel_time_rejected[True-1]`.

### Edge case 3: Tie-breaking is stable and independent of input order

**Input:** 10 partners `P0`–`P9` all in zone `Z`, all with same workload (0), same travel times, and `prep_minutes=0`. Partners are inserted in reverse order (`[P9, P8, ..., P0]`).

**Expected:** All partners produce the same ETA. Tie-break selects `P0` (lexicographically smallest).

**Actual:** `partner_id='P0'` regardless of input order. Verified by `test_ties_break_by_partner_id_independent_of_input_order`.

## 4. Assumptions and limitations

### Tie-breaking
Ties in ETA are broken by ascending lexicographic order of `partner_id`. This uses Python's string comparison via `str(partner_id)`.

### Workload accounting
- `workload_minutes` is added to the pickup time, representing the partner's remaining delivery workload.
- On cancellation, the cancelled order's minutes (from `minutes_by_order`) are subtracted from `workload_minutes`, clamped to a minimum of 0.

### Cancellation idempotency
- Each cancellation event has a unique `event_id`. Before applying, we check if `event_id` is already in `processed_cancellation_ids`. If so, the cancellation is skipped entirely (no workload or order-list change).
- This prevents double-release of capacity and workload.

### Validation strictness
- Only `bool` values of `True` are accepted for the `active` field. Integer `1`, strings like `"yes"`, etc. are rejected.
- Capacity must be a positive `int` (not `bool`). `True`, `0`, negative, `None`, and float capacities are rejected.
- Travel times, prep times, and `now` must be finite non-negative `int` or `float` values (not `bool`).
- Order string fields (`order_id`, `restaurant_id`, `destination_zone`) must be non-empty strings.

### Unresolved limitations
- No validation of `workload_minutes` on the partner (trusted as-is from the data).
- If `minutes_by_order` is missing an entry for a cancelled order, the workload reduction is 0 (silent fallback).
- The system handles one order at a time; no batch-assignment priority logic is implemented.

# DISPATCH_NOTES.md — Required submission

## 1. Worked ETA example

Using the sample inputs from `fixtures.py`:
- **Order:** `O-7`, restaurant `R-2`, customer zone `Z-9`, food prep = 10 mins.
- **Partner:** `P-2`, starts in zone `Z-1`, existing workload = 5 mins.
- **Travel times:** 
  - Leg 1 (`Z-1` to `R-2`) = 8 mins
  - Leg 2 (`R-2` to `Z-9`) = 12 mins

**Math:**
- `pickup = now (0) + leg1 (8) + workload (5) = 13 mins`
- `eta = pickup (13) + prep (10) + leg2 (12) = 35 mins`

**Result from `main.py`:**
`{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

*(P-2 is picked over P-1 because P-1's ETA comes out to 36 mins).*

---

## 2. No-eligible-partner example

**Order:** `O-99` (restaurant `R-5`, dropoff `Z-4`, prep = 10 mins).

We test three partners:
1. `P-A`: Capacity is 1, but they already have 1 active order $\rightarrow$ **Rejected (full)**.
2. `P-B`: Has `active=False` $\rightarrow$ **Rejected (offline)**.
3. `P-C`: Active and free, but the travel table is missing the route from restaurant `R-5` to `Z-4` $\rightarrow$ **Rejected (missing route)**.

**Output:**
`{'order_id': 'O-99', 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}`

---

## 3. Three edge cases

### 1. Duplicate cancellation event
- **Input:** Call `process_cancellation()` twice with the same order `O1` and event ID `C1`.
- **Expected:** The first call removes the order and drops workload to 0. The second call should do nothing.
- **Actual:** The order isn't removed twice and event ID isn't duplicated in the history list. Verified by `test_duplicate_cancellation_is_idempotent`.

### 2. Passing `True` as a travel time
- **Input:** Travel time given as `True` instead of a number like `5`.
- **Expected:** Should be rejected. In Python `True == 1`, so without a type check it would silently count as 1 minute.
- **Actual:** Marked `eligible=False` and ETA is `None`. Verified by `test_invalid_or_missing_travel_time_rejected[True-1]`.

### 3. Tie-breaking between identical ETAs
- **Input:** Two partners `A` and `B` with the exact same ETA (e.g. 20 mins).
- **Expected:** Partner `A` should always be picked because "A" comes before "B" alphabetically.
- **Actual:** Partner `A` is picked every time, even if partner `B` was listed first in the input list. Verified by `test_tie_break_by_partner_id`.

---

## 4. Assumptions and limitations

- **Tie-breaker:** Ties in ETA are broken alphabetically by `partner_id` using `str()`.
- **Workload floor:** When an order is cancelled, subtracting its time will never drop total workload below 0 (using `max(0, ...)`).
- **One by one:** The engine assigns one order at a time, not batch orders.
- **Trusting initial workload:** We assume the starter workload number on a partner is valid.

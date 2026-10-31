# DISPATCH_NOTES.md — Required submission

> The worked arithmetic below is calculated from the supplied fixture values. It is not represented as an observed program run.

## 1. Worked ETA example
Supplied fixture:
- Order: `O-7`
- Restaurant: `R-2`
- Destination zone: `Z-9`
- Preparation time: 10 minutes
- Candidate partner: `P-2`, whose zone is `Z-1`
- Partner-to-restaurant travel: `Z-1 -> R-2` = 8 minutes
- Remaining workload: 5 minutes
- Restaurant-to-customer travel: `R-2 -> Z-9` = 12 minutes
- Current time (`now`): 0

Calculation:
- Pickup = current time + partner-to-restaurant travel + remaining workload
- Pickup = `0 + 8 + 5 = 13` minutes
- ETA = pickup + preparation + restaurant-to-customer travel
- ETA = `13 + 10 + 12 = 35` minutes

The other fixture candidate, `P-1`, has 12 minutes to the restaurant, 2 minutes of workload, 10 minutes of preparation, and 12 minutes from restaurant to destination:
- Pickup = `0 + 12 + 2 = 14` minutes
- ETA = `14 + 10 + 12 = 36` minutes

Both candidates have the required travel entries in the supplied fixture. Based on the stated formula, `P-2` has the lower ETA (35 minutes versus 36 minutes). This is a calculation from fixture data; the actual output should be recorded after running `python main.py`.

## 2. No-eligible-partner example
Illustrative input condition (not an observed run):
- Candidate `P-A` is active but already has `len(active_order_ids) == capacity`; it is ineligible because capacity is full.
- Candidate `P-B` is active and below capacity, but its partner-to-restaurant travel key is absent; it cannot receive a reliable ETA and is ineligible.
- Expected service result: `partner_id=None`, `pickup_minutes=None`, `eta_minutes=None`, with a reason explaining that no eligible partner remains.

Record the exact actual result after executing a test for this case.

## 3. Three edge cases
1. **Missing travel leg**
   - Input: omit either `(partner_zone, restaurant_id)` or `(restaurant_id, destination_zone)` from the travel dictionary.
   - Expected behaviour: candidate is ineligible; missing travel is not substituted with zero.
   - Actual observed result: Not run / not supplied.
   - Test: add a test for each missing leg.

2. **Capacity reached**
   - Input: active partner with `len(active_order_ids) == capacity`.
   - Expected behaviour: partner is excluded from candidate selection.
   - Actual observed result: Not run / not supplied.
   - Test: add a test where the only partner is at capacity and verify an unassigned result.

3. **Duplicate cancellation event**
   - Input: process the same `event_id` twice for an order with recorded workload.
   - Expected behaviour: the second call does not remove workload or capacity a second time.
   - Actual observed result: Not run / not supplied.
   - Test: compare partner state after the first and second calls.

## 4. Assumptions and limitations
- Tie-breaking: compare ETA first, then partner ID in ascending lexicographic order.
- Workload accounting: `workload_minutes` is the remaining workload; `minutes_by_order[order_id]` is the amount to release when that order is cancelled.
- Cancellation idempotency: a previously processed event ID must not apply its state change again.
- Limitation: no runtime test output has been provided, so actual service behavior remains to be verified.

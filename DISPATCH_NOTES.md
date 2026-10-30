# Dispatch Notes

## How it works
`assign_order(order, partners, travel, now)` validates the order, filters
partners (active, valid capacity, `len(active_order_ids) < capacity`), computes
an ETA per remaining partner with `estimate_eta`, and picks the lowest ETA.
ETA ties go to the lexicographically smallest partner ID.

    pickup = now + partner_to_restaurant_travel + workload_minutes
    eta    = pickup + prep_minutes + restaurant_to_destination_travel

Travel legs are keyed `(partner zone, restaurant_id)` and
`(restaurant_id, destination_zone)`. A missing leg makes a partner ineligible;
it is never treated as 0.

## Worked ETA (sample fixture, now = 0)
Order O-7: restaurant R-2, destination Z-9, prep 10.

| Partner | Zone | Travel to R-2 | Workload | Pickup | + prep | + travel to Z-9 | ETA |
|---|---|---|---|---|---|---|---|
| P-2 | Z-1 | 8  | 5 | 0+8+5 = 13  | 23 | 12 | **35** |
| P-1 | Z-3 | 12 | 2 | 0+12+2 = 14 | 24 | 12 | 36 |

P-2 wins (35 < 36). Output:
`{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

## No eligible partner
P-2 is at capacity (capacity 1, holds OLD-1) and P-1 has no route from Z-3 to R-2.
Result: `partner_id: None`, `eta_minutes: None`,
`reason: 'no eligible partner or missing time data'`,
`details: ['P-2: at capacity', 'P-1: missing travel-time entry']`.
The order stays unassigned. The missing route is never treated as 0.

## Edge cases
1. **Duplicate cancellation:** replaying event `C1` returns the partner unchanged,
   so workload and capacity are released once and `C1` is recorded once.
2. **Fast partner with a missing route:** it is excluded, and a slower partner
   with complete data wins.
3. **Invalid times (`-1`, `nan`, `inf`, `True`, `"5"`, `None`):** rejected for
   `now`, prep, workload and both travel legs. `True` is rejected because
   `bool` is a subclass of `int`.

## Root causes found in the starter
1. Travel times not validated (negative, nan, inf, bool, string).
2. Prep time not validated, and a missing value defaulted to 0.
3. `now` not validated.
4. `assign_order` ignored order IDs, the `active` flag and capacity.
5. `process_cancellation` recorded the event ID but never checked it.

## Design decisions and limitations
- `active` uses truthiness (`0`/`None`/`False` inactive). A stricter `is True`
  check would also be reasonable.
- Cancelling an order the partner does not hold releases nothing but still
  records the event ID, so a replay is ignored.
- A different event ID for an already-released order is a no-op.
- Prep time is added after pickup as the spec states; we do not model
  `max(arrival, food ready)`. This is a known simplification.
- Inputs are never mutated (`deepcopy` in cancellation).
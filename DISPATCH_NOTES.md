# DISPATCH_NOTES.md — Required submission

All times are in minutes. `now` is passed in, and the code never reads the clock.

## 1. Worked ETA example
Order O-7: restaurant R-2, destination Z-9, preparation 10 minutes, now = 0 (data from `fixtures.py`).

| | P-2 | P-1 |
|---|---|---|
| zone | Z-1 | Z-3 |
| partner -> restaurant travel | 8 | 12 |
| remaining workload | 5 | 2 |
| pickup = now + travel + workload | 0 + 8 + 5 = 13 | 0 + 12 + 2 = 14 |
| ETA = pickup + prep + restaurant -> customer travel (12) | 13 + 10 + 12 = 35 | 14 + 10 + 12 = 36 |

P-2 has the lowest ETA (35 < 36), so it is assigned. Actual output of `python -m main`:

`{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

Test: `tests/test_dispatch_regressions.py::test_worked_eta_numbers`

## 2. No-eligible-partner example
Order O (restaurant R, destination D), three partners, empty travel table:
- P1 is inactive.
- P2 has capacity 1 and one active order, so it is at capacity.
- P3 is active with free capacity, but no travel data exists for it.

Actual result:

`{'order_id': 'O', 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner (P1: inactive; P2: at capacity; P3: missing travel time)'}`

The order stays unassigned, and the reason lists every partner. The text is the same whatever order the partners are supplied in.

Test: `test_no_eligible_partner_reports_each_reason`

## 3. Three edge cases
1. Missing travel is not zero.
   - Input: prep 0. Partner A has no partner -> restaurant route. Partner B has route 50 and restaurant -> customer 1.
   - Expected: A is excluded and never treated as ETA 0. B is assigned with pickup 50 and ETA 51.
   - Actual: partner B, ETA 51.
   - Test: `test_missing_partner_leg_is_not_zero`. Also `tests/test_contract.py::test_missing_travel_is_not_zero`.
2. Tie-break by partner ID.
   - Input: partners P2 and P10 with the same ETA, supplied in both orders.
   - Expected: P10 wins both times, because "P10" < "P2" as strings.
   - Actual: P10 and P10.
   - Test: `test_eta_tie_breaks_by_string_partner_id`. Also `tests/test_contract.py::test_tie_break_by_partner_id`.
3. Duplicate cancellation.
   - Input: a partner with orders A (10 min) and B (20 min), workload 30. Cancel A with event C1, then repeat C1 for A, and separately reuse C1 for B.
   - Expected: workload and capacity are released once. The repeat changes nothing, and a reused event ID is ignored.
   - Actual: active orders = ['B'], workload = 20 after the first event. The repeat returns an identical partner. Reusing C1 for B leaves B active with workload 20.
   - Test: `test_duplicate_cancellation_releases_once`, `test_same_event_id_for_another_order_is_ignored`


## 4. Assumptions and limitations
- A partner is eligible when `active is True` and `len(active_order_ids) < capacity`. Capacity must be an int >= 1 and not a bool.
- Remaining workload is the partner's `workload_minutes`. If the key is absent it counts as 0. This is the only default, and it is never applied to travel times.
- Tie-break: lowest ETA first, then partner ID in ascending string order.
- ETAs are sums of whole minutes, so ties are exact. With float times, rounding could turn a true tie into a non-tie.
- Cancellations are deduplicated by event ID. An event with no valid ID cannot be deduplicated by ID, so it relies on the order having already been removed from the active list.
- Travel times are static estimates. There is no fallback for partial data, and one order is assigned at a time.
- `assign_order` returns a decision and does not update the partner's load.
- Known gaps: a non-dict partner passed directly to `estimate_eta` or `process_cancellation`, and a corrupt `minutes_by_order` value, are not handled.
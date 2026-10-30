# Dispatch Notes

## 1. Worked ETA example

Order `O-7` is from restaurant `R-2` to destination zone `Z-9`, with 10 minutes of preparation time. Partner `P-2` starts in zone `Z-1`, has 5 minutes of remaining workload, and the current time is minute 0.

- Partner to restaurant travel: 8 minutes
- Pickup time: `0 + 8 + 5 = 13` minutes
- Restaurant preparation: 10 minutes
- Restaurant to customer travel: 12 minutes
- ETA: `13 + 10 + 12 = 35` minutes

The demo returned `P-2`, pickup minute 13, ETA 35. Partner `P-1` has a 12-minute first leg and 2 minutes of workload, so its ETA is `0 + 12 + 2 + 10 + 12 = 36`; `P-2` correctly wins.

## 2. No-eligible-partner example

Order `O-NONE` needs a route from restaurant `R` to destination `D`.

- `P-FULL` is active but has capacity 1 and already has one active order.
- `P-ROUTE` is active and below capacity, but only its zone-to-restaurant route is provided; the restaurant-to-destination route is missing.

Observed result:

```text
{'order_id': 'O-NONE', 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner: missing or invalid travel-time data; partner at capacity'}
```

The order remains unassigned. The reason names both exclusion causes rather than treating the missing route as zero travel time.

## 3. Three edge cases

1. **Missing route:** A partner has one required route but not the other. Expected and observed: ineligible ETA with `eta_minutes=None`. Verified by `test_eta_is_ineligible_when_either_required_route_is_missing`.
2. **Capacity boundary:** A partner with capacity 1 already has one active order. Expected and observed: not selected. Verified by `test_full_partner_not_assigned` and `test_capacity_boundary_matrix`.
3. **Duplicate cancellation event:** Cancel order `O1` with event `C1`, then replay event `C1` for `O2`. Expected and observed: `O2` stays active, workload remains for `O2`, and `C1` appears once. Verified by `test_duplicate_cancellation_event_cannot_cancel_another_order`.

## 4. Assumptions and limitations

- Partner IDs and order/zone identifiers are non-empty strings. Active status must be the boolean `True`; capacity must be a positive integer.
- Minute values may be integers or finite floats, but must be non-negative. `now` and workload are expressed in the same minute-based time scale.
- ETA uses the required formula: current time + first-leg travel + remaining workload + preparation + second-leg travel.
- ETA ties are resolved by ascending partner ID. A pickup-time key makes output deterministic if duplicate partner IDs have the same ETA; duplicate IDs should still be corrected in input data.
- Cancellation events are uniquely identified by `event_id`. Reprocessing an event is a no-op; cancelling an unknown order does not release workload.
- No live GPS, changing traffic, restaurant state updates, or batch-assignment behavior is implemented; these are outside the required scope.

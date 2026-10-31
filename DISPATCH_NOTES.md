# Dispatch notes

## Worked ETA
The repository's `sample_inputs()` supplies order O-7, restaurant R-2, destination Z-9, and preparation time 10. P-2 is in Z-1, has 5 minutes of workload, and travels 8 minutes to the restaurant. Restaurant-to-customer travel is 12. With `now=0`, pickup = 0 + 8 + 5 = **13**; ETA = 13 + 10 + 12 = **35**. Running `python -m main` returned `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`. P-1 has pickup 14 and ETA 36, so P-2 wins.

## No eligible partner
For order O at R going to D, a partner with capacity 1 and one active order is full. Another active partner whose restaurant-to-customer route is missing cannot receive a reliable ETA. Neither qualifies; `assign_order` returns `partner_id=None`, `eta_minutes=None` and the reason `no eligible partner or missing time data`.

## Three edge cases
1. **Missing route:** `{('Z','R'): 0}` lacks `('R','D')`. Expected and observed: no assignment (`test_missing_route_does_not_default_to_zero`).
2. **Tie:** A and B share the same zone and ETA; input order reversed. Expected and observed: A selected (`test_tie_independent_of_input_order`).
3. **Repeated cancellation:** event EVENT cancels O; an O with new workload is subsequently present and the same event is replayed. Expected and observed: second event leaves capacity/workload untouched (`test_duplicate_event_does_not_release_reused_order_id`).

## Assumptions and limitations
ETAs are absolute minutes relative to the supplied `now`; the specified formula adds preparation after pickup rather than overlapping preparation with travel. Active orders are represented by `active_order_ids`, and workload by `workload_minutes`. `assign_order` is a pure selection function: it does not reserve capacity or mutate partner records. Callers coordinating concurrent assignments must persist reservations atomically. Cancellation event IDs are assumed unique across events for each partner; processed IDs are retained indefinitely. Cancellation uses per-order workload only if non-negative and valid. No external map, GPS or network data is used.

## V3 optional stretch: candidate explanations

`explainer.explain_dispatch(order, partners, travel, now)` returns `decision` (the unchanged `assign_order` response) and `candidates` (one row per supplied partner). Each row reports its ID, eligibility, pickup/ETA when known, status, and a human-readable explanation. The inspector sorts partner IDs for a repeatable display, independent of input ordering. It never substitutes zero for missing travel.

Illustrative equal-ETA case: order prep=12, customer travel=10, partner travel=8, workload=0, now=0. Both P-01 and P-02 have pickup=8, ETA=30. P-01 wins because its ID is lexicographically smaller. In a no-partner case the engine returns an unassigned decision and an empty candidate list. If P-01 instead has no partner-to-restaurant travel record, its ETA is unknown (None), not 22 or 0; the inspector labels it `Missing travel data`.

This is the **only optional stretch feature** included in the evaluation engine. The Streamlit dashboard is an optional demonstration interface, not GPS or a persistent logistics service.

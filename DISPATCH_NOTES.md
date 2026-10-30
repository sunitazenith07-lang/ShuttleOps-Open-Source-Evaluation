# Dispatch notes

These examples were checked during the Codex-assisted work described in approach.md. Times below are minutes relative to the supplied `now` value.

## Worked ETA from the demo

Order `O-7` is picked up at `R-2` and delivered to `Z-9`. Preparation takes 10 minutes and restaurant-to-customer travel takes 12 minutes. Current time is 0.

| Partner | Travel to restaurant | Remaining workload | Pickup calculation | ETA calculation |
|---|---:|---:|---|---|
| P-2 | 8 | 5 | 0 + 8 + 5 = 13 | 13 + 10 + 12 = 35 |
| P-1 | 12 | 2 | 0 + 12 + 2 = 14 | 14 + 10 + 12 = 36 |

Both partners are active and below capacity. P-2 wins because 35 is lower than 36. The actual `python -m main` output was:

```text
{'order_id': 'O-7', 'partner_id': 'P-2', 'eta_minutes': 35, 'pickup_minutes': 13, 'reason': 'assigned'}
```

The calculation adds preparation after pickup, as required by this assignment. It does not model preparation happening in parallel with partner travel.

## No eligible partner

A separate local example used order O, restaurant R and destination D. Partner A in zone X had capacity 1 and already had order OLD. Partner B in zone Y had spare capacity, but its route to R was missing. The only travel entry supplied was R to D = 4.

A was rejected because it was full. B was rejected because its pickup travel time was unknown. The observed result was:

```text
{'order_id': 'O', 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner: missing travel time; partner is at capacity'}
```

This example was run directly through `assign_order()`. Missing-route and full-capacity behaviour also have dedicated tests in `test_contract.py`.

## Edge cases

1. **Equal ETA:** A and Z have the same route timing, with Z supplied first. A must win because IDs are compared lexicographically. The actual selection was A. Evidence: `test_contract.py::test_tie_break_by_partner_id`.
2. **Repeated cancellation:** an order with 9 minutes is cancelled twice using C1. Expected and observed: workload becomes 0 and history contains C1 once. Evidence: `test_contract.py::test_duplicate_cancellation_is_idempotent`.
3. **Missing route:** an empty travel mapping cannot produce an ETA. Expected and observed: `eligible` is false and ETA is `None`. Evidence: `test_contract.py::test_missing_travel_is_not_zero`.
4. **Zero duration:** both travel legs and preparation can be zero. Expected and observed: a valid ETA of 0. Evidence: `test_regressions.py::test_missing_route_explained_and_zero_route_allowed`.

5. **Missing cancellation accounting:** the fixture has OLD-1 active with 5 workload minutes but no per-order minutes. The first cancellation leaves state and history unchanged. After adding the 5-minute entry, retrying the same event removes the order and releases the workload. Evidence: `test_accounting.py::test_fixture_incomplete_accounting_can_be_repaired_and_retried`.
6. **Already-active order:** O appears on a supplied partner's active-order list. Assignment returns no partner and reason `order is already active`, whether the existing partner is active or inactive. Evidence: `test_accounting.py::test_already_active_order_is_not_assigned_to_another_partner`.

## Assumptions and limitations

Identifiers must be nonempty strings; whitespace-only values are rejected. IDs are compared as strings, so P10 sorts before P2. Durations may be integers or floats, but cannot be booleans, negative values, NaN or infinity.

The caller supplies current workload and active orders. Assignment rejects orders already active in the supplied state, then returns a choice without changing those records or reserving capacity. The caller must record a new assignment before using that state for subsequent requests. Cancellation returns a deep copy, removes the active order and its per-order minutes, and clamps remaining workload at zero. Repeated event IDs are ignored for that partner. Event history is not shared across partners.

Cancellation requires a valid active-order list, total workload, and per-order accounting map. An active order must have its own valid recorded minutes; an explicit zero is accepted, but a missing entry is not. Incomplete accounting, invalid input, or unrepresentable arithmetic returns unchanged state without consuming the event ID. After correcting the data, the caller can retry the same event. The existing API still returns only partner state, without a separate error field.

No live GPS, database, batch-assignment feature or concurrent reservation system is included.

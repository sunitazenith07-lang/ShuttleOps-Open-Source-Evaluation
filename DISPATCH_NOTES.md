# Dispatch Notes

## Worked ETA example

For order `O-7`, partner `P-2` starts in `Z-1` with 5 minutes of remaining workload. The route from `Z-1` to `R-2` is 8 minutes, preparation is 10 minutes, and the restaurant-to-`Z-9` route is 12 minutes.

`pickup = 0 + 8 + 5 = 13`

`ETA = 13 + 10 + 12 = 35`

The demo returns `P-2`, pickup 13, ETA 35.

## No eligible partner example

For order `O` from `R` to `D`, `FULL` has capacity 1 and already has one active order, so it is excluded. `MISSING` is active but has only a `Y -> R` route; its required `R -> D` route is absent. The observed result is `{'order_id': 'O', 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}`.

## Edge cases

1. Missing travel data: input has no required route. Expected: no ETA and no assignment. Actual: `eta_minutes` and `partner_id` are `None`. Verified by `test_missing_travel_is_not_zero`.
2. ETA tie: input places `B` before `A`, each with ETA 2. Expected: `A` by lexicographic tie-break. Actual: `A` was selected with pickup 1 and ETA 2. Verified by `test_tie_break_by_partner_id`.
3. Duplicate cancellation: input cancels order `O` twice using event `C-1`; initial workload is 8 and the order accounts for 5 minutes. Expected: one event record and workload 3. Actual: `processed_cancellation_ids` is `['C-1']`, `active_order_ids` is empty, and workload is 3. Verified by `test_cancellation_records_once_and_does_not_mutate_input`.

## Assumptions and limitations

Time values must be finite, non-negative numbers; identifiers are non-empty strings; and a partner is active only when `active is True`. Capacity is the length of `active_order_ids`. Cancellation returns a copied record and uses `processed_cancellation_ids` for idempotency. This module does not coordinate concurrent assignments or persistent storage.

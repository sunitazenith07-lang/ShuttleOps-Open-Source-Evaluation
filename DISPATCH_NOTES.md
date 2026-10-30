# Dispatch Notes

## Worked ETA example

For order `O-7`, partner `P-2` starts in `Z-1` with 5 minutes of remaining workload. The route from `Z-1` to `R-2` is 8 minutes, preparation is 10 minutes, and the restaurant-to-`Z-9` route is 12 minutes.

`pickup = 0 + 8 + 5 = 13`

`ETA = 13 + 10 + 12 = 35`

The demo returns `P-2`, pickup 13, ETA 35.

## No eligible partner example

For an order from `R` to `D`, a full partner at capacity is excluded before ETA calculation. A second otherwise-active partner without `R -> D` travel data is also excluded. With no valid candidate, `assign_order` returns the order ID with `partner_id` and `eta_minutes` set to `None` and a reason explaining that no eligible partner or usable time data exists.

## Edge cases

1. Missing travel data: a missing route yields no ETA, not a zero-minute route. Verified by `test_missing_travel_is_not_zero`.
2. ETA tie: equal candidate ETAs select the lexicographically smaller partner ID regardless of list order. Verified by `test_tie_break_by_partner_id`.
3. Duplicate cancellation: repeating the same event keeps one event ID and does not release workload again. Verified by `test_cancellation_records_once_and_does_not_mutate_input`.

## Assumptions and limitations

Time values must be finite, non-negative numbers; identifiers are non-empty strings; and a partner is active only when `active is True`. Capacity is the length of `active_order_ids`. Cancellation returns a copied record and uses `processed_cancellation_ids` for idempotency. This module does not coordinate concurrent assignments or persistent storage.

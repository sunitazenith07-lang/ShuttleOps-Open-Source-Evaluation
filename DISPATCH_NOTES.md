# Dispatch Notes

## 1. Worked ETA example
For sample order `O-7`, candidate `P-2` has partner-to-restaurant travel 8 minutes, remaining workload 5 minutes, preparation time 10 minutes, and restaurant-to-customer travel 12 minutes. With `now=0`:

- Pickup = `0 + 8 + 5 = 13` minutes
- ETA = `13 + 10 + 12 = 35` minutes

The demo produced partner `P-2`, pickup `13`, ETA `35`, and reason `assigned`.

## 2. No-eligible-partner example
Consider an order with preparation `10` and destination `D`, two partners, and these routes:

- `P-FULL`: active, capacity `1`, one active order; ineligible because capacity is reached.
- `P-MISSING`: active below capacity, missing route `Z -> R`; ETA cannot be calculated reliably.

`assign_order(...)` returns `partner_id=None`, `eta_minutes=None`, and reason `no eligible partner or missing time data`.

## 3. Edge cases
1. **Negative preparation:** input preparation `-5`. Expected and observed: no assignment, verified by `test_negative_prep_time_is_rejected`.
2. **Equal ETA:** partners `A` and `Z` have identical required travel and workload. Expected and observed: `A` wins by ascending partner ID, verified by `test_tie_break_by_partner_id`.
3. **Duplicate cancellation:** partner has workload 9 for active order `O1`; cancelling `O1` with event `C1` twice. Expected and observed: workload becomes `0`, and processed IDs remain `['C1']`, verified by `test_duplicate_cancellation_is_idempotent`.

## 4. Assumptions and limitations
- Only partners with exactly `active=True`, a valid integer capacity of at least one, and fewer active orders than capacity are considered.
- Missing or invalid required travel values make a partner ineligible; zero is valid but missing is not represented as zero.
- Lower ETA wins; equal ETAs are ordered by partner ID.
- Cancellation workload is floored at zero and cancellation event IDs are processed once. The implementation copies a partner dictionary rather than mutating its input.
- Synthetic challenge data only; live traffic and persistence are outside this implementation.

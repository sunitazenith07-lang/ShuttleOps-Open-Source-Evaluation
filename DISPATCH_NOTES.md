# Dispatch notes

## 1. Worked ETA example
The offline demo uses order `O-7` (`R-2` to `Z-9`) and partner `P-2` in `Z-1`. The partner has 5 minutes of workload; travel to the restaurant is 8 minutes; preparation is 10 minutes; travel from restaurant to destination is 12 minutes. At `now=0`:

- Pickup: `0 + 8 + 5 = 13`
- ETA: `13 + 10 + 12 = 35`
- Observed demo result: `partner_id=P-2`, `pickup_minutes=13`, `eta_minutes=35`.

## 2. No-eligible-partner example
For order `O` from restaurant `R` to destination `D`, candidate `P-full` has capacity 1 and already has one active order. Candidate `P-route` is active and below capacity but has only the `Y -> R` route; `R -> D` is missing. The observed result is:

```text
{'order_id': 'O', 'partner_id': None, 'eta_minutes': None,
 'reason': 'no eligible partner or missing time data'}
```

## 3. Three edge cases
1. A negative or missing required travel time makes the ETA ineligible rather than treating that leg as zero. Verified by `test_invalid_or_missing_travel_time_rejected`.
2. An inactive or full partner is not assigned, even when route data is available. Verified by `test_inactive_partner_not_assigned` and `test_capacity_boundary_matrix`.
3. Replaying a cancellation event does not remove workload twice or duplicate its event ID. Verified by `test_duplicate_cancellation_is_idempotent` and `test_duplicate_cancellation_is_idempotent_across_workloads`.

## 4. Assumptions and limitations
- ETA ties are broken by ascending lexicographic partner ID.
- Workload minutes are added to partner-to-restaurant travel time; cancellation subtracts the matching per-order minutes and clamps the remaining total at zero.
- Processed cancellation IDs are retained on each partner record. A caller must persist that record for deduplication to survive a restart.
- The service has no persistence or live travel-time integration; tests use synthetic, in-memory records.

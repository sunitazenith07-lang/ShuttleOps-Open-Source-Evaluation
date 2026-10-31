# Dispatch notes

## 1. Worked ETA example

The offline fixture order is `O-7` (`R-2` to `Z-9`) with 10 minutes of restaurant preparation. Partner `P-2` starts in `Z-1`, has 5 minutes of remaining workload, and the fixture contains travel times of 8 minutes from `Z-1` to `R-2` and 12 minutes from `R-2` to `Z-9`. With `now=0`:

- Pickup: `0 + 8 + 5 = 13` minutes.
- Delivery ETA: `13 + 10 + 12 = 35` minutes.
- Observed demo result: `P-2`, pickup 13, ETA 35, reason `assigned`.

## 2. No eligible partner example

Use order `O` from restaurant `R` to destination `D`; give `P-FULL` capacity 2 with two active orders, and give `P-ROUTE` a valid `X` to `R` travel time but omit `R` to `D`. `P-FULL` is rejected at capacity and `P-ROUTE` has no complete ETA. The service returns `partner_id=None`, `eta_minutes=None`, and reason `no eligible partner (capacity reached: 1; missing or invalid ETA data: 1)`. The regression `test_no_candidate_reason_names_capacity_and_route_problems` verifies both reasons.

## 3. Edge cases

1. **Missing route:** Omit either travel tuple. Expected: `eligible=False` and `eta_minutes=None`. Actual: passed `test_eta_is_ineligible_when_either_required_route_is_missing`.
2. **Capacity reached:** Set `len(active_order_ids) == capacity`. Expected: no assignment to that partner. Actual: passed `test_capacity_boundary_matrix`.
3. **Duplicate cancellation:** Apply the same event ID twice to an active order with 9 minutes recorded. Expected: order removed, workload reduced to 0 once, event ID listed once. Actual: passed `test_duplicate_cancellation_is_idempotent_across_workloads`.

## 4. Assumptions and limitations

- Time values are finite, non-negative integer or float minutes; booleans and numeric strings are invalid.
- A partner is eligible only when `active is True`, capacity is a positive integer, and active order count is below capacity. ETA ties use ascending lexicographic partner ID.
- `workload_minutes` is remaining work before this order is picked up. Cancellation uses `minutes_by_order` and clamps workload at zero.
- A cancellation event needs a non-empty stable string `event_id`. Duplicate IDs do not change state again. Unknown order IDs are recorded once but do not release workload.
- The module is in-memory; persistence and concurrent event processing are caller responsibilities.

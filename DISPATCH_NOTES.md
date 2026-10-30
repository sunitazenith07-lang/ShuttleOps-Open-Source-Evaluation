# DISPATCH_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked ETA example
Show an order, the candidate partner, partner-to-restaurant travel time, remaining workload, restaurant preparation time, restaurant-to-customer travel time, the ETA calculation, and the actual result.
- Order: `{"order_id": "O1", "restaurant_id": "R1", "destination_zone": "D1", "prep_minutes": 10}`
- Partner: `{"partner_id": "P1", "zone": "Z1", "active": True, "capacity": 2, "active_order_ids": ["OLD1"], "workload_minutes": 5}`
- Travel & time: `now = 0`, `("Z1", "R1") = 4`, `("R1", "D1") = 6`
- Calculation: `pickup = 0 + 4 + 5 = 9`; `eta = 9 + 10 + 6 = 25`
- Actual result: `{"partner_id": "P1", "pickup_minutes": 9, "eta_minutes": 25, "eligible": True}`

## 2. No-eligible-partner example
Show why each candidate is ineligible (for example, capacity reached or required travel-time data missing) and how the service reports the order as unassigned.
- Order: `new_order("O1", "R1", "D1", 10)` with `travel = {("Z1", "R1"): 3, ("R1", "D1"): 5}`
- P1 (`active=False`): Rejected because partner is inactive.
- P2 (`capacity=1, active_order_ids=["A"]`): Rejected because capacity is full (`1 < 1` is False).
- P3 (`zone="Z_MISSING"`): Rejected because route `("Z_MISSING", "R1")` is not in `travel`.
- Actual result: `{"order_id": "O1", "partner_id": None, "pickup_minutes": None, "eta_minutes": None, "reason": "no eligible partner or missing time data"}`

## 3. Three edge cases
For each, state input, expected behaviour, actual observed result, and test that verifies it.
1. Duplicate cancellation: Calling `process_cancellation(p, "O1", "C1")` twice on a partner with `workload_minutes=9`. Expected: Subtract workload once and record `"C1"` once. Actual: `workload_minutes=0`, `processed_cancellation_ids=["C1"]`. Test: `test_duplicate_cancellation_is_idempotent`.
2. Boolean/NaN inputs: Passing `now=True`, `prep_minutes=float("nan")`, or `capacity=True`. Expected: Reject booleans and `NaN`. Actual: `eligible: False` and `partner_id: None`. Tests: `test_current_time_validation[True]`, `test_preparation_time_validation[nan]`, `test_capacity_boundary_matrix[True-0]`.
3. Negative times: Passing `prep_minutes=-5` or travel leg `-1`. Expected: Reject negative durations. Actual: `eligible: False` and `partner_id: None`. Tests: `test_negative_prep_time_is_rejected`, `test_invalid_or_missing_travel_time_rejected[-1-1]`.

## 4. Assumptions and limitations
Document tie-breaking, workload accounting, cancellation idempotency, and any unresolved issue.
- Tie-breaking: Equal ETAs break deterministically by `str(partner_id)` using `min(options, key=lambda item: (item["eta_minutes"], str(item["partner_id"])))`.
- Workload accounting: `pickup = now + leg1 + workload_minutes` and `eta = pickup + prep_minutes + leg2`. Cancelled workload is floored at `0`.
- Cancellation idempotency: Uses a deep copy and returns early if `event_id in processed_cancellation_ids`.
- Limitations: Greedily assigns one order at a time without batch optimization or mutating partner state in place.
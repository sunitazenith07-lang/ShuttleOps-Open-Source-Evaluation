# Dispatch Engine Notes

## 1. Worked ETA Calculation Example
A candidate assignment sequence is evaluated using the following operational data layout:
- **Current Reference Time (`now`):** 0
- **Order Preparation Time (`prep_minutes`):** 10
- **Partner Current Workload (`workload_minutes`):** 5
- **Travel Node Leg 1 (`partner['zone']` to restaurant):** 8 minutes
- **Travel Node Leg 2 (restaurant to `order['destination_zone']`):** 12 minutes

### Time Evaluation Matrix Math:
1. `pickup_minutes` = current_time (0) + Leg 1 travel (8) + existing workload (5) = **13 minutes**
2. `eta_minutes` = pickup_minutes (13) + prep_minutes (10) + Leg 2 travel (12) = **35 minutes**

**Result:** Partner is assigned with an explicit pickup point at minute 13 and delivery ETA at minute 35.

## 2. Unassigned Order Scenario (No Eligible Partner)
- **Scenario:** Order `O-99` requires travel from Zone `Z-1` to `Z-2`.
- **Condition:** All active available partners are registered inside Zone `Z-3`, and no mapping exists within the `travel` database for `('Z-3', 'Restaurant_ID')`.
- **Engine Resolution:** Lookups return `None`. The engine drops the candidate from the active priority queue. If zero viable tracking pathways are matched across the entire collection, the assignment returns:
  ```json
  {
    "order_id": "O-99",
    "partner_id": null,
    "eta_minutes": null,
    "reason": "no eligible partner or missing time data"
  }
  ```

## 3. Systemic Assumptions
- **Static Travel Configurations:** Travel durations across geographical zone configurations remain fixed for the duration of an assignment loop execution.
- **Strict Capacity Constraints:** A delivery partner's capacity ceiling is an absolute physical limit. If a partner is at capacity, they cannot accept new assignments under any circumstances, even if their current ETA is lower than alternative candidates.
- **Lexicographical Stability:** When two partners produce identical fulfillment metrics, ties are resolved deterministically using a string-based ascending sort on their structural `partner_id`.

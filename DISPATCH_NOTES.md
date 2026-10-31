# DISPATCH_NOTES.md — Required submission

## 1. Worked ETA example

**Order details:**
- Order ID: O-7
- Restaurant ID: R-2
- Destination zone: Z-9
- Preparation time: 10 minutes

**Candidate partner:**
- Partner ID: P-2
- Current zone: Z-1
- Remaining workload: 5 minutes
- Partner-to-restaurant travel time: 8 minutes
- Restaurant-to-customer travel time: 12 minutes

**ETA calculation:**

Pickup Time = 8 + 5 = 13 minutes

ETA = 13 + 10 + 12 = **35 minutes**

**Actual result:** P-2 was assigned successfully with a pickup time of 13 minutes and an ETA of 35 minutes.

## 2. No-eligible-partner example

**Order:** O-8

Two candidate partners are considered:

- **P-1:** Rejected because it has reached its maximum capacity.
- **P-2:** Rejected because restaurant-to-customer travel-time data is missing.

**Actual result:**

```python
{
    'order_id': 'O-8',
    'partner_id': None,
    'eta_minutes': None,
    'reason': 'no eligible partner or missing time data'
}
```

The order remains unassigned because no candidate has valid eligibility and travel-time information.

## 3. Three edge cases

### 1. Missing travel-time data
- **Input:** Required travel-time route is missing.
- **Expected:** Reject the candidate instead of assuming zero travel time.
- **Actual:** Candidate rejected; ETA remains None.
- **Test:** `test_unassigned_reason_is_returned_when_all_candidates_lack_travel_data`

### 2. Duplicate cancellation event
- **Input:** Same order cancellation event is processed twice.
- **Expected:** Workload must be deducted only once.
- **Actual:** Workload is deducted once; subsequent processing does not deduct it again.
- **Test:** `test_duplicate_cancellation_is_idempotent`

### 3. Unknown order cancellation
- **Input:** Cancellation requested for an order not present in the partner's active orders.
- **Expected:** Cancellation must not be processed or recorded.
- **Actual:** Active orders, workload and processed cancellation IDs remain unchanged.
- **Test:** `test_unknown_cancellation_does_not_record_event`

## 4. Assumptions and limitations

- **Tie-breaking:** Lowest ETA wins. Equal ETAs are resolved using partner ID in ascending order.
- **Workload accounting:** Existing workload is included in pickup-time calculation. Cancellation releases the workload recorded for that order.
- **Cancellation idempotency:** Previously processed event IDs prevent duplicate deductions. Unknown orders are rejected without recording their event IDs.
- **Limitations:** Assignment selection does not automatically update partner workload or active orders. A separate state-management operation is required to commit assignments.
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
- Travel time (Partner → Restaurant): 8 minutes
- Travel time (Restaurant → Customer): 12 minutes

**ETA calculation:**

Pickup Time = 8 + 5 = 13 minutes

ETA = 13 + 10 + 12 = 35 minutes

**Actual result:**

```python
{
    'order_id': 'O-7',
    'partner_id': 'P-2',
    'pickup_minutes': 13,
    'eta_minutes': 35,
    'reason': 'assigned'
}
```

The service successfully assigns the order to P-2 with an ETA of 35 minutes.

## 2. No-eligible-partner example

**Order:** O-8

Two candidate partners are considered:

- **P-1:** Excluded because its capacity is reached.
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

The order remains unassigned because neither partner has valid assignment eligibility.

## 3. Three edge cases

### 1. Missing travel-time data
- **Input:** Required restaurant-to-customer travel time is missing.
- **Expected:** Reject the candidate instead of assuming zero travel time.
- **Actual:** Candidate rejected; no reliable ETA calculated.
- **Test:** Missing travel data rejected.

### 2. Partner at full capacity
- **Input:** Partner has reached its maximum capacity.
- **Expected:** Partner must not receive another order.
- **Actual:** Partner excluded from assignment.
- **Test:** Full capacity excluded.

### 3. Duplicate cancellation event
- **Input:** Same cancellation event is processed twice.
- **Expected:** Workload must be deducted only once.
- **Actual:** Workload decreases from 15 to 5 minutes on the first cancellation and remains 5 minutes on the duplicate.
- **Test:** Duplicate cancellation deducted once.

## 4. Assumptions and limitations

- **Tie-breaking:** Lowest ETA wins. Equal ETAs are resolved using partner ID in ascending order.
- **Workload accounting:** Existing workload is included in pickup-time calculation. Cancellation releases workload associated with the cancelled order.
- **Cancellation idempotency:** Previously processed cancellation event IDs prevent duplicate workload deductions.
- **Limitations:** Unknown order cancellation events can still be recorded as processed. Assignment itself does not update partner workload or active orders; that requires a separate state-management operation.

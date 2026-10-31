# DISPATCH_NOTES.md — Required submission

## 1. Worked ETA example

Consider an order with the following details:

**Order details:**
- Order ID: O-7
- Restaurant ID: R-2
- Customer destination: Z-9
- Preparation time: 10 minutes

**Selected delivery partner:**
- Partner ID: P-2
- Current zone: Z-1
- Current workload: 5 minutes
- Active orders: 1
- Capacity: 2

**Travel information:**
- Partner to restaurant: 8 minutes
- Restaurant to customer: 12 minutes

**ETA calculation:**

Pickup time = Current time + Partner-to-restaurant travel time + Remaining workload

Pickup time = 0 + 8 + 5 = 13 minutes

Final ETA = Pickup time + Preparation time + Restaurant-to-customer travel time

Final ETA = 13 + 10 + 12 = **35 minutes**

**Actual result:**

The service selected partner P-2 and returned:

- Partner ID: P-2
- Pickup time: 13 minutes
- ETA: 35 minutes
- Reason: assigned

The other eligible partner, P-1, had an ETA of 36 minutes. Therefore, P-2 was selected because it had the lower ETA.

## 2. No-eligible-partner example

Consider an order with the following details:

- Order ID: O-100
- Restaurant ID: R-100
- Customer destination: Z-100
- Preparation time: 10 minutes

Three delivery partners are available as candidates:

**Partner P-101: Inactive partner**

- Active status: False
- Expected behaviour: The partner should be skipped because inactive partners cannot receive orders.

**Partner P-102: Full capacity**

- Capacity: 1
- Active orders: 1
- Expected behaviour: The partner should be skipped because it has reached its maximum capacity.

**Partner P-103: Missing travel-time information**

- Partner-to-restaurant travel time: 5 minutes
- Restaurant-to-customer travel time: Missing
- Expected behaviour: The partner should be marked ineligible because the complete travel information is unavailable.

**Actual result:**

The service returned:

- Order ID: O-100
- Partner ID: None
- ETA: None
- Reason: no eligible partner or missing time data

No delivery partner was assigned because none of the three candidates satisfied the eligibility requirements.

## 3. Three edge cases

### Case 1: Invalid partner workload

**Input:**
- Partner workload: Infinity
- Valid order details and travel times.

**Expected behaviour:**

The service should reject the workload value and mark the partner as ineligible. The ETA should be None.

**Actual observed result:**

The partner was marked ineligible and no ETA was calculated.

**Test:** `test_invalid_partner_workload_makes_eta_ineligible`

### Case 2: Non-finite current time

**Input:**
- Current time: NaN
- Valid order details, partner information and travel times.

**Expected behaviour:**

The service should reject the invalid current-time value instead of calculating an incorrect ETA.

**Actual observed result:**

The partner was marked ineligible and the ETA was None.

**Test:** `test_non_finite_current_time_makes_eta_ineligible`

### Case 3: Duplicate cancellation ID

**Input:**
- Active orders: O-1 and O-2
- Workload: 19 minutes
- Processed cancellation IDs: C-1
- A new cancellation request uses the same ID C-1 for order O-2.

**Expected behaviour:**

The service should recognize that cancellation ID C-1 has already been processed. It should not remove O-2 or reduce the workload again.

**Actual observed result:**

Both active orders remained unchanged, workload stayed at 19 minutes, and the processed cancellation list remained unchanged.

**Test:** `test_duplicate_cancellation_id_does_not_cancel_a_different_order`

## 4. Assumptions and limitations

### Tie-breaking

The service first selects the eligible delivery partner with the lowest estimated ETA. If two or more partners have the same ETA, it selects the partner with the lexicographically smaller partner ID. This makes the selection consistent regardless of the input partner order.

### Workload accounting

The remaining workload of a partner is added to the travel time when calculating pickup time. During cancellation, the corresponding order workload is removed from the partner's total workload. The workload is prevented from becoming negative.

### Cancellation idempotency

Each cancellation ID is recorded after processing. If the same cancellation ID is received again, the service ignores it. This prevents duplicate cancellation events from changing active orders or workload multiple times.

### Remaining limitations

The service depends on the availability and correctness of travel-time information. If required travel data is missing or invalid, the partner is marked ineligible.

The current implementation uses the provided travel-time data and does not independently retrieve live traffic information.

The complete test suite was executed using:

`python -m pytest -q`

**Final observed result: 241 passed in 0.26s.**

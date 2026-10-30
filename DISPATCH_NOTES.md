

# DISPATCH_NOTES.md — Required Submission

## 1. Worked ETA example

Consider the following order and delivery partner:

* Current time (`now`) = 0 minutes
* Partner-to-restaurant travel time = 5 minutes
* Remaining partner workload = 10 minutes
* Restaurant preparation time = 15 minutes
* Restaurant-to-customer travel time = 12 minutes

**ETA Calculation:**

Pickup time = Current time + Travel time to restaurant + Remaining workload

Pickup time = 0 + 5 + 10 = 15 minutes

Delivery ETA = Pickup time + Preparation time + Travel time to customer

Delivery ETA = 15 + 15 + 12 = **42 minutes**

Therefore, the estimated delivery time is **42 minutes**.

## 2. No-eligible-partner example

Consider an order with three available delivery partners:

* **P1:** Inactive, so this partner is not eligible.
* **P2:** Has reached the maximum capacity, so this partner cannot accept another order.
* **P3:** Required travel-time information is missing, so a valid ETA cannot be calculated.

Since all three partners are ineligible, the system leaves the order unassigned.

**Important:** Missing travel-time information is not treated as zero. A partner with missing required route information is excluded from ETA calculation.

## 3. Five edge cases

### Edge Case 1: Missing travel-time information

* **Input:** A partner has no travel-time entry for a required route.
* **Expected behaviour:** The partner should be excluded from ETA calculation because a valid ETA cannot be calculated.
* **Actual observed result:** The full test suite passed (229 tests).
* **Test evidence:** Full pytest suite (229 tests passed); individual test mapping not confirmed.

### Edge Case 2: Inactive delivery partner

* **Input:** A delivery partner has `active = False`.
* **Expected behaviour:** The inactive partner should not be assigned a new order.
* **Actual observed result:** The full test suite passed (229 tests).
* **Test evidence:** Full pytest suite (229 tests passed); individual test mapping not confirmed.

### Edge Case 3: Partner has reached maximum capacity

* **Input:** A partner has 2 active orders and a maximum capacity of 2.
* **Expected behaviour:** The partner should not receive another order.
* **Actual observed result:** The full test suite passed (229 tests).
* **Test evidence:** Full pytest suite (229 tests passed); individual test mapping not confirmed.

### Edge Case 4: Two partners have equal ETA

* **Input:** Two eligible partners have the same estimated delivery time.
* **Expected behaviour:** The partner with the lexicographically smaller partner ID should be selected.
* **Actual observed result:** The full test suite passed (229 tests).
* **Test evidence:** Full pytest suite (229 tests passed); individual test mapping not confirmed.

### Edge Case 5: Duplicate cancellation event

* **Input:** The same cancellation event is processed twice for the same partner and order.
* **Expected behaviour:** The cancellation should be processed only once. Workload should not be reduced twice.
* **Actual observed result:** The full test suite passed (229 tests).
* **Test evidence:** Full pytest suite (229 tests passed); individual test mapping not confirmed.

## 4. Assumptions and limitations

1. **Tie-breaking:** If two partners have the same ETA, the partner ID is compared in ascending lexicographical order.
2. **Workload accounting:** The remaining workload of a partner is included when calculating pickup time.
3. **Cancellation idempotency:** A duplicate cancellation event is ignored so that workload and capacity are not updated more than once.
4. **Missing travel data:** If required travel-time information is missing, the partner is excluded from that assignment's ETA calculation.
5. **Partner eligibility:** Only active partners with available capacity and valid travel-time information are considered for assignment.

**Limitations:** A valid ETA cannot be calculated when required travel-time information is unavailable.
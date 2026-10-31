# DISPATCH_NOTES.md

## 1. Worked ETA example

To understand how the ETA calculation works, I used the supplied demo example for order `O-7`.

The order is assigned to delivery partner `P-2`.

**Order details:**

- Order ID: O-7
- Restaurant ID: R-2
- Destination zone: Z-9
- Current simulated time: 0 minutes
- Restaurant preparation time: 10 minutes

**Delivery partner details:**

- Partner ID: P-2
- Partner-to-restaurant travel time: 8 minutes
- Remaining workload: 5 minutes
- Restaurant-to-customer travel time: 12 minutes

**Step 1: Calculate pickup time**

According to the required formula:

Pickup Time = Current Time + Partner-to-Restaurant Travel Time + Remaining Workload

= 0 + 8 + 5

= **13 minutes**

**Step 2: Calculate final ETA**

ETA = Pickup Time + Restaurant Preparation Time + Restaurant-to-Customer Travel Time

= 13 + 10 + 12

= **35 minutes**

**Actual result observed:**

When I ran the supplied application demo using `python -m main`, it assigned order `O-7` to partner `P-2`.

The output showed:

```text
{
    'order_id': 'O-7',
    'partner_id': 'P-2',
    'pickup_minutes': 13,
    'eta_minutes': 35,
    'reason': 'assigned'
}
```

This confirmed that the existing ETA calculation works correctly for this supplied example.

## 2. No-eligible-partner example

Consider a new order `O-8` that needs to be delivered from restaurant `R-2` to destination zone `Z-9`.

Suppose two delivery partners are available in the system.

**Partner P-1:**

- Active: True
- Capacity: 3 orders
- Current active orders: 3

This partner is not eligible because they have already reached their maximum order capacity.

**Partner P-2:**

- Active: True
- Capacity: 3 orders
- Current active orders: 0

This partner has available capacity, but the required travel-time information from their zone to restaurant `R-2` is missing.

Since the ETA cannot be calculated reliably, this candidate must also be excluded.

**Expected service result:**

```python
{
    'order_id': 'O-8',
    'partner_id': None,
    'eta_minutes': None,
    'reason': 'no eligible partner or missing/invalid time data'
}
```

The order remains unassigned because neither candidate satisfies all the required conditions.

This example illustrates why SmartDispatch must check both partner eligibility and the availability of reliable travel information before making an assignment.

Note: This is a constructed example based on the implemented logic. It should be run locally before being described as an independently observed test result.

## 3. Three edge cases

### 1. Invalid partner workload

**Input:**

A delivery partner has an invalid workload value, such as:

- `-1`
- `True`
- `NaN`
- `Infinity`

**Expected behaviour:**

The partner should not receive a reliable ETA because their workload information is invalid.

**Actual result:**

The `is_valid_time()` helper rejects negative, Boolean and non-finite values. The regression test checks that the resulting ETA is ineligible and `eta_minutes` is `None`.

**Test name:**

`test_invalid_partner_workload_makes_eta_ineligible`

**Verification:** The regression test has been added. Its final passing result should be recorded after running the latest local test suite.

### 2. Non-finite current time

**Input:**

The ETA function receives a current-time value of:

- `NaN`
- `Infinity`
- `-Infinity`

**Expected behaviour:**

The input should be rejected because the current simulated time must be a valid finite, non-negative number.

**Actual result:**

The current-time validation uses the existing `is_valid_time()` helper, which rejects these values before performing the ETA calculation.

**Test name:**

`test_non_finite_current_time_makes_eta_ineligible`

**Verification:** A regression test has been added to check all three values. Its final passing result is pending local verification.

### 3. Duplicate cancellation ID

**Input:**

A partner has two active orders, `O-1` and `O-2`.

The cancellation event ID `C-1` has already been processed for `O-1`. The same event ID is then received again for `O-2`.

**Expected behaviour:**

The duplicate event should be ignored. Neither active order nor the partner's workload should change again.

**Actual result:**

The cancellation logic checks `processed_cancellation_ids` before applying another update. An already processed event returns the copied partner record without releasing additional workload.

**Test name:**

`test_duplicate_cancellation_id_does_not_cancel_a_different_order`

**Verification:** The regression test has been added and checks that both orders remain active and the workload remains unchanged. Its final passing result is pending local verification.

## 4. Assumptions and limitations

While implementing SmartDispatch, I followed a few important assumptions based on the problem statement and the existing data model.

**Tie-breaking:**

When multiple eligible partners have the same ETA, the system selects the partner with the lowest ID using ascending lexicographic order.

This makes the assignment deterministic and ensures that the same inputs produce the same result.

**Workload accounting:**

The partner's remaining workload is added to the partner-to-restaurant travel time while calculating pickup time.

For cancellations, the implementation uses `minutes_by_order` to determine how much workload should be released for the cancelled order. The resulting workload is prevented from becoming negative.

The current implementation also defaults missing partner workload to zero. This assumption should be consistent with the project's data contract.

**Cancellation idempotency:**

The system maintains a list called `processed_cancellation_ids`.

Before processing a cancellation, it checks whether the event ID has already been recorded. If it has, the function returns without applying the cancellation again.

This prevents duplicate events from releasing workload or capacity more than once.

**Limitations and further improvements:**

- Travel-time information is supplied through offline synthetic data; there is no live GPS or external routing integration.
- The implementation depends on the accuracy and consistency of the supplied partner and travel records.
- More regression coverage is needed for malformed records, unknown identifiers and additional cancellation scenarios.
- Performance benchmarking has not been performed, so no measurable speed improvement is claimed.

Overall, my main priority was to make the assignment engine reliable and predictable while keeping the implementation understandable and maintainable.
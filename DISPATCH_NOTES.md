# DISPATCH_NOTES.md

## 1. Worked ETA example

I used the sample order `O-7` to check how the ETA calculation works.

**Order details:**
- Order ID: `O-7`
- Restaurant ID: `R-2`
- Destination zone: `Z-9`
- Current time: 0 minutes
- Preparation time: 10 minutes

**Candidate partner: P-2**
- Partner-to-restaurant travel time: 8 minutes
- Remaining workload: 5 minutes
- Restaurant-to-customer travel time: 12 minutes

**ETA calculation:**

Pickup time = Current time + Travel time + Remaining workload

`0 + 8 + 5 = 13 minutes`

ETA = Pickup time + Preparation time + Restaurant-to-customer travel time

`13 + 10 + 12 = 35 minutes`

The other candidate, P-1, has an ETA of 36 minutes.

**Actual result:**

The program selected P-2 with a pickup time of 13 minutes and an ETA of 35 minutes.

The output from `python -m main` was:

`{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

## 2. No-eligible-partner example

Suppose an order requires travel from zone `Z-1` to restaurant `R-2`, and then from `R-2` to destination `Z-9`.

There are two candidate partners:

- **P-1:** The partner is inactive, so it is skipped.
- **P-2:** The partner is active and has available capacity, but the required travel-time entry from `R-2` to `Z-9` is missing.

Neither partner can be assigned:
- P-1 cannot be considered because it is inactive.
- P-2 cannot receive a reliable ETA because part of the travel data is missing.

**Expected and observed behaviour:**

The service leaves the order unassigned and returns a result with `partner_id` and `eta_minutes` set to `None`, along with the reason:

`no eligible partner or missing time data`

Missing travel time is not treated as zero.

## 3. Three edge cases

### 1. Duplicate cancellation event

**Input:**

A partner has:
- Active orders: `['O1']`
- Workload: 9 minutes
- Workload for O1: 9 minutes
- Cancellation event ID: `C1`

The same cancellation event is processed twice.

**Expected behaviour:**

The workload should be reduced only once. The second cancellation should not change it again.

**Actual observed result:**

The earlier tested implementation left the workload at 0 and stored `C1` only once.

**Test:** `test_duplicate_cancellation_is_idempotent` in `test_contract.py`.

### 2. Missing travel-time data

**Input:**

An order requires travel from zone `Z` to restaurant `R`, and then to destination `D`. The travel-time dictionary is empty.

**Expected behaviour:**

The partner should not receive an ETA because the required travel information is missing.

**Actual observed result:**

The ETA is `None` and the partner is marked as ineligible.

**Test:** `test_missing_travel_is_not_zero` in `test_contract.py`.

### 3. Partner has reached capacity

**Input:**

A partner has a capacity of 1 and already has one active order.

**Expected behaviour:**

The partner should be skipped because they cannot accept another order.

**Actual observed result:**

The order remains unassigned when this is the only candidate.

**Test:** `test_full_partner_not_assigned` in `test_contract.py`.

## 4. Assumptions and limitations

- **Tie-breaking:** If two partners have the same ETA, the partner ID is used to choose the one that comes first alphabetically. This keeps the result consistent even if the input partner order changes.
- **Workload accounting:** Existing workload is added to the partner's travel time when calculating pickup time. When an order is cancelled, its recorded workload is subtracted.
- **Cancellation idempotency:** Each cancellation event ID should be processed only once. Repeated events with the same ID should not reduce workload again.
- **Limitations:** The service depends on the travel-time dictionary containing the required route information. If a route is missing, that partner cannot be given a reliable ETA.
- **Testing note:** An earlier version of my fixes passed all 229 tests. I shortened the implementation afterwards, so I still need to run the full test suite on that final version to confirm the same result.

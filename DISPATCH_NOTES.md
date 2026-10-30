# DISPATCH_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked ETA example
Show an order, the candidate partner, partner-to-restaurant travel time, remaining workload, restaurant preparation time, restaurant-to-customer travel time, the ETA calculation, and the actual result.

* **Order**: `order_id="O-7"`, `restaurant_id="R-2"`, `destination_zone="Z-9"`, `prep_minutes=10`
* **Candidate Partner**: `partner_id="P-2"`, `zone="Z-1"`, `active=True`, `capacity=2`, `active_order_ids=['OLD-1']`, `workload_minutes=5`
* **Travel Matrix**:
  * Leg 1 (`Z-1` $\rightarrow$ `R-2`): `8` minutes
  * Leg 2 (`R-2` $\rightarrow$ `Z-9`): `12` minutes
* **Current Time (`now`)**: `0`
* **Calculation Breakdown**:
  * $\text{pickup\_minutes} = \text{now} + \text{leg1} + \text{workload} = 0 + 8 + 5 = 13$
  * $\text{eta\_minutes} = \text{pickup\_minutes} + \text{prep\_minutes} + \text{leg2} = 13 + 10 + 12 = 35$
* **Actual Result**:
  ```python
  {
      'order_id': 'O-7',
      'partner_id': 'P-2',
      'pickup_minutes': 13,
      'eta_minutes': 35,
      'reason': 'assigned'
  }
  ```

---

## 2. No-eligible-partner example
Show why each candidate is ineligible (for example, capacity reached or required travel-time data missing) and how the service reports the order as unassigned.

* **Order**: `order_id="O-10"`, `restaurant_id="R-1"`, `destination_zone="Z-2"`, `prep_minutes=15`
* **Candidate Partners Evaluated**:
  1. **Partner P-A** (`zone="Z-1"`, `active=False`): Ineligible because partner is not active (`partner['active'] is not True`).
  2. **Partner P-B** (`zone="Z-1"`, `active=True`, `capacity=1`, `active_order_ids=['O-PREV']`): Ineligible because current active orders ($1$) equal capacity ($1$), leaving zero available capacity.
  3. **Partner P-C** (`zone="Z-3"`, `active=True`, `capacity=2`, `active_order_ids=[]`): Ineligible because leg 1 route `("Z-3", "R-1")` is missing from the travel matrix.
* **Actual Result**:
  ```python
  {
      'order_id': 'O-10',
      'partner_id': None,
      'eta_minutes': None,
      'reason': 'no eligible partner or missing time data'
  }
  ```
* **Candidate Diagnostic Explanation (`explain_candidates`)**:
  ```python
  {
      'P-A': {'eligible': False, 'reason': 'partner is inactive', 'eta_minutes': None, 'is_selected': False},
      'P-B': {'eligible': False, 'reason': 'capacity reached (1/1)', 'eta_minutes': None, 'is_selected': False},
      'P-C': {'eligible': False, 'reason': 'missing or invalid travel route (Z-3 -> R-1)', 'eta_minutes': None, 'is_selected': False}
  }
  ```

---

## 3. Three edge cases
For each, state input, expected behaviour, actual observed result, and test that verifies it.

### Case 1: Incomplete or Missing Route in Travel Matrix
* **Input**: Order `("O", "R", "D")`, Partner `("P", "Z")`, Travel `{}` (empty map).
* **Expected Behaviour**: Missing routes must never default to 0; partner cannot receive a reliable ETA and must be marked ineligible.
* **Actual Result**: `{'partner_id': 'P', 'eta_minutes': None, 'eligible': False}`.
* **Verifying Test**: `test_contract.py::test_missing_travel_is_not_zero`, `test_edge_cases.py::test_eta_is_ineligible_when_either_required_route_is_missing`.

### Case 2: Duplicate Cancellation Event Replay
* **Input**: Partner `P` with `active_order_ids=['O1']`, `workload_minutes=9`, `minutes_by_order={'O1':9}`. Cancellation event `'C1'` executed twice in succession.
* **Expected Behaviour**: The cancellation must be strictly idempotent. The first event releases workload and removes order; the duplicate event is ignored without decrementing workload or recording duplicate IDs.
* **Actual Result**: `workload_minutes == 0`, `active_order_ids == []`, `processed_cancellation_ids == ['C1']`.
* **Verifying Test**: `test_contract.py::test_duplicate_cancellation_is_idempotent`, `test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads`.

### Case 3: Boolean and Non-Numeric Type Rejection
* **Input**: `now = True` or `leg1 = True` or `prep_minutes = "10"`.
* **Expected Behaviour**: Because in Python `isinstance(True, int)` is `True`, booleans must be explicitly rejected so `True` is not treated as $1$ minute. Non-numeric types (strings, `NaN`, `inf`, `None`) must also be rejected.
* **Actual Result**: `eligible == False` and `eta_minutes is None`.
* **Verifying Test**: `test_acceptance_matrix.py::test_current_time_validation[True]`, `test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[True-1]`.

---

## 4. Assumptions and limitations
Document tie-breaking, workload accounting, cancellation idempotency, and any unresolved issue.

* **Tie-Breaking**: When multiple eligible candidates yield identical `eta_minutes`, ties are resolved deterministically using ascending lexicographical order of `partner_id` (`min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))`).
* **Workload Accounting**: Workload is additive and represents remaining delivery time from previous orders. In cancellations, workload reduction uses `max(0, current_workload - order_minutes)` to ensure workload never becomes negative.
* **Cancellation Idempotency**: Cancellation deduplication depends on unique event IDs recorded in `processed_cancellation_ids`. An event already in the list is immediately returned as a no-op.
* **In-Memory Concurrency & Persistence**: Current operations are performed in memory on dictionary structures. Production deployment would require database locking or transactional semantics to guard against concurrent assignment race conditions.

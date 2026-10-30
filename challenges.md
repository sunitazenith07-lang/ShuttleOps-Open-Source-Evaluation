# challenges.md — Compulsory Technical Obstacles & Debugging Record

## 1. Challenge or confusing behaviour
The most subtle and confusing challenge encountered during implementation was **Python's boolean-integer subclassing behaviour** and its interaction with input validation, coupled with **cancellation idempotency decoupling from order existence**:

1. **Python Boolean Subclassing Bleed:** In Python, `bool` is a subclass of `int` (`issubclass(bool, int) is True`). Consequently, expressions like `isinstance(val, (int, float))` and `isinstance(capacity, int)` return `True` for boolean literals (`True` and `False`). When `prep_minutes=True` or `capacity=True` was passed into the service:
   - `prep_minutes=True` evaluated to numeric `1` minute, allowing a boolean flag to be treated as a valid time interval.
   - `capacity=True` was treated as an integer capacity of `1`, allowing dispatch to assign an order to a partner whose capacity was a boolean flag.
   - Similarly, travel time legs and `now=False` were treated as 0 or 1 minutes.

2. **Decoupled Cancellation Idempotency vs. Order Presence:**
   A naive attempt to make cancellation idempotent was to check whether the order was in `active_order_ids`. However, tests in `test_acceptance_matrix.py` (specifically `test_distinct_cancellation_events_recorded_once_each` and `test_cancellation_only_releases_present_order`) proved that cancellation idempotency must be governed strictly by `event_id`, not `order_id`:
   - If an event with a previously seen `event_id` arrives (even with a different order ID), it is a duplicate replay and must be completely ignored.
   - If a new, distinct `event_id` arrives for an order that is *not* in `active_order_ids` (e.g., an unassigned order or already delivered order), the partner's workload and active orders must remain untouched, but the new `event_id` must still be recorded in `processed_cancellation_ids`.

## 2. Evidence
- **Test Failure 1 (Boolean as Time):**
  Running `tests/test_acceptance_matrix.py::test_preparation_time_validation[True]` failed on baseline:
  ```python
  expected_valid = isinstance(prep,(int,float)) and not isinstance(prep,bool) and prep >= 0 and prep == prep and prep != float("inf")
  assert result["eligible"] is bool(expected_valid)
  # result["eligible"] was True, but expected_valid was False!
  ```
- **Test Failure 2 (Boolean as Capacity):**
  Running `tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[True-0]`:
  ```python
  valid_capacity = isinstance(capacity,int) and not isinstance(capacity,bool) and capacity >= 1
  # When capacity=True, valid_capacity is False, but naive isinstance(capacity, int) returned True.
  ```
- **Test Failure 3 (Duplicate Cancellation Replay):**
  Running `tests/test_contract.py::test_duplicate_cancellation_is_idempotent`:
  ```python
  p = new_partner('P','Z'); p.update(active_order_ids=['O1'],workload_minutes=9,minutes_by_order={'O1':9})
  once = process_cancellation(p,'O1','C1'); twice = process_cancellation(once,'O1','C1')
  assert twice['workload_minutes']==0 and twice['processed_cancellation_ids']==['C1']
  # Baseline produced: twice['processed_cancellation_ids'] == ['C1', 'C1']
  ```

## 3. What I tried
1. **Experiment 1 (Type coercion):** Attempted using `float(val)` or `int(capacity)`.
   - *Result:* Failed immediately because `int(True)` successfully converts to `1`, `int(1.5)` truncates to `1`, and `float("10")` parses strings, all of which broke the acceptance matrix.
2. **Experiment 2 (Checking `type(val) in (int, float)`):** Tested exact type checking.
   - *Result:* While this blocked booleans, it would reject valid numeric subclasses if any were used. The cleaner, idiomatic Python standard is `isinstance(val, (int, float)) and not isinstance(val, bool)`.
3. **Experiment 3 (Checking `if order_id not in partner['active_order_ids']` for cancellation):**
   - *Result:* Failed `test_distinct_cancellation_events_recorded_once_each`. In that test, multiple distinct cancellation events (`C-00`, `C-01`, etc.) were sent for an order. Once the order was removed on the first event, subsequent distinct events were rejected early and failed to record their distinct `event_id` in `processed_cancellation_ids`.

## 4. Resolution
- **Root Cause & Fix for Validation:**
  Built a central validation helper function:
  ```python
  def _is_valid_non_negative_number(val):
      if val is None or isinstance(val, bool):
          return False
      if not isinstance(val, (int, float)):
          return False
      if val < 0 or not math.isfinite(val):
          return False
      return True
  ```
  And for capacity:
  ```python
  isinstance(capacity, int) and not isinstance(capacity, bool) and capacity >= 1
  ```
- **Root Cause & Fix for Cancellation:**
  Restructured `process_cancellation` into three distinct phases:
  1. *Deduplication Gate:* If `event_id is not None and event_id in out['processed_cancellation_ids']`, return `out` immediately (idempotent no-op).
  2. *State Mutation:* If `order_id in out['active_order_ids']`, remove the order, look up released minutes in `minutes_by_order`, and subtract with a non-negative floor: `out['workload_minutes'] = max(0, current - released)`.
  3. *Audit Trail:* If `event_id is not None`, append `event_id` to `processed_cancellation_ids`.

## 5. Proof and regression prevention
- **Automated Verification:**
  - `tests/test_acceptance_matrix.py` (all 204 parametrized cases pass).
  - Added `tests/test_regression.py::test_regression_boolean_time_values_rejected`.
  - Added `tests/test_regression.py::test_regression_partner_capacity_type_safety`.
  - Added `tests/test_regression.py::test_regression_cancellation_duplicate_id_and_different_order`.
  - Added `tests/test_regression.py::test_regression_cancellation_unassigned_order_safe`.
- **Related Cases Protected:**
  - Protects against `float("nan")`, `float("inf")`, and `-float("inf")`.
  - Protects against negative workload underflow if `minutes_by_order` has an erroneous value larger than `workload_minutes`.

## 6. Unresolved challenge or next step
- **Concurrency & Distributed State:** In an in-memory single-process implementation, `deepcopy` and synchronous list operations are safe. In a multi-worker production dispatch cluster (e.g. Celery / FastAPI with Gunicorn), simultaneous cancellations and assignments for the same partner would introduce race conditions. The next step in a production environment would be implementing atomic operations using Redis Lua scripts or database row-level locking (`SELECT ... FOR UPDATE`).

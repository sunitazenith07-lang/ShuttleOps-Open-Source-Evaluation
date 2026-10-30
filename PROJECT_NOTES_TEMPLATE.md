# Project Notes

## Requirements completed

During this challenge, I completed all core requirements outlined in the problem statement:

1. **Input & Order Validation**:
   - Validated that `order_id`, `restaurant_id`, and `destination_zone` are non-empty strings.
   - Validated that preparation time (`prep_minutes`) and current time (`now`) are non-negative, finite numbers (not booleans, strings, NaN, or infinity).
2. **Partner Eligibility & Capacity Rules**:
   - Filtered out inactive partners (`active` must be strictly `True`, rejecting `False`, `0`, `None`, and `"yes"`).
   - Validated capacity as a positive integer ($\ge 1$).
   - Prevented assignment to partners whose current active orders have reached or exceeded capacity (`len(active_order_ids) >= capacity`).
3. **Route Lookup & ETA Calculation**:
   - Enforced that both travel legs (partner-to-restaurant and restaurant-to-customer) must exist in the travel table. Missing data is never treated as zero.
   - Implemented the required formula:
     - `pickup_minutes = now + leg1 + workload_minutes`
     - `eta_minutes = pickup_minutes + prep_minutes + leg2`
4. **Deterministic Tie-Breaking**:
   - When multiple eligible partners have the same minimum ETA, ties are deterministically broken by choosing the lexicographically smaller `partner_id` (alphabetical order).
5. **Cancellation Idempotency**:
   - Handled duplicate cancellation events safely. If an `event_id` was already processed, the cancellation is ignored so partner workload and capacity are not released a second time.

---

## Files changed

- **`service.py`**:
  - Added four helper functions: `_is_valid_numeric()`, `_is_valid_travel_time()`, `_is_valid_order()`, and `_is_eligible_partner()`.
  - Updated `estimate_eta()` with input checks for `now`, `prep_minutes`, and travel leg validity.
  - Updated `assign_order()` with order validation and partner eligibility filtering.
  - Updated `process_cancellation()` with an idempotency guard using `processed_cancellation_ids`.
- **`tests/test_regressions.py`**:
  - Created a new test file containing 71 regression tests across 10 test classes to protect against each identified bug.
- **Documentation**:
  - Filled out `approach.md`, `challenges.md`, `optimizations.md`, `TESTING.md`, `DISPATCH_NOTES.md`, `ARCHITECTURE_TEMPLATE.md`, `AI_USAGE_TEMPLATE.md`, and `CONTRIBUTING.md`.

---

## Decisions and assumptions

- **Boolean Type Handling**: In Python, `isinstance(True, int)` returns `True`. Because of this, I made sure all numeric validation explicitly checks `isinstance(value, bool)` first and rejects it. A travel time of `True` is invalid, not 1 minute.
- **Dispatch-Time Validation**: I kept validation inside `service.py` functions rather than modifying the factory functions in `models.py`. This ensures that even if test fixtures modify partner dictionaries directly after creation, our dispatch logic remains safe.
- **Lexicographic Tie-Breaking**: Used Python's standard `min()` with a tuple key `(item['eta_minutes'], str(item['partner_id']))`. This makes selection 100% deterministic and independent of input list ordering.
- **Cancellation Clamping**: When subtracting an order's minutes from `workload_minutes`, I used `max(0, ...)` so workload never accidentally becomes negative.

---

## Tests and results

- **Initial Baseline Run**:
  - Command: `python -m pytest -q`
  - Result: **65 failed, 164 passed** (out of 229 starter tests).
- **Final Run (After Fixes & Regressions)**:
  - Command: `python -m pytest -q`
  - Result: **300 passed in 0.19s** (229 original tests + 71 new regression tests, 0 failures).
- **Offline Demo**:
  - Command: `python -m main`
  - Output: `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}` (matches expected worked calculation).

---

## Limitations and next steps

- **Workload Validation**: Currently, the initial `workload_minutes` value on a partner dictionary is trusted as-is from the data source. In the future, I would add validation to reject negative workloads.
- **Missing Minutes in Cancellation**: If a cancelled order is not listed in `minutes_by_order`, the workload reduction defaults to 0 minutes via `.get(order_id, 0)`.
- **Batch Assignment**: The current engine assigns one order at a time. A logical next step for production would be adding batch dispatch to handle high order volume during peak delivery hours.

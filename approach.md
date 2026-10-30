# approach.md — Implementation Approach & Engineering Decisions

## 1. Baseline
- **Commands run before editing:**
  - `python -m pip install -r requirements-dev.txt`
  - `python -m pytest -q`
  - `python -m main`
- **Initial test result (actual summary):**
  - `65 failed, 164 passed, 1 warning in 1.18s` (Total: 229 tests)
  - Failing test groups on starter code:
    - `test_invalid_or_missing_travel_time_rejected`: TypeError on string values (`'int' and 'str'`), assertion failures on negative travel times and boolean values (`True`/`False`).
    - `test_preparation_time_validation`: negative, NaN, infinite, string, and boolean prep times were not rejected.
    - `test_inactive_partners_never_selected`: inactive partners (`active=False`, `0`, `None`, `"no"`) were selected because `assign_order` had no active status check.
    - `test_capacity_boundary_matrix`: capacity boundaries (`len(active_order_ids) >= capacity`) and invalid capacity types (0, -1, float 1.5, bool `True`, None) were ignored.
    - `test_duplicate_cancellation_is_idempotent_across_workloads`: duplicate cancellation events appended the `event_id` repeatedly and failed idempotency checks.
    - `test_current_time_validation`: negative or invalid `now` values were accepted.
    - `test_invalid_order_fields_do_not_assign_partner`: malformed/empty order IDs, restaurant IDs, and destination zones were assigned partners instead of being rejected.
- **Demo / output observed on baseline:**
  ```python
  {'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
  ```

## 2. Codebase understanding
- **Important files and functions inspected:**
  - `service.py`: Contains core business logic (`estimate_eta`, `assign_order`, `process_cancellation`).
  - `models.py`: Data factories `new_partner` and `new_order`.
  - `fixtures.py` & `main.py`: Sample inputs and offline demo entry point.
  - `tests/test_contract.py`: Fundamental contract test cases (ETA calculation formula, tie-breaking, inactive partner, idempotency).
  - `tests/test_acceptance_matrix.py`: Comprehensive parameterized matrix verifying boundary conditions across time, capacity, routes, and cancellations.
  - `tests/test_edge_cases.py`: Boundary tests for ETA formulas with large numbers, zero values, and missing routes.
  - `data/records.json`: Synthetic dataset with 180 orders, 60 partners, 387 travel times, 177 cancellation events, and 10 cataloged edge cases.
- **Candidate filtering, ETA calculation, and capacity flow traced:**
  - In `assign_order`, each partner in `partners` is evaluated. In the starter code, no capacity or active checks were performed; it simply called `estimate_eta`.
  - In `estimate_eta`, leg1 was retrieved via `(partner['zone'], order['restaurant_id'])` and leg2 via `(order['restaurant_id'], order['destination_zone'])`. Missing routes returned `eligible: False`, but invalid types (strings, negatives, booleans) caused TypeErrors or incorrect arithmetic.
  - Pickup time formula: `pickup = now + leg1 + workload_minutes`.
  - Delivery ETA formula: `eta = pickup + prep_minutes + leg2`.
  - Tie-breaking: `min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))`.
- **How understanding was confirmed:**
  - Traced stack traces from the 65 pytest failures.
  - Cross-referenced expected behaviors in `STUDENT_PROBLEM_STATEMENT.md` with assertions in `test_acceptance_matrix.py`.

## 3. Investigation and implementation strategy

### Issue 1: Missing Input Validation & Boolean Type Bleed
- **Symptom:** `TypeError: unsupported operand type(s) for +: 'int' and 'str'` when travel times or prep minutes were strings. Furthermore, passing `True` or `False` for `prep_minutes`, `now`, or travel times was treated as numeric 1 or 0 because `bool` is a subclass of `int` in Python (`isinstance(True, int) == True`).
- **Hypothesis:** Type checking must explicitly exclude booleans, ensure numeric types (`int`, `float`), verify finite values (rejecting `NaN` and `inf`), and enforce non-negativity (`>= 0`).
- **Evidence:** `test_invalid_or_missing_travel_time_rejected[2-1]` raised `TypeError`, and `test_preparation_time_validation[True]` failed assertion.
- **Fix chosen:** Created `_is_valid_non_negative_number(val)` checking `val is not None and not isinstance(val, bool) and isinstance(val, (int, float)) and math.isfinite(val) and val >= 0`. Created `_is_valid_identifier(val)` to ensure IDs/zones are non-empty strings.

### Issue 2: Partner Inactivity and Capacity Boundary Bypass
- **Symptom:** Inactive partners and partners with `len(active_order_ids) >= capacity` were assigned orders.
- **Hypothesis:** Before estimating ETA for a candidate, verify partner active status (`partner.get('active') is True`) and validate capacity: `capacity` must be an integer >= 1 (excluding boolean `True` or floats like `1.5`), and `len(active_order_ids) < capacity`.
- **Evidence:** `test_inactive_partners_never_selected[False0]` and `test_capacity_boundary_matrix[1-1]` failed with partner assigned instead of `None`.
- **Fix chosen:** Implemented `_is_eligible_partner(partner)` which validates active state, integer capacity, current load against capacity, non-negative workload, and zone identifier.

### Issue 3: Cancellation Event Non-Idempotency & Underflow Risk
- **Symptom:** `test_duplicate_cancellation_is_idempotent` produced `twice['processed_cancellation_ids'] == ['C1', 'C1']` instead of `['C1']`.
- **Hypothesis:** `process_cancellation` appended `event_id` unconditionally without checking if `event_id` was already present in `processed_cancellation_ids`. Also, if an order is cancelled whose minutes exceed partner workload, workload could become negative if not clamped.
- **Evidence:** `test_duplicate_cancellation_is_idempotent_across_workloads` failed on all 15 workload parameterized cases.
- **Fix chosen:**
  1. If `event_id is not None and event_id in out['processed_cancellation_ids']`, return `out` immediately.
  2. If `order_id in out['active_order_ids']`, remove the order, look up minutes in `minutes_by_order`, and update `workload_minutes = max(0, current_workload - released)`.
  3. Append `event_id` to `processed_cancellation_ids` if not already present.

## 4. Implementation decisions
- **Main changes and why:**
  - Extracted validation functions (`_is_valid_non_negative_number`, `_is_valid_identifier`, `_is_eligible_partner`, `_is_valid_order`) to ensure uniform validation across both `estimate_eta` and `assign_order`.
  - Kept dictionary structures immutable from the caller's perspective by returning new/copied dicts.
  - Implemented the optional stretch feature `explain_candidates` to provide actionable transparency into why candidates were rejected or selected.
- **Alternatives considered and why rejected:**
  - *Alternative: Raising exceptions for invalid inputs.* Rejected because the test suite contract and problem statement expect deterministic dictionary responses with `eligible: False` or `partner_id: None` and `reason` explanations, rather than unhandled exceptions.
  - *Alternative: Mutating the assigned partner's state inside `assign_order`.* Rejected because `assign_order` is an assignment evaluation query; mutating partner state in-place would violate existing test expectations and cause test isolation issues.
- **Assumptions:**
  - Time units are non-negative minutes and can be integer or float (e.g. 1.5).
  - An order requires valid string identifiers for `order_id`, `restaurant_id`, and `destination_zone`.
  - Ties in ETA are broken lexicographically by string representation of `partner_id`.

## 5. Verification
- **Tests added or changed:**
  - Added `tests/test_regression.py` with 9 comprehensive test functions:
    1. `test_regression_boolean_time_values_rejected`: Verifies boolean values in prep/now/legs are rejected.
    2. `test_regression_partner_capacity_type_safety`: Verifies non-integer/boolean/negative capacity handling.
    3. `test_regression_cancellation_duplicate_id_and_different_order`: Verifies replay attack prevention.
    4. `test_regression_cancellation_unassigned_order_safe`: Verifies cancellation of unassigned orders leaves workload unchanged.
    5. `test_regression_cancellation_workload_clamped_to_zero`: Verifies non-negative workload floor.
    6. `test_regression_empty_and_whitespace_ids_rejected`: Verifies whitespace ID rejection.
    7. `test_regression_stable_tie_breaking_multiple_partners`: Verifies stable lexicographical tie-breaking.
    8. `test_regression_synthetic_dataset_batch_dispatch`: End-to-end integration test iterating over `data/records.json`.
    9. `test_regression_explain_candidates`: Tests the candidate explanation feature.
- **Commands run and actual results:**
  - `python -m pytest -q` -> `238 passed, 1 warning in 0.44s`
  - `python -m main` -> `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`
- **Edge cases verified:**
  - Negative and zero travel times.
  - Non-numeric and boolean types for prep/travel/now.
  - Active orders count equal to capacity (`len(active_order_ids) == capacity`).
  - Identical ETAs breaking ties deterministically by partner ID.
  - Duplicate cancellation events with identical and different order payloads.
  - Workload reduction exceeding current partner workload.
- **Remaining failures or known limitations:**
  - None. All 238 tests pass cleanly.

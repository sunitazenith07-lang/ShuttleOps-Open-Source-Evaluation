# approach.md — Approach and Implementation Decisions

## 1. Baseline
- **Commands run before editing:**
  ```bash
  python3 --version
  python3 -m pip install -r requirements-dev.txt
  python3 -m pytest -q
  python3 -m main
  ```
- **Initial test result:**
  - Python version: `Python 3.14.7`
  - Total test count: 229 tests across `tests/test_acceptance_matrix.py`, `tests/test_contract.py`, and `tests/test_edge_cases.py`
  - Actual initial summary: `65 failed, 164 passed in 0.39s`
  - Key failures observed:
    - Travel time validation failures (`test_invalid_or_missing_travel_time_rejected`) with `TypeError` when handling non-numeric strings (`"2"`) and booleans (`True`).
    - Preparation time validation failures (`test_preparation_time_validation`) when receiving negative numbers, booleans, string numbers, `None`, `nan`, or `inf`.
    - Inactive partner filtering failures (`test_inactive_partners_never_selected`).
    - Partner capacity enforcement failures (`test_capacity_boundary_matrix`).
    - Duplicate cancellation idempotency failures (`test_duplicate_cancellation_is_idempotent_across_workloads`).
- **Demo/output observed:**
  ```bash
  $ python3 -m main
  {'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
  ```

## 2. Codebase understanding
- **Important files/functions inspected:**
  - `service.py`: Contains the core dispatch and ETA engine functions:
    - `estimate_eta(order, partner, travel, now=0)`: Computes pickup and delivery ETA for a single candidate partner.
    - `assign_order(order, partners, travel, now=0)`: Filters candidates, calculates ETAs, performs tie-breaking, and returns assignment result.
    - `process_cancellation(partner, order_id, event_id)`: Applies order cancellation to partner workload and capacity.
  - `models.py`: Helper factories `new_order` and `new_partner` setting default schemas (`active: True`, `capacity: 2`, `workload_minutes: 0`, `active_order_ids: []`, `prep_minutes: 10`).
  - `fixtures.py` & `main.py`: Offline sample inputs demonstrating expected flow with 2 delivery partners.
  - `data/records.json`: Expanded synthetic dataset comprising 180 orders, 60 partners, 387 travel routes, and 177 cancellation events.
  - `tests/`: Matrix tests checking edge-case combinations of travel legs, workloads, preparation times, capacity thresholds, and cancellation idempotency.
- **Candidate filtering, ETA calculation, and capacity flow traced:**
  - In the starter implementation of `assign_order`, candidate partners were neither filtered by their `active` flag nor checked against their `capacity` limit (`len(active_order_ids) < capacity`).
  - In `estimate_eta`, the arithmetic `pickup = now + leg1 + workload` and `eta = pickup + prep + leg2` directly added inputs without type-checking or range validation, throwing unhandled `TypeError` exceptions on string values or silently producing corrupted ETAs on negative numbers, booleans, NaN, and infinity.
  - In `process_cancellation`, the starter unconditionally appended `event_id` to `processed_cancellation_ids` without verifying whether that `event_id` had already been processed, which violated idempotency and allowed double cancellations.
- **How understanding was confirmed:**
  - Ran `pytest` with traceback analysis (`--tb=short`), examined the exact parameterized inputs that failed assertions, and validated input boundary behaviors against `STUDENT_PROBLEM_STATEMENT.md`.

## 3. Investigation and implementation strategy
- **Issue 1: Type safety and validation for travel, preparation, and workload times**
  - *Symptom:* `TypeError: unsupported operand type(s) for +: 'int' and 'str'` when travel times were string literals, and incorrect eligibility when times were boolean, negative, NaN, or infinite.
  - *Hypothesis:* The system lacked a strict non-negative finite numeric validation helper. In Python, booleans inherit from `int` (`isinstance(True, int) == True`), which causes `True` to be treated as `1` unless explicitly disallowed.
  - *Evidence:* Acceptance matrix test cases `test_invalid_or_missing_travel_time_rejected[2-1]` and `test_preparation_time_validation[True]`.
  - *Fix:* Created helper `_is_valid_non_negative_number(val)` verifying that `val` is not None, not a boolean, is an `int` or `float`, is `>= 0`, and is finite (`math.isfinite(val)`). Used this helper across `estimate_eta` and `assign_order`.
- **Issue 2: Inactive partners and capacity constraints ignored in assignment**
  - *Symptom:* Inactive partners and partners with active orders at or exceeding capacity were assigned orders.
  - *Hypothesis:* `assign_order` iterated over all partners without evaluating `partner.get('active') is True` and `active_count < capacity` where `capacity >= 1`.
  - *Evidence:* `test_inactive_partner_not_assigned` and `test_capacity_boundary_matrix[1-1]` failed.
  - *Fix:* Added upfront candidate filtering in `assign_order`: require `partner.get('active') is True`, `isinstance(capacity, int) and not isinstance(capacity, bool) and capacity >= 1`, and `len(active_order_ids) < capacity`.
- **Issue 3: Cancellation idempotency and workload underflow**
  - *Symptom:* Duplicate cancellation events repeatedly appended the event ID and could reduce partner workload below zero.
  - *Hypothesis:* `process_cancellation` recorded `event_id` without checking if `event_id in out['processed_cancellation_ids']`.
  - *Evidence:* `test_duplicate_cancellation_is_idempotent_across_workloads` failed with duplicate IDs `['C', 'C']`.
  - *Fix:* Guarded `process_cancellation` by checking `if event_id in out['processed_cancellation_ids']: return out`. If not previously processed, deduct minutes only if `order_id in out['active_order_ids']`, clamp remaining workload at zero (`max(0, workload - deduct)`), and append `event_id`.
- **Issue 4: Deterministic tie-breaking on identical ETAs**
  - *Symptom:* Order assignment must guarantee reproducible selection when multiple partners have identical ETA.
  - *Hypothesis:* Sorting key must combine ETA and lexicographical partner ID.
  - *Evidence:* `test_dispatch_selects_lowest_eta_and_stable_tie` and `test_ties_break_by_partner_id_independent_of_input_order`.
  - *Fix:* Used `min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))`.

## 4. Implementation decisions
- **Main changes and why:**
  - Implemented centralized validation helpers `_is_valid_non_negative_number` and `_is_valid_string_id` to ensure strict defensive handling without code duplication.
  - In `estimate_eta`, safely handled missing travel dictionary keys and invalid numeric parameters by returning `{'partner_id': partner_id, 'eta_minutes': None, 'eligible': False}`.
  - In `assign_order`, added order format validation (non-empty string IDs, non-negative prep time, valid current time `now`), skipped ineligible partners, and returned deterministic unassigned responses with descriptive reasons when no candidate is available.
  - In `process_cancellation`, ensured deep immutability, idempotent event tracking, and clamped workload reduction.
  - Implemented the optional stretch feature `batch_assign_orders` to process multiple orders sequentially in supplied priority order, dynamically updating partner capacity and workload across assignments.
- **Alternatives considered and why rejected:**
  - *Modifying input dictionaries in place:* Rejected to maintain pure function semantics and prevent side effects during evaluation and simulated rollouts.
  - *Treating missing travel time as 0:* Rejected because missing route data is unknown, not zero (violates problem contract requirement 5).
  - *Using float('inf') for missing ETA:* Rejected because downstream contract specifically expects `None` for ineligible ETAs.
- **Assumptions:**
  - Route keys in `travel` are 2-tuples of `(origin, destination)`.
  - A partner's active order count is based on the length of `active_order_ids`.
  - Travel time, prep time, and current time values may be floats or integers, but must be finite and non-negative.

## 5. Verification
- **Tests added or changed:**
  - Did not delete, weaken, or bypass any of the original 229 tests.
  - Created new test module `tests/test_regression.py` containing 9 comprehensive regression test functions:
    1. `test_regression_travel_time_non_numeric_and_special_floats`: string, boolean, NaN, and Inf travel leg rejection.
    2. `test_regression_negative_travel_and_prep_times`: negative time rejection.
    3. `test_regression_inactive_partner_filtering`: inactive flag types (False, None, 0, "active").
    4. `test_regression_capacity_boundary_and_validation`: capacity limits and invalid capacity types.
    5. `test_regression_lexicographic_tie_breaking`: multi-partner tie resolution independent of list order.
    6. `test_regression_cancellation_idempotency_and_clamping`: duplicate event deduplication and zero-floor clamping.
    7. `test_regression_malformed_inputs_gracefully_handled`: None/empty inputs for order, partner list, and travel map.
    8. `test_regression_synthetic_records_dataset_integration`: full integration test loading `data/records.json` (180 orders, 60 partners, 387 travel routes).
    9. `test_regression_batch_assignment_stretch_feature`: sequential multi-order assignment verifying dynamic capacity exhaustion.
- **Commands run and actual results:**
  - Baseline: `229 passed, 65 failed in 0.39s` (164 passed).
  - After implementation: `238 passed in 0.11s` (100% pass rate).
  - Demo command: `python3 -m main` ran cleanly with exit code 0.
- **Edge cases verified:**
  - Zero travel/prep time boundary values (`0 + 0 + 0 = 0`).
  - Full partner capacity (`active_count == capacity`).
  - Missing route data in travel table (`None` return, unassigned reason).
  - Duplicate cancellation with identical event ID (no duplicate reduction).
  - Cancellation order not present in partner's active list (safely ignored, no reduction).
- **Remaining failures or known limitations:**
  - None. All 238 tests pass cleanly.

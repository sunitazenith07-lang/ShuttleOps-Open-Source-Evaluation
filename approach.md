# approach.md - Implementation Approach and Decisions

This document explains how I analyzed, fixed, and verified the SmartDispatch delivery partner assignment engine. It is written in simple, clear language so that any student or evaluator can easily follow the implementation.

---

## 1. Baseline

Before changing any code, I ran the baseline tests and the demo script to understand the starting state of the project.

- **Commands run before editing:**
  ```bash
  python -m pip install -r requirements-dev.txt
  python -m pytest -q
  python -m main
  ```
- **Initial test result:**
  ```text
  65 failed, 164 passed in 0.88s (229 total tests)
  ```
  Out of 229 tests, 65 tests failed. This was expected because the starter code had intentional bugs and missing features.
- **Demo output observed:**
  ```text
  {'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
  ```
  The demo ran, but the engine was assigning partners without checking their active status or current capacity.

---

## 2. Codebase Understanding

I inspected all project files to trace how data flows through the application:

- **Important files inspected:**
  - `models.py`: Helper functions that build dictionaries for orders and delivery partners.
  - `service.py`: The core dispatch engine containing `estimate_eta()`, `assign_order()`, and `process_cancellation()`.
  - `fixtures.py`: Sample data used by the offline demo.
  - `main.py`: Entry point that runs the offline demo.
  - `tests/test_contract.py`: Contract tests checking basic dispatch rules.
  - `tests/test_acceptance_matrix.py`: Large test matrix checking edge cases, boundary values, and invalid types.
  - `tests/test_edge_cases.py`: Checks ETA calculations across different time values.

### Step-by-Step Data Flow

1. **Order Input:** An order comes in with an `order_id`, `restaurant_id`, `destination_zone`, and `prep_minutes`.
2. **Partner Filtering:**
   - The engine checks each delivery partner in the list.
   - A partner must be active (`active == True`).
   - A partner must have room for more orders (`len(active_order_ids) < capacity`).
   - If a partner is inactive or full, the engine skips them.
3. **ETA Calculation:**
   - For each eligible partner, the engine looks up two travel legs in the travel table:
     - `leg1`: Travel time from the partner's current zone to the restaurant.
     - `leg2`: Travel time from the restaurant to the customer's delivery zone.
   - If either travel time is missing or invalid, the partner cannot be used.
   - **Pickup Time Formula:**
     $$\text{pickup\_minutes} = \text{now} + \text{leg1} + \text{workload\_minutes}$$
   - **Delivery ETA Formula:**
     $$\text{eta\_minutes} = \text{pickup\_minutes} + \text{prep\_minutes} + \text{leg2}$$
4. **Order Assignment:**
   - The engine gathers all partners who have a valid ETA.
   - If no partner qualifies, it returns `partner_id: None` with a clear reason.
   - If one or more partners qualify, it picks the partner with the lowest `eta_minutes`.
   - If two partners have the exact same ETA, it breaks the tie by sorting their `partner_id` alphabetically (lexicographically).
5. **Order Cancellation:**
   - When an order is canceled, the engine checks if the cancellation `event_id` was already processed.
   - If it was already processed, it does nothing (this is called *idempotency*).
   - If it is new, it removes the order, reduces the partner's workload, and records the `event_id`.
   - The partner's workload is never allowed to go below zero.

---

## 3. Investigation and Implementation Strategy

I investigated the 65 failing tests and grouped them into three main issues.

### Issue 1: Missing Input Validation in `estimate_eta()`
- **Symptom:** Tests crashed with `TypeError` when travel times were strings like `"2"`. Tests also failed when given negative times, `NaN`, `infinity`, booleans, or empty order IDs.
- **Hypothesis:** `estimate_eta()` was doing math directly without checking if the inputs were valid positive numbers. In Python, `bool` is a subclass of `int`, so `isinstance(True, int)` is `True`. This allowed booleans to slip through as numbers.
- **Evidence:** `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[-1-1]` failed because `-1` was accepted as a valid travel time.
- **Fix Chosen:**
  - Added `_is_valid_non_negative_number(val)`: explicitly rejects booleans, accepts non-negative integers, and accepts non-negative finite floats using `math.isfinite()`.
  - Added `_is_valid_non_empty_str(val)`: ensures IDs and zones are non-empty strings.
  - Validated `now`, `prep_minutes`, `workload_minutes`, `leg1`, `leg2`, and `partner.zone`.
  - If any value is invalid or missing, `estimate_eta()` safely returns `{'partner_id': ..., 'eta_minutes': None, 'eligible': False}`.

### Issue 2: Inactive and Full Partners Assigned in `assign_order()`
- **Symptom:** Partners with `active=False` or partners who already reached their capacity were still being assigned orders.
- **Hypothesis:** `assign_order()` had a placeholder loop that directly called `estimate_eta()` without checking partner status or capacity limits.
- **Evidence:** `tests/test_contract.py::test_inactive_partner_not_assigned` and `test_full_partner_not_assigned` failed because inactive and full partners were assigned.
- **Fix Chosen:**
  - Added `_is_valid_capacity(val)`: checks that capacity is an integer $\ge 1$ and not a boolean.
  - Added strict check: `partner.get('active') is True`.
  - Checked that `len(partner.get('active_order_ids', [])) < capacity`.
  - Ineligible partners are skipped before ETA calculation.

### Issue 3: Duplicate Cancellations Subtracted Workload Twice in `process_cancellation()`
- **Symptom:** When the same cancellation event was sent twice, the cancellation ID was added twice to `processed_cancellation_ids` (`['C1', 'C1']`), and the workload was deducted twice.
- **Hypothesis:** `process_cancellation()` appended the `event_id` without checking if it was already in `processed_cancellation_ids`.
- **Evidence:** `tests/test_contract.py::test_duplicate_cancellation_is_idempotent` failed with `['C1', 'C1'] == ['C1']`.
- **Fix Chosen:**
  - Checked `if event_id in out['processed_cancellation_ids']: return out`.
  - If already processed, return the partner state immediately without any changes.
  - If new, remove the order, safely reduce workload using `max(0, workload - minutes)`, and append the `event_id` once.

---

## 4. Implementation Decisions

- **Main changes and why:**
  - Kept all logic inside `service.py` to preserve the original architecture.
  - Used defensive helper functions so that bad input never causes unhandled exceptions.
  - Used `min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))` for single-pass selection and deterministic tie-breaking.
  - Handled data immutably where required (`deepcopy` in cancellation) so callers do not experience unexpected side effects.
- **Alternatives considered and why rejected:**
  - *Sorting the whole list of candidates:* Sorting takes $O(N \log N)$ time. Using `min()` takes $O(N)$ time, which is faster and cleaner for finding a single winner.
  - *External validation libraries (like Pydantic):* The project instructions require using the existing codebase and standard library. Built-in helpers keep the project lightweight and fast.
- **Assumptions:**
  - Valid IDs and zones must be non-empty strings.
  - Missing travel routes in the `travel` dictionary mean the route cannot be completed; they must never default to zero.
  - Workload cannot be negative.

---

## 5. Verification

- **Tests run and actual results:**
  - Step 1 (After Bug 1 fix): 195 passed, 34 failed.
  - Step 2 (After Bug 2 fix): 213 passed, 16 failed.
  - Step 3 (After Bug 3 fix): **229 passed, 0 failed** in 0.35 seconds.
- **Commands run:**
  ```bash
  python -m pytest -v
  python -m main
  ```
- **Edge cases verified:**
  - Missing travel routes (`None`) marked ineligible.
  - Non-numeric strings, negative numbers, `NaN`, `infinity`, and booleans rejected.
  - Inactive partners (`False`, `0`, `"no"`, `None`) rejected.
  - Capacity boundary (`active_order_ids >= capacity`) respected.
  - Exact tie-breaks decided by partner ID in alphabetical order.
  - Duplicate cancellations ignored safely.
- **Remaining failures or known limitations:**
  - All 229 automated tests pass with zero failures.
  - The engine is designed for offline batch/single dispatch and does not include live GPS tracking or persistent database storage, which matches the project specification.

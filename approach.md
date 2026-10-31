# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- **Commands run before editing:**
  - `python main.py`
  - `python -m pytest -q`
- **Initial test result (include the actual summary):**
  - The starter test suite (`tests/test_acceptance_matrix.py`) failed across validation, partner filtering, edge-case time handling, and duplicate cancellation tests because `service.py` contained intentional starter defects.
- **Demo/output observed:**
  - Running `python main.py` with `sample_inputs()` executed `assign_order` without validating order fields or partner active/capacity states and printed:
    `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

## 2. Codebase understanding
- **Important files/functions inspected:**
  - `models.py`: Inspected `new_partner` and `new_order` factory functions to see the expected dictionary keys (`partner_id`, `zone`, `active`, `capacity`, `active_order_ids`, `workload_minutes`, `minutes_by_order`, `processed_cancellation_ids`, `order_id`, `restaurant_id`, `destination_zone`, `prep_minutes`).
  - `service.py`: Inspected `estimate_eta`, `assign_order`, and `process_cancellation`, noting the inline comments indicating missing validation and missing idempotency checks.
  - `fixtures.py` & `main.py`: Inspected `sample_inputs()` to see how the travel matrix `{(from_id, to_id): minutes}` is structured and passed to `assign_order`.
- **Candidate filtering, ETA calculation, and capacity flow traced:**
  - `assign_order` loops over `partners`, calls `estimate_eta(order, partner, travel, now)` for each candidate, collects results where `estimate['eligible']` is `True`, and selects the minimum candidate using `(item['eta_minutes'], str(item['partner_id']))`.
  - `estimate_eta` looks up `leg1 = travel.get((partner.zone, order.restaurant_id))` and `leg2 = travel.get((order.restaurant_id, order.destination_zone))`, computes `pickup = now + leg1 + workload_minutes`, and computes `eta_minutes = pickup + prep_minutes + leg2`.
- **How you confirmed your understanding:**
  - Traced `sample_inputs()` by hand (`P-2` in `Z-1`: `pickup = 0 + 8 + 5 = 13`, `eta = 13 + 10 + 12 = 35`; `P-1` in `Z-3`: `pickup = 0 + 12 + 2 = 14`, `eta = 14 + 10 + 12 = 36`) and matched it against the output of `python main.py` and the expectations in `tests/test_acceptance_matrix.py`.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- **Issue 1: Unvalidated orders, inactive/full partners accepted, and non-finite/negative times allowed**
  - **Symptom:** Orders with missing IDs or negative/boolean/`inf` preparation or travel times were accepted, and inactive partners (`active=False`) or partners at full capacity (`len(active_order_ids) >= capacity`) were still assigned orders.
  - **Hypothesis:** `assign_order` lacked pre-loop order validation and partner eligibility guards, and `estimate_eta` only checked `leg1 is None or leg2 is None` without verifying that time values were finite, non-boolean, non-negative numbers.
  - **Evidence:** Starter comment in `assign_order` (`# Starter is intentionally incomplete: active/capacity/time validation is missing.`) and pytest failures on `test_invalid_or_missing_travel_time_rejected[1-inf]` and `test_preparation_time_validation[inf]`.
  - **Fix chosen:** Added helper functions `_is_non_empty_str(val)` and `_is_non_neg_num(val)` (checking `not isinstance(val, bool) and isinstance(val, (int, float)) and math.isfinite(val) and val >= 0`), validated order fields before the loop, and added `active is True` and `len(active_orders) < capacity` guards inside `assign_order`.
- **Issue 2: Duplicate cancellation events deducted workload multiple times**
  - **Symptom:** Calling `process_cancellation(partner, order_id, event_id)` twice with the same `event_id` recorded the `event_id` twice and could repeatedly mutate state.
  - **Hypothesis:** `process_cancellation` appended `event_id` to `processed_cancellation_ids` at the end of the function without checking if `event_id` had already been processed.
  - **Evidence:** Starter comment in `process_cancellation` (`# Starter defect: event_id is recorded but not checked before applying the event.`) and cancellation idempotency tests in `test_acceptance_matrix.py`.
  - **Fix chosen:** Added an early return guard `if not _is_non_empty_str(event_id) or event_id in out['processed_cancellation_ids']: return out` before removing `order_id` or subtracting workload.
- **Issue 3: Malformed records and non-dict/non-list inputs caused runtime errors**
  - **Symptom:** Passing `None` or corrupted partner/order dictionaries (e.g., `active_order_ids=None` or negative `workload_minutes`) raised `AttributeError` or `TypeError`.
  - **Hypothesis:** `setdefault` only sets a default when a key is completely missing, not when the key exists with value `None` or a non-list type.
  - **Evidence:** Edge-case test cases in `test_acceptance_matrix.py` testing malformed inputs and corrupted records.
  - **Fix chosen:** Added `isinstance(..., dict)` and `isinstance(..., list)` guards across `estimate_eta`, `assign_order`, and `process_cancellation`, and sanitized corrupted `active_order_ids`, `processed_cancellation_ids`, and `workload_minutes` fields.

## 4. Implementation decisions
- **Main changes and why:**
  - Centralized string and numeric validation in `_is_non_empty_str` and `_is_non_neg_num` inside `service.py` so `estimate_eta`, `assign_order`, and `process_cancellation` enforce identical rules for IDs and time values.
  - Added `math.isfinite(val)` to `_is_non_neg_num` so `float('inf')`, `float('-inf')`, and `float('nan')` are rejected alongside negative numbers and booleans.
- **Alternatives considered and why rejected:**
  - *Alternative 1:* Checking only `isinstance(val, (int, float)) and val >= 0` for time values. Rejected because in Python `isinstance(True, int)` is `True` and `float('inf') >= 0` is `True`, which caused boolean and infinity test cases to fail.
  - *Alternative 2:* Using `partner.get('active', False)` truthiness instead of `partner.get('active') is True`. Rejected because non-boolean truthy values (such as `'active': 1` or `'active': 'yes'`) should not be treated as valid active flags.
- **Assumptions:**
  - `assign_order` returns an assignment decision dictionary without mutating the chosen partner's `active_order_ids` or `workload_minutes` in place.
  - Missing travel routes must always remain `None` and render a candidate ineligible rather than defaulting to `0` minutes.

## 5. Verification
- **Tests added or changed:**
  - Verified against the existing acceptance test suite in `tests/test_acceptance_matrix.py` (no test assertions were weakened or removed).
- **Commands run and actual results:**
  - `python -m pytest -q` — All acceptance matrix tests passed (`0 failed, 0 errors`).
  - `python main.py` — Returned deterministic assignment output `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.
- **Edge cases verified:**
  - Infinite (`float('inf')`), `NaN`, negative, and boolean (`True`/`False`) preparation, workload, and travel times.
  - Duplicate cancellation `event_id` calls and cancellations for unknown `order_id`s.
  - Tie-breaking between candidates with identical ETAs using ascending lexicographic `partner_id` order.
  - Empty partner lists, missing travel dictionary entries, and malformed partner/order records.
- **Remaining failures or known limitations:**
  - No remaining test failures. Known architectural limitations are that state is held in memory using plain dictionaries and `assign_order` evaluates one order at a time greedily.
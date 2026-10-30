# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing:
  - `python -m pip install -r requirements-dev.txt`
  - `python -m pytest -q`
  - `python -m main`
- Initial test result (include the actual summary):
  - Total Tests: 229
  - Passed: 164
  - Failed: 65 (failures across `test_acceptance_matrix.py` and `test_contract.py`)
  - Errors: 0, Skipped: 0
  - Duration: 3.13s
- Demo/output observed:
  - `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

## 2. Codebase understanding
- Important files/functions inspected:
  - `service.py`: Contains `estimate_eta`, `assign_order`, and `process_cancellation`.
  - `models.py`: Lightweight entity factories (`new_order`, `new_partner`) producing standard Python dictionaries.
  - `fixtures.py` & `main.py`: Sample inputs and execution script for offline demonstration.
  - `tests/test_contract.py`, `tests/test_acceptance_matrix.py`, `tests/test_edge_cases.py`: Contract and parameterized test suites.
  - `data/records.json`: Expanded dataset with 180 orders, 60 partners, 387 travel times, and 177 cancellations.
- Candidate filtering, ETA calculation, and capacity flow traced:
  - Incoming orders undergo field validation (order ID, restaurant ID, destination zone, prep minutes).
  - Candidates are filtered by active status (`partner['active'] is True`) and capacity (`len(active_order_ids) < capacity`).
  - For each eligible partner, pickup time is calculated as `now + leg1_travel + workload`, and ETA as `pickup + prep_minutes + leg2_travel`. Missing travel data renders a candidate ineligible.
  - The partner with lowest ETA is selected, with ties broken by partner ID in ascending lexicographical order.
  - Cancellation events release workload and capacity idempotently.
- How you confirmed your understanding:
  - Traced data flow line-by-line against the acceptance matrix and reproduced the 65 baseline test failures.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1: Unvalidated travel and preparation time inputs in `estimate_eta`.
  - *Symptom:* `TypeError: unsupported operand type(s) for +: 'int' and 'str'` when travel times were strings, and silent acceptance of negative times, booleans, NaN, and infinity.
  - *Hypothesis:* The function assumed sanitized numerical inputs without guarding against invalid types.
  - *Evidence:* Failures in `test_invalid_or_missing_travel_time_rejected` and `test_preparation_time_validation`.
  - *Fix:* Added `_is_valid_non_negative_number` validator to reject negative values, strings, booleans, NaN, and infinity, returning `eligible=False` immediately.
- Issue 2: Missing active status and capacity enforcement in `assign_order`.
  - *Symptom:* Inactive partners and partners at full capacity were assigned new orders.
  - *Hypothesis:* `assign_order` looped over all candidates and only checked ETA route eligibility, omitting partner state checks.
  - *Evidence:* Failures in `test_inactive_partners_never_selected` and `test_capacity_boundary_matrix`.
  - *Fix:* Enforced `partner.get('active') is True`, validated integer `capacity >= 1`, and verified `len(active_orders) < capacity`.
- Issue 3: Non-idempotent cancellation handling in `process_cancellation`.
  - *Symptom:* Duplicate cancellation events repeatedly deducted workload and appended duplicate event IDs.
  - *Hypothesis:* `process_cancellation` recorded event IDs without checking whether the event had already been processed.
  - *Evidence:* Failures in `test_duplicate_cancellation_is_idempotent_across_workloads` where `processed_cancellation_ids` became `['C', 'C']`.
  - *Fix:* Implemented early exit `if event_id in out['processed_cancellation_ids']: return out` to ensure idempotency.

## 4. Implementation decisions
- Main changes and why:
  - Kept code beginner-friendly and functional using standard Python dictionaries without unnecessary class overhead.
  - Created standalone helper functions `_is_valid_non_negative_number` and `_is_valid_id` for clean, readable validation.
  - Added `tests/conftest.py` to ensure `sys.path` correctly resolves the repository root across all terminal environments.
- Alternatives considered and why rejected:
  - Custom exception classes / try-except blocks: Rejected in favor of explicit defensive validation for better readability and performance.
  - Object-oriented partner/order classes: Rejected to preserve full backward compatibility with starter contracts and tests.
- Assumptions:
  - Missing travel routes indicate unreachable destinations and must never default to zero.
  - A partner with capacity <= 0 or non-integer capacity is considered misconfigured and ineligible.

## 5. Verification
- Tests added or changed:
  - Added `tests/test_regression.py` covering edge-case types, boundary conditions, dataset processing, and multi-call idempotency.
  - Created `tests/conftest.py` for root directory resolution.
- Commands run and actual results:
  - `python -m pytest -q` -> 235 passed (229 existing + 6 new regression tests) in 0.95s, 0 failures.
  - `python -m main` -> Demo output verified.
- Edge cases verified:
  - Negative preparation times, boolean inputs (`True`/`False`), NaN/Inf, missing travel legs, capacity limits, tie-breaking order independence, and duplicate cancellations.
- Remaining failures or known limitations:
  - Zero remaining failures. All tests pass with 100% success rate.

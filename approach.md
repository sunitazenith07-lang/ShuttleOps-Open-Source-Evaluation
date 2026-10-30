# approach.md - Required submission

## 1. Baseline
- Commands run before editing: `pytest`
- Initial test result (include the actual summary): `56 failed, 173 passed in 0.55s`
- Demo/output observed: The terminal showed multiple `TypeError` messages (e.g., trying to compare a string to an int), `AssertionError: assert 'P' is None` for capacity checks, and failures in cancellation workload math (e.g., `assert 9 == 0`).

## 2. Codebase understanding
- Important files/functions inspected: `service.py` (for logic), `fixtures.py` (to understand data structure), and `tests/test_acceptance_matrix.py` (to see exactly what edge cases were being tested).
- Candidate filtering, ETA calculation, and capacity flow traced: I traced how `assign_order` loops through partners, checks if they are active, calls `estimate_eta`, and then uses `min()` to find the lowest time.
- How you confirmed your understanding: I read the `STUDENT_PROBLEM_STATEMENT.md` and matched the rules (like tuple lookups and missing travel time) against the failing assertions in the test file.

## 3. Investigation and implementation strategy
- **Issue 1: Invalid Data Types (Strings, Booleans, NaN)**
  - Symptom: Tests crashed with `TypeError` or incorrectly marked bad data as eligible.
  - Hypothesis: Python treats `True` as `1`, and basic `< 0` checks don't catch `NaN`.
  - Evidence: `TypeError: '<' not supported between instances of 'str' and 'int'`.
  - Fix: Created a helper function `is_valid_num()` to strictly check for real integers/floats, rejecting booleans and `NaN`.
- **Issue 2: Travel Dictionary Lookup**
  - Symptom: Travel times were never found, resulting in wrong ETAs.
  - Hypothesis: The dictionary keys were tuples `(zone, restaurant)`, but the code passed them as separate arguments.
  - Evidence: Inspecting `fixtures.py` showed keys like `('Z-1', 'R-2')`.
  - Fix: Added extra parentheses: `travel.get((partner.get('zone'), order.get('restaurant_id')))`.
- **Issue 3: Workload Deduction on Cancellation**
  - Symptom: Cancelling an order didn't reduce the partner's workload.
  - Hypothesis: The workload was stored as a dictionary (`minutes_by_order`), not a single integer.
  - Evidence: `assert 9 == 0` failure in `test_distinct_cancellation_events_recorded_once_each`.
  - Fix: Looked up the specific `order_id` inside `minutes_by_order` and added an idempotency check to prevent double-deductions.

## 4. Implementation decisions
- Main changes and why: I added strict validation to `estimate_eta` before doing any math to prevent crashes. I added an idempotency check in `process_cancellation` to safely handle duplicate events.
- Alternatives considered and why rejected: I considered using `try/except` blocks to catch math errors, but rejected this because it might silently hide logic bugs instead of properly rejecting malformed input.
- Assumptions: If a partner's capacity is not explicitly stated in the data, I defaulted it to 2 (based on standard fixtures).

## 5. Verification
- Tests added or changed: None. I strictly followed the rule to not modify the test files.
- Commands run and actual results: Ran `pytest` after applying the fixes. Result: `229 passed in 0.14s`.
- Edge cases verified: `nan`/`inf` prep times, missing travel routes, capacity boundaries, duplicate cancellations, and negative workloads.
- Remaining failures or known limitations: None. All 229 tests passed successfully.
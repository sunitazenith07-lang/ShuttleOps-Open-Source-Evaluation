# approach.md - Required submission

## 1. Baseline
- Commands run before editing:
  - `python -m pip install -r requirements-dev.txt`
  - `python -m pytest -q`
  - `python -m main`
- Initial test result (include the actual summary):
  - Several failures due to unvalidated inputs (`TypeError` with `None`, strings, booleans), incorrect handling of negative numbers/NaN/inf, and missing capacity/idempotency checks (e.g., multiple tests failing in `test_acceptance_matrix.py` and `test_contract.py`).
- Demo/output observed:
  - `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

## 2. Codebase understanding
- Important files/functions inspected:
  - `service.py`: Core dispatch engine, `estimate_eta()`, `assign_order()`, and `process_cancellation()`.
  - `models.py`: Entity creation schemas and helpers.
  - `tests/test_acceptance_matrix.py` and `tests/test_contract.py`: Acceptance criteria and edge-case boundaries.
- Candidate filtering, ETA calculation, and capacity flow traced:
  - Traced how `assign_order` loops through partners, verifies active status and workload capacity, invokes `estimate_eta`, and applies tie-breaking (lowest ETA, then lexicographic partner ID).
- How you confirmed your understanding:
  - By running the initial test suite and mapping out the failing assertions against unhandled edge cases in time types and partner constraints.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1: Unvalidated time parameters (`prep_minutes`, `now`, travel legs) causing `TypeError` when performing arithmetic (`+`) with `None` or strings, or accepting invalid inputs like negatives and booleans (`True`/`False`).
  - *Fix:* Created a centralized `is_valid_time()` helper function to strictly validate non-negative numbers while rejecting booleans, strings, `None`, `NaN`, and `inf`.
- Issue 2: Partner capacity and active status boundary check failures (e.g., accepting partners with `capacity = None` or `active = 1` instead of strict `True`).
  - *Fix:* Enforced strict type checking for capacity (`isinstance(capacity, int)` and `capacity >= 1`) and strict boolean check (`partner.get('active') is True`).
- Issue 3: Duplicate cancellation events reducing partner workloads more than once.
  - *Fix:* Added an idempotency check in `process_cancellation` to verify if an `event_id` already exists in `processed_cancellation_ids` before applying any updates.

## 4. Implementation decisions
- Main changes and why:
  - Implemented robust input guards in `estimate_eta()` and `assign_order()` to prevent runtime crashes and ensure specification compliance.
- Alternatives considered and why rejected:
  - Duck typing was considered, but strict validation (`isinstance` checks) was necessary because test cases explicitly pass booleans (`True`), strings (`"10"`), and boundary values (`inf`, `nan`) to test engine resilience.
- Assumptions:
  - Float values (e.g., `1.5` minutes) are acceptable time inputs provided they are finite and non-negative.

## 5. Verification
- Tests added or changed:
  - Relied on the comprehensive built-in regression test suite (`test_acceptance_matrix.py` and `test_contract.py`) covering all edge-case matrices.
- Commands run and actual results:
  - `python -m pytest -q`
  - Result: `229 passed in 0.46s` (Zero failures).
- Edge cases verified:
  - Negative/infinite/NaN times, boolean time inputs, missing partner capacity (`None`), inactive partners, and duplicate cancellation idempotency.
- Remaining failures or known limitations:
  - None. All test cases passed successfully.
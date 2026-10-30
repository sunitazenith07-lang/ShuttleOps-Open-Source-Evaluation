# Approach and implementation decisions

## Baseline
- Before editing, `python -m pytest -q` could not start because this terminal has no `python` command.
- `python3 -m pytest -q --tb=no` on Python 3.14.7: **65 failed, 164 passed**.
- The starter demo ran and printed partner `P-2` with ETA 35 minutes.

## Codebase understanding
- The acceptance rules are in `STUDENT_PROBLEM_STATEMENT.md`; `service.py` contains ETA estimation, partner selection and cancellation handling.
- `models.py` creates the example order and partner records. The tests in `tests/` specify ETA math, input validation, capacity, tie-breaking and cancellation behavior.
- `assign_order` estimates each partner's ETA, selects the smallest ETA, and uses partner ID as the tie-break. `process_cancellation` returns a copy of partner state.
- The baseline tests confirmed these flows were incomplete: eligibility was not checked, times and records were not validated, and processed cancellation IDs were not checked.

## Investigation and implementation strategy
1. Travel-time cases with negative, non-numeric, Boolean, NaN or infinite values failed because ETA estimation only checked for missing routes. Added explicit non-negative finite numeric validation.
2. Inactive and at-capacity partners were selected because dispatch did not check either field. Dispatch now requires `active is True`, a valid positive integer capacity, and an active-order count below capacity.
3. Duplicate cancellations were applied repeatedly because event IDs were appended without checking existing IDs. The cancellation handler now returns unchanged copied state for a previously processed event.
4. Added validation for required identifiers, preparation/workload/current-time values, malformed records and overflowing ETA arithmetic. Invalid dispatch candidates remain unassigned rather than raising during ordinary estimation.

## Implementation decisions
- Numeric strings and Booleans are rejected instead of coerced; coercion could turn malformed inputs into valid-looking time estimates.
- Missing required travel entries remain invalid; they are never substituted with zero.
- ETA ordering remains deterministic: `(eta_minutes, partner_id)`.
- Cancellation state is copied before changes, and workload is clamped at zero as in the starter behavior.

## Verification
- Added `tests/test_regressions.py` for malformed records, overflow and cancellation input immutability.
- Final `python3 -m pytest -q`: **235 passed**.
- Final `python3 -m main` output: `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.
- `git diff --check` completed successfully.
- I used AI assistance after receiving instructor clarification; see `AI_USAGE_TEMPLATE.md` for the disclosure. The initial local `python` command was unavailable, so validation used `python3`.

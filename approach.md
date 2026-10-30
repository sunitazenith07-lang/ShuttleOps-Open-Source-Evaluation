# Approach

## 1. Baseline
- Commands run before editing: `./.venv/bin/python -m pytest -q` and `python3 -m main`.
- Initial result: 65 failed, 164 passed.
- Demo output observed: `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.

## 2. Codebase understanding
- Inspected `service.py`, `models.py`, `fixtures.py`, `main.py`, the dataset documentation, and every test under `tests/`.
- Traced assignment through `assign_order()` and `estimate_eta()`, including travel lookups, workload addition, active/capacity filtering, and cancellation processing.
- Parameterized tests confirmed that ETA uses `now + partner-to-restaurant + workload + preparation + restaurant-to-customer`.

## 3. Investigation and implementation strategy
- **Inactive and full partners:** the starter omitted eligibility checks. I added exact-active (`is True`), valid-capacity, and active-order count checks.
- **Invalid values:** negative travel and preparation values could be accepted. I added finite, non-negative, non-Boolean numeric validation.
- **Duplicate cancellations:** repeated cancellation could release state again. I check processed IDs before mutation.

## 4. Implementation decisions
- Validation helpers are private in `service.py` and reject strings, booleans, negative values, NaN, and infinity. Missing data remains distinct from valid zero-minute values.
- Candidate selection remains a deterministic minimum over ETA and string partner ID.
- Cancellation copies partner state and safely normalizes malformed collections.

## 5. Verification
- Existing parameterized tests were not weakened. The suite exercised 229 cases covering zeros, large values, invalid types, capacity boundaries, tie-breaking, missing routes, and repeated cancellations.
- Final command: `./.venv/bin/python -m pytest -q` — 233 passed in 0.07s.
- Final demo command: `python3 -m main` — produced the assigned sample result above.
- No remaining visible-suite failures are known.

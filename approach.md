# approach.md — implementation notes

## 1. Baseline
- Command before changes: `.venv/bin/python -m pytest -q`
- Initial result: **65 failed, 164 passed**.
- Demo command: `.venv/bin/python -m main`
- Initial demo output assigned partner `P-2` with ETA 35 minutes.

## 2. Codebase understanding
- `models.py` creates the order and partner dictionaries; `fixtures.py` supplies the small demo case.
- `estimate_eta` reads the two route times and calculates pickup and delivery times.
- `assign_order` evaluates partners and chooses the lowest ETA.
- `process_cancellation` copies a partner record, removes a cancelled order, and subtracts its recorded workload.
- The acceptance tests showed that the basic formula, missing-route rejection, and ID tie-break worked, but partner eligibility, capacity, invalid values, and duplicate event handling did not.

## 3. Investigation and implementation strategy
- **ETA validation:** The starter performed arithmetic without checking the values first. Tests demonstrated exceptions for strings and `None`, and incorrect eligibility for negative or non-finite times. I added shared checks for non-empty string identifiers and non-negative finite numeric minute values before calculating.
- **Partner eligibility and capacity:** The assignment loop only checked whether ETA calculation succeeded. The inactive and full-partner tests showed that those partners could still be selected. I added checks for explicitly active partners, valid capacity, and active order count before ETA comparison.
- **Cancellation idempotency:** The starter appended cancellation IDs without checking whether they had already been processed. The duplicate-event test showed duplicate IDs in the result. The function now returns the copied partner unchanged for a repeated event ID.
- **Unassigned explanations:** The original response used one generic message for all failures. Assignment now reports invalid order/collection data and deterministic exclusion reasons such as full capacity or missing route data.

## 4. Implementation decisions
- Kept the existing module, function names, dictionary-based models, and public result shapes.
- Rejected treating missing workload as zero because that can understate ETA; an absent or invalid workload makes the ETA unreliable.
- Kept the prescribed ETA-then-partner-ID ordering. Pickup time is a final deterministic tie-breaker only if malformed input contains two distinct records with the same partner ID and same ETA.
- Used small private validation helpers rather than repeating value checks.
- AI assistance was used for implementation and review with teacher/evaluation-authority permission; the existing tests were retained and run locally.

## 5. Verification
- Added `tests/test_regressions.py`; no existing tests were changed.
- Final command: `.venv/bin/python -m pytest -q` — **239 passed**.
- Demo command: `.venv/bin/python -m main` — assigned `P-2`, pickup 13, ETA 35.
- Pylance diagnostics for `service.py`: no diagnostics reported.
- The repository workflow targets Python 3.11; only Python 3.14.7 was run locally, so the workflow interpreter was not independently tested here.

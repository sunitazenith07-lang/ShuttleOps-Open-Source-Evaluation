# Approach

## 1. Baseline
- Commands run before editing:
  - `python3 -m venv .venv`
  - `. .venv/bin/activate`
  - `python -m pip install -r requirements-dev.txt`
  - `python -m pytest -q`
- Initial result:
  - The suite failed before the fix. The first run showed repeated failures in ETA validation, partner assignment logic, and cancellation handling.
- Demo result observed:
  - The starter assignment logic returned candidates even when the route data was invalid or the partner was inactive or full.

## 2. Codebase understanding
The key files were:
- `service.py` for the dispatch and ETA logic
- `models.py` for the order and partner object structure
- `fixtures.py` for the sample scenario used by the demo
- `main.py` for the sample runner
- `tests/test_contract.py`, `tests/test_acceptance_matrix.py`, and `tests/test_edge_cases.py` for the acceptance contract

I traced the flow as:
- build valid order and partner objects
- validate required route data
- calculate ETA for every candidate
- filter invalid or full partners
- choose the lowest ETA with a stable tie-break
- apply cancellation by reducing workload and releasing active order state once

## 3. Investigation and implementation strategy
Issue 1: invalid or missing travel routes
- Symptom: the ETA logic accepted absent route values and returned a misleading result instead of rejecting them.
- Evidence: the acceptance matrix included invalid/missing travel cases and expected `eligible == False` with `eta_minutes is None`.
- Fix: reject any missing or invalid travel leg before computing ETA.

Issue 2: invalid order, prep-time, or current-time values
- Symptom: malformed values were able to pass through to the assignment engine.
- Evidence: parametrized tests covered negative prep times, invalid current time values, and invalid order fields.
- Fix: enforce non-empty string IDs and non-negative finite numeric values.

Issue 3: assignment logic did not enforce activity or capacity rules
- Symptom: inactive or full partners could still be selected.
- Evidence: multiple acceptance tests expected inactive and full-capacity partners to be excluded.
- Fix: filter partners by `active is True`, valid capacity, and capacity usage before ETA evaluation.

Issue 4: duplicate cancellations released workload twice
- Symptom: repeated cancellation events reduced workload and active order state more than once.
- Evidence: tests for duplicate cancellations and idempotence expected the second call to be ignored.
- Fix: check `event_id` against `processed_cancellation_ids` before applying the cancellation again.

## 4. Implementation decisions
Main changes and why:
- Added numeric validation helpers to reject invalid `None`, negative, boolean, NaN, and infinity values.
- Added stricter ordering validation to ensure order IDs and zone values are real strings.
- Kept the ETA formula aligned with the problem statement: pickup time + prep time + final route leg.
- Enforced partner eligibility before selection: active partner, valid capacity, and not full.
- Made cancellation processing idempotent by tracking processed event IDs and clamping workload to zero.

Alternatives considered:
- Treating missing travel as zero was considered but rejected because it violates the acceptance contract and produces wrong dispatch decisions.
- Hard-coding fixture-specific logic was rejected because the tests require general validation across many inputs.

Assumptions:
- Workload is measured in minutes and should never go below zero.
- Tie-breaking is by partner ID ascending to keep the result deterministic and independent of input order.

## 5. Verification
Tests added or changed:
- I verified the existing acceptance tests and edge-case tests rather than weakening or skipping them.

Commands run and actual results:
- `. .venv/bin/activate && python -m pytest -q`
- Result: `229 passed in 0.05s`

Edge cases verified:
- missing route data
- negative prep time
- invalid current time
- inactive partner
- full-capacity partner
- duplicate cancellation events
- workload floor at zero

Remaining failures or known limitations:
- None. The visible suite passed as written after the fix.

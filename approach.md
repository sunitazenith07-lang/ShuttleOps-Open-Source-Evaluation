# approach.md - Implementation approach

## 1. Baseline
- Commands run before editing:
  - `python -m pip install -r requirements-dev.txt` (installed pytest 9.2.0 on Python 3.11.9)
  - `python -m pytest -q`
- Initial test result: **164 passed, 65 failed** (the 65 failures are the intentionally incomplete starter behaviour described in the problem statement).
- Demo/output observed: `python -m main` printed
  `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.

## 2. Codebase understanding
- Important files/functions inspected:
  - `service.py`: `estimate_eta`, `assign_order`, `process_cancellation` (the main business logic).
  - `models.py`: `new_order`, `new_partner` (data shapes).
  - `fixtures.py`: `sample_inputs` (used by `main.py` and the demo).
  - `main.py`: offline demo execution path.
  - `tests/`: `test_contract.py`, `test_edge_cases.py`, `test_acceptance_matrix.py` (the acceptance contract).
  - `data/records.json`: 180 orders, 60 partners, 387 travel-time rows, 177 cancellations, edge-case catalog.
- Candidate filtering, ETA calculation, and capacity flow traced:
  - `estimate_eta` computes pickup = now + leg1 + workload and ETA = pickup + prep + leg2, but only guarded against `None` travel legs.
  - `assign_order` looped over every partner and took `min` by `(eta, str(partner_id))`, with no active/capacity/order validation.
  - `process_cancellation` recorded `event_id` every call and removed the order/reduced workload every call, so a duplicate cancellation released workload twice.
- How I confirmed understanding: ran the baseline suite; every failure mapped to one of the three starter defects flagged in the source comments ("Starter is intentionally incomplete", "Starter defect").

## 3. Investigation and implementation strategy
For each major defect: symptom, hypothesis, evidence, fix.

- Issue 1 — `estimate_eta` accepted invalid time inputs and crashed on malformed `now`.
  - Symptom: `test_current_time_validation` raised `TypeError` for `now="5"`/`None`; `test_preparation_time_validation` and `test_invalid_or_missing_travel_time_rejected` treated negative/string/boolean/NaN/inf travel and prep as valid.
  - Hypothesis: `estimate_eta` only checked `leg is None` and never validated `now`, `prep`, or the travel values themselves.
  - Evidence: baseline failures in `test_acceptance_matrix` (`test_current_time_validation[-1]`, `[5_1]`, `[True]`, `[None]`, `test_preparation_time_validation`, `test_invalid_or_missing_travel_time_rejected`).
  - Fix: added `_is_valid_number` (real non-bool int/float, finite, >= 0) and `_is_valid_identifier`; `estimate_eta` now validates `now`, both travel legs, and `prep`, returning `eligible=False`/`eta_minutes=None` instead of computing or crashing.

- Issue 2 — `assign_order` ignored partner active status, capacity, and malformed order fields.
  - Symptom: `test_inactive_partner_not_assigned`, `test_full_partner_not_assigned`, `test_capacity_boundary_matrix`, `test_invalid_order_fields_do_not_assign_partner`, `test_negative_prep_time_is_rejected` all failed.
  - Hypothesis: `assign_order` had no eligibility gating beyond `estimate_eta['eligible']`.
  - Evidence: baseline contract-test failures.
  - Fix: `assign_order` now validates order id/restaurant id/destination zone (non-empty strings) and prep time up front, then skips partners that are not `active is True`, have invalid capacity (< 1 non-bool int), or are at/over capacity (`len(active_order_ids) >= capacity`) before calling `estimate_eta`.

- Issue 3 — `process_cancellation` was not idempotent.
  - Symptom: `test_duplicate_cancellation_is_idempotent` and `test_duplicate_cancellation_is_idempotent_across_workloads` produced `processed_cancellation_ids == ['C', 'C']` instead of `['C']`.
  - Hypothesis: `event_id` was appended unconditionally and the workload release was applied on every call.
  - Evidence: contract-test failure showing the duplicated event id.
  - Fix: `process_cancellation` now returns early if `event_id` is already in `processed_cancellation_ids`; otherwise appends the id and only releases workload when `order_id` is actually in `active_order_ids` (workload floored at zero).

## 4. Implementation decisions
- Main changes and why: centralized time validation in `_is_valid_number` so travel data is never treated as zero and malformed `now`/prep cannot crash the demo; eligibility gating in `assign_order` keeps `estimate_eta` focused on ETA maths while assignment enforces the acceptance contract; idempotency guard in `process_cancellation` satisfies "process a cancellation event only once".
- Alternatives considered and why rejected:
  - Putting active/capacity checks inside `estimate_eta`: rejected because `estimate_eta` is also called directly by the ETA-formula tests with a fresh valid partner; keeping assignment-level gating in `assign_order` separates concerns and matches how the contract tests invoke the functions.
  - Rejecting `active` truthy values like `1` or `"yes"`: the acceptance matrix asserts `active is True` selects the partner and makes no assertion for `1`/`"yes"`, so I used the strict `is True` check.
- Assumptions: `now` defaults to 0; capacity must be a non-bool int >= 1; identifiers are non-empty strings; all data is synthetic (no live GPS/mobile app).

## 5. Verification
- Tests added or changed: added `tests/test_regressions.py` (37 tests) covering invalid `now`, invalid travel times, invalid prep, inactive/full-capacity/invalid-capacity partners, malformed order identifiers, tie-breaking, cancellation idempotency, unknown-order cancellation, and a deterministic dispatch pass over a bounded sample of `data/records.json`.
- Commands run and actual results: `python -m pytest -q` → **266 passed, 0 failed**; `python -m main` → P-2 assigned, pickup 13, eta 35 (unchanged, correct).
- Edge cases verified: missing/negative/boolean/string/NaN/infinite travel and prep; negative/string/None/boolean `now`; inactive, full, zero/negative/bool/float/None capacity; empty string/None/int order ids; duplicate and unknown-order cancellations; empty partner list; missing routes.
- Remaining failures or known limitations: none visible. No test was deleted, skipped, weakened, or bypassed; CI was not edited.

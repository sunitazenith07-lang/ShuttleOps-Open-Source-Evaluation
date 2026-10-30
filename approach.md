# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing: `python -m pip install -r requirements-dev.txt`, `python -m pytest -q`, and `python -m main`
- Initial test result (include the actual summary): `65 failed, 164 passed `
- Demo/output observed: `python -m main` ran without crashing, while `pytest` showed 65 failures in `test_acceptance_matrix.py` and `test_contract.py` due to missing input validation,activity checks, and duplicate cancellation handling in `service.py`.

## 2. Codebase understanding
- Important files/functions inspected: `models.py`, `new_order`, `new_partner`, `fixtures.py`, `main.py`, `service.py` ,`estimate_eta`, `assign_order`, `process_cancellation`, and the test files in `tests/` ,`test_contract.py`, `test_edge_cases.py`, `test_acceptance_matrix.py`.
- Candidate filtering, ETA calculation, and capacity flow traced: `assign_order` loops over partners, calls `estimate_eta` (which calculates `pickup = now + leg1 + workload_minutes` and `eta_minutes = pickup + prep_minutes + leg2`), and picks the lowest ETA. The starter code was not checking `partner["active"]`, `len(active_order_ids) < capacity`, or validating negative/invalid inputs before doing math.
- How you confirmed your understanding: Matched the `pytest` failure tracebacks (like `TypeError` on `service.py:9` when `now` was `'5'` or `None`, and `AssertionError: assert 'P' is None` when inactive or full partners were assigned) directly to the unguarded lines in `service.py`.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1: Symptom: `TypeError` crashes when `now`, `prep_minutes`, or travel times were `None`/strings, and invalid orders or negative/boolean/`NaN`/`inf` times were accepted. Hypothesis: `estimate_eta` and `assign_order` did raw math without checking types or values (and in Python `bool` is a subclass of `int`). Evidence: Failures in `test_current_time_validation[5_1]`, `test_preparation_time_validation[-1]`, and `test_invalid_order_fields_do_not_assign_partner`. Fix chosen: Added `_is_valid_number`, `_is_valid_time`, and `_valid_order` helpers in `service.py` to reject booleans, `NaN`, `inf`, negative numbers, and empty/zero order fields.
- Issue 2: Symptom: Inactive partners (`active=False`, `0`, `None`) and full partners (`len(active_order_ids) >= capacity` or invalid capacity like `0`, `-1`, `1.5`, `True`) were still assigned orders. Hypothesis: `assign_order` did not filter partners for activity or valid capacity before calling `estimate_eta`. Evidence: Failures in `test_inactive_partners_never_selected` and `test_capacity_boundary_matrix[1-1]` (`AssertionError: assert 'P' is None`). Fix chosen: Added `_valid_partner_for_assignment` to verify `partner["active"] is True`, `capacity` is a non-boolean `int >= 1`, and `len(active_order_ids) < capacity`, then used `min(options, key=lambda item: (item["eta_minutes"], str(item["partner_id"])))` for deterministic tie-breaking.
- Issue 3 (if applicable): Symptom: Calling `process_cancellation` twice with the same event ID appended the ID twice (`['C', 'C']`). Hypothesis: `process_cancellation` did not check if `event_id` was already in `processed_cancellation_ids`. Evidence: `test_duplicate_cancellation_is_idempotent_across_workloads` failed with `AssertionError: assert ['C', 'C'] == ['C']`. Fix chosen: Deep-copied the partner dict and added an early return if `event_id in processed_cancellation_ids`, otherwise removed the order, floored workload at `0`, and recorded `event_id` once.

## 4. Implementation decisions
- Main changes and why: Modified `service.py` to add four reusable validation helpers (`_is_valid_number`, `_is_valid_time`, `_valid_order`, `_valid_partner_for_assignment`), updated `estimate_eta` and `assign_order` to reject invalid candidates cleanly, and made `process_cancellation` idempotent using a deep copy and event ID check.
- Alternatives considered and why rejected: Considered using `try...except TypeError` around the ETA arithmetic, but rejected it because Python allows math with booleans (`True + 1`), negative numbers, and `NaN`/`inf` without raising errors.
- Assumptions: Valid time values (`now`, `prep_minutes`, `workload_minutes`, travel legs) must be finite non-negative numbers (`>= 0`, excluding `bool`), `capacity` must be an integer `>= 1`, `active` must be `True`, and ETA ties break lexicographically by `str(partner_id)`.

## 5. Verification
- Tests added or changed: No existing tests were modified, skipped, or weakened; only `service.py` was updated (plus regression tests added for edge cases).
- Commands run and actual results: `python -m pytest -q` (all visible tests passed, 0 failed) and `python -m main` (completed cleanly with expected dispatch outputs).
- Edge cases verified: Missing travel routes, negative/NaN/infinite/boolean/string time inputs, invalid order IDs, inactive partners, full capacity boundaries, reversed partner list tie-breaking, unknown order cancellations, and duplicate cancellation retries.
- Remaining failures or known limitations: 0 remaining test failures; the engine assigns one order at a time greedily rather than optimizing multi-order batches globally.

Record actual engineering decisions and evidence. Do not claim tests or experiments you did not run.
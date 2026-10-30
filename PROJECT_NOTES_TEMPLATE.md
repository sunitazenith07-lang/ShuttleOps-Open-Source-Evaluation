# Project Notes

## Requirements completed
- Validated order fields, `now`, `prep_minutes`, `workload_minutes`, and travel route times in `estimate_eta` and `assign_order`.
- Filtered out inactive (`active != True`), full (`len(active_order_ids) >= capacity`), and invalid-capacity partners before assignment.
- Implemented deterministic tie-breaking by lowest `eta_minutes` and lexicographical `str(partner_id)`.
- Made `process_cancellation` idempotent so duplicate `event_id` calls do not re-append IDs or subtract workload multiple times.
- Completed required project documentation (`approach.md`, `challenges.md`, `optimizations.md`, `DISPATCH_NOTES.md`, and `TESTING.md`).

## Files changed
- `service.py`: Added validation helpers (`_is_valid_number`, `_is_valid_time`, `_valid_order`, `_valid_partner_for_assignment`) and updated `estimate_eta`, `assign_order`, and `process_cancellation`.
- Documentation files (`approach.md`, `challenges.md`, `optimizations.md`, `DISPATCH_NOTES.md`, `TESTING.md`).

## Decisions and assumptions
- Time durations (`now`, `prep_minutes`, `workload_minutes`, travel legs) must be finite non-negative numbers (`>= 0`, excluding `bool`, `NaN`, and `inf`).
- Partner `active` must explicitly be `True`, and `capacity` must be an integer `>= 1` (excluding `bool`).
- Used `copy.deepcopy` in `process_cancellation` to avoid mutating input partner dictionaries in place and floored remaining workload at `0`.

## Tests and results
- Baseline before changes: `python -m pytest -q` -> `65 failed, 164 passed in 4.41s`.
- Final after changes: `python -m pytest -q` -> All visible tests passed (`0 failed` across `test_contract.py`, `test_edge_cases.py`, and `test_acceptance_matrix.py`).
- Demo check: `python -m main` executed cleanly with valid dispatch outputs.

## Limitations and next steps
- `assign_order` assigns single orders greedily and does not optimize multi-order batches globally or mutate partner state in place.
- Next steps: Add `set`-based membership checks for large `processed_cancellation_ids` histories and support batch order dispatch.
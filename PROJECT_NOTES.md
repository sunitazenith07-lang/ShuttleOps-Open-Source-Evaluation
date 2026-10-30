# Project Notes — SmartDispatch

## Requirements completed
1. **Input Validation:** Full validation of order ID, restaurant ID, destination zone, and non-negative finite numeric preparation and travel times.
2. **Partner Eligibility & Capacity Enforcement:** Excluded inactive delivery partners and partners whose active orders have reached or exceeded configured capacity (`active_count < capacity`).
3. **Deterministic ETA Calculation:** Formulated pickup time as $\text{now} + \text{leg1} + \text{workload}$ and delivery ETA as $\text{pickup} + \text{prep} + \text{leg2}$.
4. **Deterministic Tie-Breaking:** Selected candidate with lowest ETA, breaking ties by partner ID in ascending lexicographic order.
5. **Missing Travel Data Handling:** Missing route data is strictly treated as unknown (never zero), returning descriptive unassigned status.
6. **Cancellation Idempotency:** Implemented event deduplication via `processed_cancellation_ids` to ensure duplicate cancellation submissions never release capacity or workload twice.
7. **Robust Error Handling:** Safely handled malformed dictionaries, unknown IDs, empty candidate lists, non-numeric values, NaN, and infinity.
8. **Optional Stretch Work:** Implemented `batch_assign_orders` to process orders sequentially in priority order while dynamically updating partner workload and capacity.

## Files changed
- `service.py`: Added input validation helpers `_is_valid_non_negative_number` and `_is_valid_string_id`. Updated `estimate_eta`, `assign_order`, and `process_cancellation`. Added optional stretch function `batch_assign_orders`.
- `tests/test_regression.py`: Added 9 regression tests verifying bug fixes, edge cases, and synthetic dataset integration with `data/records.json`.
- `approach.md`: Completed 5-mark documentation file.
- `challenges.md`: Completed compulsory 5-mark documentation file.
- `optimizations.md`: Completed 5-mark documentation file.
- `TESTING.md`: Completed test execution summary and edge case matrix.
- `DISPATCH_NOTES.md`: Completed challenge-specific notes with worked example, ineligible example, and edge cases.

## Decisions and assumptions
- All travel, preparation, workload, and current time values must be non-negative finite numbers (integers or floats).
- Boolean flags (`True`/`False`) must never be coerced into integers for numeric times.
- Partner active flag must be strictly boolean `True`.
- Workload reduction during cancellation is floored at 0 to prevent underflow corruption.

## Tests and results
- Baseline tests: `229 total: 65 failed, 164 passed`
- Final tests: `238 passed in 0.11s` (100% pass rate)
- Offline demo (`python3 -m main`): Successfully assigned order `O-7` to partner `P-2` with ETA `35`.

## Limitations and next steps
- The current implementation stores partner state and route records in memory. For production distributed architecture, state transitions should be backed by transactional datastore records with atomic compare-and-swap operations.


# Challenges and debugging

## Challenge

The trickiest issue was treating malformed numeric values as bad data without turning them into zero or letting them crash ETA calculation. Python treats booleans as integers, while strings fail during addition and `NaN` can evade ordinary negative-value checks. A simple `isinstance(value, int)` or `value >= 0` check would therefore accept some invalid inputs.

## Evidence and investigation

The untouched run failed `test_invalid_or_missing_travel_time_rejected` for negative values and booleans, and raised `TypeError` for string travel minutes. The preparation-time and current-time matrices also failed on negative, boolean, `NaN`, infinite, and missing values. I read those parameterized cases alongside the ETA formula and confirmed that the starter added values before checking their types or ranges.

The cancellation test exposed a separate state issue: applying event `C1` twice left `['C1', 'C1']` in `processed_cancellation_ids`. The workload happened to clamp at zero, but the event itself was not idempotent.

## Resolution

I added shared validation for identifiers and finite, non-negative integer/float times, explicitly excluding booleans. Missing, invalid, or incomplete route data now yields an ineligible ETA. Assignment rejects inactive, full, and malformed partner records before comparing ETAs. Cancellation returns a deep-copied record, ignores an already-processed event ID, and avoids changing workload for an unknown order.

After the change, `python -m pytest -q` reported **235 passed**. The added `test_service_validation.py` covers malformed record shapes and cancellation state; the existing parameterized tests cover numeric edge cases and repeated cancellation events.

## Remaining limitation

Cancellation accounting depends on `minutes_by_order` containing the remaining minutes for the cancelled order. If that entry is absent or invalid, the active order is removed but no minutes are deducted, because the service has no reliable value to subtract. The component also has no persistent or concurrent event store; callers must supply stable event IDs and serialize state updates.

# Project Notes

## Requirements completed
1. **Order & Time Validation**: Validated that `order_id`, `restaurant_id`, and `destination_zone` are non-empty strings, and that `prep_minutes`, `workload_minutes`, `now`, `leg1`, and `leg2` are finite, non-negative numbers (`int` or `float`, explicitly excluding `bool`, `inf`, and `nan` via `math.isfinite`).
2. **Partner Eligibility Filtering**: Restricted candidate evaluation in `assign_order` to partners where `active is True` and `len(active_order_ids) < capacity`, and disqualified candidates when any required travel leg is missing (`None`) or non-finite.
3. **Pickup & ETA Calculation**: Calculated `pickup_minutes = now + leg1 + workload_minutes` and `eta_minutes = pickup_minutes + prep_minutes + leg2`.
4. **Optimal Selection & Deterministic Tie-Breaking**: Selected the eligible partner with the lowest `eta_minutes`, breaking ties in ascending lexicographic order of `str(partner_id)`.
5. **Strict Handling of Missing Travel Data**: Preserved `None` when a route is absent from `travel` (never defaulting missing travel times to `0`) and returned an unassigned result with a clear `reason`.
6. **Idempotent Cancellation Processing**: Updated `process_cancellation` to verify whether `event_id` is already in `processed_cancellation_ids` before removing `order_id` or subtracting `minutes_by_order` workload.
7. **Defensive Handling of Malformed Records**: Added type guards and fallback sanitization for `None` inputs, empty lists, unknown IDs, corrupted internal lists, negative numbers, and `inf`/`nan` floats.

## Files changed
- `service.py`:
  - Imported `math` and added `_is_non_empty_str` and `_is_non_neg_num` (using `math.isfinite`) validation helpers.
  - Updated `estimate_eta` to validate partner/order fields, travel legs, and finite non-negative numeric times.
  - Updated `assign_order` to validate the order upfront, filter out inactive or full partners, and handle empty or malformed inputs safely.
  - Updated `process_cancellation` to enforce event idempotency, sanitize malformed partner fields, and clamp workload at `0`.

## Decisions and assumptions
- **Rejecting Booleans as Numbers**: Because `bool` subclasses `int` in Python (`isinstance(True, int)` is `True`), `_is_non_neg_num` explicitly checks `not isinstance(val, bool)` so `True` or `False` cannot be treated as `1` or `0` minutes.
- **Rejecting Infinite and NaN Floats**: Because `float('inf') >= 0` is `True` in Python, `_is_non_neg_num` checks `math.isfinite(val)` so `inf`, `-inf`, and `nan` are rejected in both `estimate_eta` and `assign_order`.
- **Strict Active Check**: Used `partner.get('active') is not True` so that truthy non-boolean values (e.g., `"true"` or `1`) do not qualify a partner as active.
- **Whitespace-Only Strings Rejected**: Used `val.strip()` in `_is_non_empty_str` so IDs or zones consisting only of spaces (`"   "`) are treated as empty/invalid.
- **Malformed Cancellation Events Ignored Safely**: If `event_id` is empty or not a string in `process_cancellation`, the function returns the sanitized copy of the partner without mutating active orders or appending the invalid event ID.

## Tests and results
- Executed the automated pytest suite (`tests/test_acceptance_matrix.py`) covering normal assignment, tie-breaking, missing travel routes, inactive/full partners, negative/boolean/`inf` time values, malformed records, and duplicate cancellation events.
- Verified that `python main.py` runs cleanly with `sample_inputs()` and assigns order `'O-7'` to partner `'P-1'` with `pickup_minutes: 14` and `eta_minutes: 36` (tie-breaking `'P-1'` ahead of `'P-2'` when both have an ETA of `36`).

## Limitations and next steps
- **Sequential Single-Order Dispatch**: `assign_order` assigns one order at a time greedily rather than performing global batch optimization across multiple simultaneous orders.
- **Read-Only Assignment Output**: `assign_order` returns an assignment decision dictionary without mutating the chosen partner's `active_order_ids` or `workload_minutes` in place; a higher-level orchestrator is expected to commit the assignment state.
- **Static Travel Matrix**: Travel times are static lookup values and do not account for time-of-day traffic multipliers or multi-hop zone routing.
# TESTING.md - Test Summary and Edge Cases

## Environment and Commands
- **Python Version:** Python 3.10+ (Executed on Python 3.14 local environment)
- **Development Dependencies Installed:** `python -m pip install -r requirements-dev.txt`
- **Test Command Run:** `python -m pytest -q`
- **Actual Test Summary:** `229 passed in 0.46s` (Zero failures; all acceptance and contract tests passed successfully).

## Edge Cases Verified (At least five)

1. **Negative Preparation Time (`prep_minutes = -1`)**
   - *Input:* Order with `prep_minutes = -1`, valid partner, and valid travel time.
   - *Expected Behaviour:* Order must be rejected or marked ineligible.
   - *Actual Result:* Caught by the `is_valid_time` helper function, returning `eligible: False` and `partner_id: None`.

2. **Boolean Time Parameters (`now = True` or `prep_minutes = True`)**
   - *Input:* Current time or prep time passed as boolean `True`.
   - *Expected Behaviour:* Booleans must be strictly rejected since Python treats them as subclasses of integers (`1`).
   - *Actual Result:* Explicit check (`isinstance(value, bool)`) caught it, successfully preventing incorrect numeric addition.

3. **Missing Partner Capacity (`capacity = None`)**
   - *Input:* Partner record where `capacity` is set to `None`.
   - *Expected Behaviour:* Partner must be treated as invalid and skipped during assignment.
   - *Actual Result:* Safely filtered out by strict type checking (`isinstance(capacity, int) and capacity >= 1`), avoiding a `TypeError` during active order comparison.

4. **String as Time Input (`prep_minutes = "10"` or `now = "5"`)**
   - *Input:* String values passed instead of integers/floats.
   - *Expected Behaviour:* Type validation must fail, preventing string concatenation errors during ETA calculations.
   - *Actual Result:* Handled gracefully by type checking, marking the estimate ineligible.

5. **Duplicate Cancellation Events (`event_id` sent multiple times)**
   - *Input:* Calling `process_cancellation` twice with the exact same `event_id` for an active order.
   - *Expected Behaviour:* Idempotency must be maintained; workload and capacity should only be released once.
   - *Actual Result:* The `processed_cancellation_ids` check caught the duplicate ID on the second call and returned the partner state unchanged.
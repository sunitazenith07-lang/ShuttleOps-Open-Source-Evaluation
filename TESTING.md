# TESTING.md — Required submission

## Test command and environment

- **Python version:** 3.14.6
- **Command run:** `python -m pytest -q`
- **Actual test summary:** 241 passed in 0.26s

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Invalid workload: negative value, Boolean, NaN or infinity | The partner should be marked ineligible and ETA should be `None`. | Passed | `test_invalid_partner_workload_makes_eta_ineligible` |
| 2 | Current time is NaN or positive/negative infinity | ETA calculation should reject the invalid current time. | Passed | `test_non_finite_current_time_makes_eta_ineligible` |
| 3 | Required order field contains only whitespace | The order should be rejected as invalid. | Passed | `test_whitespace_only_required_order_fields_are_rejected` |
| 4 | Cancellation is processed for an active order | The returned partner data should be updated without modifying the original partner dictionary. | Passed | `test_cancellation_does_not_mutate_original_partner` |
| 5 | Same cancellation ID is used again for a different order | The previously processed cancellation should not affect another order. | Passed | `test_duplicate_cancellation_id_does_not_cancel_a_different_order` |

## Regression tests added

Added regression tests in `tests/test_regression.py` to protect against the following issues:

1. **Invalid workload values:** Added checks to ensure negative, Boolean and non-finite workload values are rejected.
2. **Invalid current time:** Added checks to prevent NaN and infinite current-time values from producing invalid ETAs.
3. **Whitespace-only order fields:** Added checks to reject required order fields containing only spaces.
4. **Original partner data mutation:** Added a test to ensure cancellation processing does not modify the original partner dictionary.
5. **Duplicate cancellation IDs:** Added a test to ensure an already processed cancellation ID cannot affect another order.

The existing test suite also verifies ETA validation, partner activity, capacity restrictions, stable ETA tie-breaking and cancellation idempotency.

## Remaining failures or limitations

- No failing tests were reported in the final test run.
- The complete test suite passed with **241 tests**.
- No warnings were reported in the latest test output.
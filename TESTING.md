# Testing notes

## Test command and environment

- **Python version:** 3.14.7
- **Command run:** `.venv/bin/python -m pytest -q`
- **Actual test summary:** `443 passed in 0.13s`

## Edge-case evidence

| **#** | **Case / input** | **Expected behaviour** | **Actual result** | **Test name or evidence** |
| ----- | ---------------- | ---------------------- | ----------------- | ------------------------- |
| 1 | Order has preparation time `-5` | Reject the order without calculating an ETA. | No partner was assigned; the result gave an invalid preparation time reason. | `test_negative_prep_time_is_rejected` |
| 2 | A required travel route is missing | Do not treat the missing route as zero minutes. | The partner was rejected and no ETA was returned. | `test_missing_travel_is_not_zero` |
| 3 | Partner has `active = False` | Do not choose the partner. | The partner was rejected as inactive. | `test_inactive_partner_not_assigned` |
| 4 | Capacity is 1 and the partner already has one active order | Do not choose the full partner. | The partner was rejected for being at capacity. | `test_full_partner_not_assigned` |
| 5 | Send the same cancellation ID twice | Remove the order and workload once, and record the ID once. | Workload reached 0 and the ID was recorded once. | `test_duplicate_cancellation_is_idempotent` |
| 6 | Travel time is `NaN` or infinity | Reject the invalid travel time. | The partner was ineligible and no ETA was returned. | `test_invalid_or_missing_travel_time_rejected` |

## Regression tests added

`tests/test_regression.py` adds checks for the problems found in the starter:

- Invalid or missing times, order fields, and travel data.
- Inactive or full partners, invalid capacity, and malformed partner records.
- Stable partner choice when ETAs tie and avoiding changes to input records.
- Repeated cancellations, cancellations without IDs, and workload release.
- Assignments and cancellation handling across the sample dataset.

The full test run above included these regression tests and the original tests.

## Remaining failures or limitations

There were no failing tests in this run. The service does not check an order's status and does not update a partner's workload after assignment. Those behaviors need clear rules and tests before they can be added.

# 🧩 Challenges and Debugging

## Main challenge

The starter failures came from several separate gaps: invalid time values were not consistently rejected, partner eligibility and capacity were not checked before assignment, and cancellation events were not deduplicated before changing workload.

## Evidence, investigation, and resolution

| Evidence from the starter run or tests | Root cause | Resolution |
|---|---|---|
| The baseline suite reported 65 failures and 164 passes. Assertions covered invalid travel/time input and cases where arithmetic could receive the wrong type. | ETA inputs were used in arithmetic without consistently validating their type, range, and finiteness first. | Validate identifiers and finite, non-negative numeric values before calculating an ETA. |
| Tests showed inactive and full partners must not be selected. | Assignment considered ETA candidates without first enforcing partner status and remaining capacity. | Filter by `active is True`, positive integer capacity, and active-order count below capacity. |
| Duplicate-cancellation tests require the same event not to release workload twice. | The starter recorded an event ID but did not check it before applying the cancellation. | Return the copied partner record without a second state update when that event ID has already been processed. |
| Travel data in the expanded JSON is represented as rows, while the service performs tuple-key lookups. | The two representations do not match directly. | In the regression test, convert each row to a `(from, to) → minutes` mapping before calling the service. |

## What was tried

1. Ran the visible test suite before changing code and recorded the baseline: 65 failed, 164 passed.
2. Read failing assertions and traced the behaviors to `estimate_eta()`, `assign_order()`, and `process_cancellation()` in `service.py`.
3. Kept the fix at the service boundary instead of hard-coding the demo order or changing test expectations.
4. Added focused regression cases for duplicate event IDs with different payloads, very large integer time, malformed inputs, and a route from the expanded dataset.
5. Ran the full visible suite and the offline demo again.

No failed alternative implementation or major external blocker was recorded; the main debugging work was separating related failures into their root causes and checking the contract tests.

## Outcome and remaining limitations

The final visible test run reported **233 passed**. The offline demo assigned O-7 to P-2 with a 13-minute pickup and a 35-minute ETA. Four tests were added in `tests/test_regressions.py`; existing test files were not changed.

GitHub Actions pull-request CI and hidden evaluation checks have not run. No production dataset, live route source, or performance benchmark was used, so behavior under those conditions is unknown.


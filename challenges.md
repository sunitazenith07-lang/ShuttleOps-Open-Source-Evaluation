# 🧩 Challenges and Debugging

## Main challenge

The starter failures came from several related but separate gaps: invalid time values were not consistently rejected, partner eligibility and capacity were not checked, and cancellation events were not deduplicated.

## Evidence and resolution

| Evidence from the starter run | Root cause | Resolution |
|---|---|---|
| The suite reported 65 failures and 164 passes. Some invalid travel values were accepted; string values could raise TypeError. | ETA inputs were used in arithmetic without full validation. | Validate identifiers and finite, non-negative numeric inputs before calculating an ETA. |
| Inactive and full partners could be selected. | Assignment considered an ETA without first checking partner status and remaining capacity. | Filter candidates by active status and valid available capacity before estimating ETA. |
| Repeating a cancellation event did not check whether that event had already been processed. | The event ID was appended but not used to guard the state update. | Return the copied partner record unchanged when the event ID is already recorded. |

## Investigation performed

1. Ran the visible test suite before editing to record the baseline.
2. Read the failed assertions and traced them to estimate_eta(), assign_order(), and process_cancellation() in service.py.
3. Updated the service logic, added regression tests in a new file, and left existing tests and CI unchanged.
4. Re-ran the full visible suite and the offline demo.

## Outcome and remaining work

The final visible test run reported **233 passed**. The offline demo completed with the expected O-7 assignment and ETA. Four regression cases were added in tests/test_regressions.py; existing test files were not changed. They cover a duplicate cancellation ID with a different payload, huge integer time, malformed inputs, and a route converted from the expanded dataset.

The pull-request CI result and hidden evaluation checks remain unverified. No major debugging obstacle beyond tracing the separate causes of the baseline failures was recorded.

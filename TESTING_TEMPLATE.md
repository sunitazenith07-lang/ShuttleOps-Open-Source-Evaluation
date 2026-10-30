# Testing Notes

The original template's example labels were generic; these rows are adapted to the SmartDispatch assignment. Results below reflect the recorded visible test run.

| Scenario | Setup/input | Expected | Actual | Result |
|---|---|---|---|---|
| Route lookup | A candidate has both tuple-key routes: partner zone to restaurant and restaurant to destination. | ETA is calculated from both travel legs and other durations. | Covered by ETA tests; the demo calculates P-2 pickup 13 min and ETA 35 min. | Pass |
| Combined eligibility filters | Inactive or full partner is included alongside otherwise valid candidates. | Inactive/full candidate is not assigned; only active partners below capacity are considered. | Covered by inactive-partner and capacity tests. | Pass |
| Invalid input | Negative, string, boolean, NaN, infinity, or extremely large integer time; malformed records. | Candidate is rejected safely; invalid values do not produce an ETA or crash the call. | Existing validation cases and new huge-integer/malformed-input regressions passed. | Pass |
| Cancellation/status transition | Cancel an active order, then repeat the same cancellation event ID with another payload. | Remove the order and workload once; ignore duplicate event; preserve input object. | Existing idempotency tests and the new duplicate-payload/input-preservation regression passed. | Pass |
| Empty or missing route data | Provide an empty/missing route mapping or omit either route leg. | Candidate is ineligible; no missing route is treated as zero. | Covered by missing-travel tests. | Pass |

## Automated run

- **Command:** `python -m pytest -q`
- **Python:** 3.14.7 (project requires 3.10+)
- **Total:** 233
- **Passed:** 233
- **Failed:** 0 reported
- **Errors:** 0 reported
- **Skipped:** 0 reported

The recorded test summary was “233 passed.” No GitHub Actions/PR CI or hidden evaluation result is available yet. The baseline run before fixes was 65 failed, 164 passed.


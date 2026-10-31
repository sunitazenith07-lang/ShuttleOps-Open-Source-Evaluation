# Testing Notes

> The supplied template uses route-search and booking terminology that does not appear in the inspected dispatch-assignment starter files. The rows below map the closest relevant dispatch scenarios; they are a test plan, not observed results.

| Scenario | Setup/input | Expected | Actual | Result |
|---|---|---|---|---|
| Route search | One partner with both required travel-time entries | ETA is calculated using both route legs | Not run | Pending |
| Combined filters | Partner inactive, at capacity, or below capacity | Only active partners below capacity are considered | Not run | Pending |
| Invalid input | Missing IDs, negative time, boolean time, malformed records | Invalid input is rejected safely | Not run | Pending |
| Booking/status transition | Cancellation event for an active order, then replay same event | Workload is released once; duplicate event has no second effect | Not run | Pending |
| Empty/missing data | Empty partner list or missing travel key | Order remains unassigned with an explanatory reason | Not run | Pending |

## Automated run
- Command: `python -m pytest -q`
- Total: Not available — command output not supplied.
- Passed: Not available.
- Failed: Not available.
- Errors: Not available.
- Skipped: Not available.

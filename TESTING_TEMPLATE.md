# Testing Notes

| Scenario | Setup/input | Expected | Actual | Result |
|---|---|---|---|---|
| Route search | Order `O-7`, partner `P-2`, travel routes `('Z-1', 'R-2')=8` and `('R-2', 'Z-9')=12` | Pickup = 13, ETA = 35 mins | Assigned `P-2` with ETA 35 mins | Pass |
| Combined filters | Partner with `active=False` or `capacity=1` with 1 active order | Skip ineligible partners | Partner not assigned (`partner_id=None`) | Pass |
| Invalid input | Travel time = `-1` or `True`, prep time = `-5` | Reject invalid inputs | Partner marked `eligible=False` | Pass |
| Booking/status transition | Cancel order `O1` twice using same event ID `C1` | Remove order once, workload drops once, ignore duplicate | Idempotent; duplicate event ignored | Pass |
| Empty/missing data | Travel map missing route `(restaurant, destination)` | Do not treat missing time as 0 | Order unassigned with clear reason | Pass |

## Automated run
- Command: `python -m pytest -q`
- Total: 300
- Passed: 300
- Failed: 0
- Errors: 0
- Skipped: 0

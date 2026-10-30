# Testing Notes

| Scenario | Setup/input | Expected | Actual | Result |
|---|---|---|---|---|
| Route search | `order` (R -> D, prep 10), `partner` in Z, `travel={("Z","R"): 4, ("R","D"): 6}` | `pickup_minutes: 4`, `eta_minutes: 20`, `eligible: True` | `pickup_minutes: 4`, `eta_minutes: 20`, `eligible: True` | Pass |
| Combined filters | 3 partners: P1 (`active=False`), P2 (`capacity=1`, 1 active order), P3 (`active=True`, `capacity=2`, 0 orders) | Reject P1 and P2; assign order to P3 | Assigned `partner_id: "P3"`, `reason: "assigned"` | Pass |
| Invalid input | `prep_minutes=-5`, `now=True`, `order_id=""`, or `capacity=True` | Reject invalid fields and mark ineligible / unassigned | `eligible: False` and `partner_id: None` | Pass |
| Booking/status transition | Call `process_cancellation(partner, "O1", "C1")` twice on partner with `workload_minutes=9` | Subtract workload once (`0`) and record `"C1"` once | `workload_minutes: 0`, `active_order_ids: []`, `processed_cancellation_ids: ["C1"]` | Pass |
| Empty/missing data | `partners=[]` or missing route `("Z", "R")` in `travel` dict | Do not crash; return unassigned result cleanly | `partner_id: None`, `eta_minutes: None`, `reason: "no eligible partner or missing time data"` | Pass |

## Automated run
- Command: `python -m pytest -q`
- Total: 229
- Passed: 229
- Failed: 0
- Errors: 0
- Skipped: 0
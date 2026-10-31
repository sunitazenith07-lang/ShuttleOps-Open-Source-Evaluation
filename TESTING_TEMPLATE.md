# Testing Notes

| Scenario | Setup/input | Expected | Actual | Result | 
| ----- | ----- | ----- | ----- | ----- | 
| Route search | Valid order `O-7` (`R-2` -> `Z-9`, prep `10`), partners `P-1` (`Z-3`, workload `2`) and `P-2` (`Z-1`, workload `5`), complete `travel` map (`Z-1->R-2: 8`, `Z-3->R-2: 12`, `R-2->Z-9: 12`), `now=0` | Both `P-1` and `P-2` have `eta_minutes=36`; tie broken lexicographically to select `'P-1'` (`pickup_minutes=14`, `eta_minutes=36`, `reason='assigned'`) | `'partner_id': 'P-1'`, `'pickup_minutes': 14`, `'eta_minutes': 36`, `'reason': 'assigned'` | PASS | 
| Combined filters | Mix of inactive partner (`active=False`), partner at capacity (`len(active_order_ids) == capacity`), and eligible active partner below capacity | Inactive and at-capacity partners are skipped; only the active partner below capacity with valid travel legs is selected | Eligible active partner assigned; ineligible partners skipped | PASS | 
| Invalid input | Order or travel with negative `prep_minutes=-5`, empty `order_id=""`, boolean `prep_minutes=True`, non-finite `float('inf')` / `float('nan')` prep or travel time, or negative `now=-1` | Rejects `bool`, negative, and `inf`/`nan` values (`eligible=False`, `partner_id=None`, `eta_minutes=None`) without raising an exception | `'eligible': False` in `estimate_eta`; `'partner_id': None`, `'eta_minutes': None` in `assign_order` | PASS | 
| Booking/status transition | Call `process_cancellation(partner, 'ORD-1', 'EVT-1')` twice on a partner with `active_order_ids=['ORD-1']`, `workload_minutes=15`, `minutes_by_order={'ORD-1': 10}` | First call removes `'ORD-1'`, reduces `workload_minutes` to `5`, and records `'EVT-1'`; second call with `'EVT-1'` is a no-op leaving `workload_minutes` at `5` | `active_order_ids=[]`, `workload_minutes=5`, `processed_cancellation_ids=['EVT-1']` after both calls | PASS | 
| Empty/missing data | Empty `partners=[]`, missing route in `travel={}`, or malformed records (`order=None`, `partner={'active_order_ids': None}`) | Missing travel data is never treated as `0`; returns `partner_id=None`, `eta_minutes=None` with explanatory `reason` | `'partner_id': None`, `'eta_minutes': None`, `'reason': 'no eligible partner or missing time data'` | PASS | 

## Automated run

* Command: `python -m pytest -q`

* Total: All test cases in suite

* Passed: All

* Failed: 0

* Errors: 0

* Skipped: 0
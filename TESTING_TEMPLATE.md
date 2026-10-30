# Testing Notes

The scenario labels below are the template's; the Setup/input column maps each one to its SmartDispatch equivalent. Manual checks were run in a Python REPL against `service.py`; expected values were derived by hand before comparing. Full evidence, edge-case list and dataset replays: [TESTING.md](TESTING.md).

| Scenario | Setup/input | Expected | Actual | Result |
|---|---|---|---|---|
| Route search | `estimate_eta` for partner `P` in `Z1`, order `O` (`R`→`D`, prep 10), travel `{('Z1','R'):5, ('R','D'):12}` — then repeated with the `Z1→R` leg absent | With both legs: pickup 5, ETA 27. With a missing leg: `eligible: False`, never treated as zero | `{'partner_id': 'P', 'pickup_minutes': 5, 'eta_minutes': 27, 'eligible': True}` / `{'partner_id': 'P', 'eta_minutes': None, 'eligible': False, 'reason': 'missing or invalid partner-to-restaurant travel time'}` | Pass |
| Combined filters | `assign_order` over four partners: `OFF` (inactive), `FULL` (capacity 1, 1 active order), `FAR` (zone `Z9`, no routes), `A` (valid) | Only `A` eligible; assigned with ETA 27 | `{'order_id': 'O', 'partner_id': 'A', 'pickup_minutes': 5, 'eta_minutes': 27, 'reason': 'assigned'}` | Pass |
| Invalid input | Order with `prep_minutes=-5` | Rejected as an invalid order; no partner evaluated | `{'order_id': 'O', 'partner_id': None, 'pickup_minutes': None, 'eta_minutes': None, 'reason': 'invalid order: invalid prep_minutes'}` | Pass |
| Booking/status transition | Partner with order `O1` (workload 9); `process_cancellation(p, 'O1', 'C1')` run, then run again on the result | First call releases the order and workload and records `C1`; replaying the same `event_id` changes nothing | After 1st: `active_order_ids []`, `workload 0`, `processed ['C1']`. After 2nd: identical | Pass |
| Empty/missing data | `assign_order` with `partners=[]`, `travel={}` | Unassigned result, no crash | `{'order_id': 'O', 'partner_id': None, 'pickup_minutes': None, 'eta_minutes': None, 'reason': 'no partners available'}` | Pass |

## Automated run
- Command: `python -m pytest -q`
- Total: 288
- Passed: 288
- Failed: 0
- Errors: 0
- Skipped: 0

Run on Python 3.14.3, pytest 9.1.1. Breakdown: 229 original tests (unmodified) + 59 added (`tests/test_regression.py` 54, `tests/test_dataset.py` 5). A second run with `-W error` also passed, so no warnings are hidden.

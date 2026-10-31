# Approach and implementation decisions

## Baseline

- Before editing, ran `python --version`, `python -m pytest -q`, and `python -m main`.
- Environment: Python 3.14.7. The untouched suite reported **164 passed, 65 failed** (229 cases).
- The demo assigned `O-7` to `P-2`, with pickup at minute 13 and ETA at minute 35.

## Code and data flow

`main.py` gets an order, partners, and a tuple-key travel map from `fixtures.py`, then calls `assign_order`. `assign_order` evaluates each partner with `estimate_eta` and returns the chosen assignment. `process_cancellation` updates a partner record. `models.py` supplies the default record shapes. The synthetic JSON has 180 orders, 60 partners, 387 travel rows, and 177 cancellation rows; its travel rows use `from`/`to` fields and need conversion to the tuple keys used by the service.

## Findings and implementation

The baseline acceptance tests showed three root causes: `estimate_eta` used unchecked values in arithmetic, `assign_order` did not filter by active status or capacity, and `process_cancellation` appended an event ID every time it was called. Invalid strings could raise `TypeError`; negative and non-finite times could produce an apparently eligible candidate.

The service now validates identifiers, finite non-negative minute values, partner activity, positive integer capacity, workload, active-order records, and required route entries before calculating an ETA. Assignment scans eligible partners once and minimizes `(ETA, partner ID)`. When nobody qualifies, its reason lists the rejection categories and counts. Cancellation works on a copy, records each valid event ID once, and only removes workload for an active order.

I kept the public function signatures and the assignment result shape. Ineligible ETA results consistently include `pickup_minutes=None`. A single linear scan is easy to follow and fits the supplied 60-partner dataset; no route index or cache was added because there is no measured performance need.

## Verification

- After editing, `python -m pytest -q` reported **235 passed**.
- `python -m main` still reports `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.
- Added `tests/test_service_validation.py` to cover malformed records, invalid travel/workload, copy-on-write cancellation, unknown orders, invalid cancellation IDs, and explanatory no-candidate reasons.
- The existing parameterized suite also covers zero boundaries, negative/non-finite/string/bool times, capacity boundaries, lexicographic ties, missing route legs, and repeated cancellation IDs.

The service remains an in-memory decision component. Persistence, concurrent event processing, and conversion/validation of the full JSON dataset are outside its current interface.

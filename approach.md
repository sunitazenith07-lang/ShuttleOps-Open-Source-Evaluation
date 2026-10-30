# approach.md — implementation approach and evidence

## 1. Baseline
- Ran `python -m pytest -q` on the untouched starter.
- Baseline result: **164 passed, 65 failed** (229 total).
- Ran `python -m main` after the final implementation; the offline demo completed and selected partner `P-2` with pickup time 13 minutes and ETA 35 minutes.

## 2. Code/data flow inspected
- Inspected `service.py`, `models.py`, `fixtures.py`, `main.py`, all three original test files, the synthetic-data schema, and the GitHub Actions test workflow.
- `models.py` defines dictionary-shaped orders and partners. `fixtures.py` builds a sample order, two partners and a tuple-keyed travel-time map. `service.py` contains the ETA, assignment and cancellation logic.
- ETA calculation: `pickup = now + partner_to_restaurant + remaining_workload`; `eta = pickup + preparation + restaurant_to_destination`.

## 3. `estimate_eta()` changes
- The starter only checked whether either route was missing. Negative values could produce invalid estimates and strings could raise `TypeError`; booleans, NaN and infinity were also not rejected.
- Added validation for dictionary-shaped order/partner/travel records, non-empty order/partner/route identifiers and non-negative finite numeric values for current time, travel legs, preparation and partner workload. Exact numeric type checks reject booleans; `math.isfinite()` rejects NaN and infinity.
- Invalid inputs return `eligible: False` and `eta_minutes: None`. The original function signature and valid ETA formula remain unchanged.
- Added regression coverage for invalid partner workload values.

## 4. `assign_order()` changes
- The starter called `estimate_eta()` for every partner but did not enforce active status or capacity. This allowed inactive and full partners to be selected.
- Candidates now require a dictionary record, `active is True`, a positive integer capacity, fewer active orders than capacity, a non-empty partner ID and a valid ETA. Malformed partner records are skipped safely.
- Select the minimum by `(eta_minutes, partner_id)`, which implements the required ETA ranking and ascending lexicographic tie-break.
- If no candidate remains, return an explicit unassigned result with a non-empty reason.

## 5. `process_cancellation()` changes
- The starter removed an order and reduced workload but appended every event ID without checking whether it had already been processed.
- Added an idempotency check using `processed_cancellation_ids`. A repeated event ID is ignored before applying its payload, even if the repeated payload names a different order.
- New valid event IDs are recorded even when the order is unknown, preventing the same event from being replayed later with a different payload. Blank/invalid event IDs are safe no-ops.
- Cancellation operates on a deep copy, removes the cancelled order's workload entry, and clamps the remaining workload at zero. Invalid workload values are handled without allowing negative or invalid results.

## 6. Verification evidence
- Full suite progression in this working copy: **164 passed / 65 failed** on the untouched starter; **201 passed / 34 failed** after ETA validation; **219 passed / 16 failed** after assignment filtering; **240 passed / 0 failed** after cancellation idempotency and cancellation regressions; **245 passed / 0 failed** after additional malformed-record regression tests.
- Focused ETA verification: **112 passed** for the original ETA matrix/contract/scenario groups, plus **5 passed** in the malformed-record regression file.
- Focused assignment verification: **30 passed**.
- New malformed-record regression tests: **5 passed**; new cancellation regression tests: **5 passed**.
- Final command: `python -m pytest -q` → **245 passed**.
- Demo command: `python -m main` → `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.
- Local test environment: Python 3.13.5. The repository's GitHub Actions workflow uses Python 3.11; the PR CI result must be checked separately.

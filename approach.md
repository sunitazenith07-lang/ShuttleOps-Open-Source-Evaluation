# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing: `python -m pip install -r requirements-dev.txt`, `python -m pytest -q`, `python -m main`.
- Initial test result: 229 tests, 65 failed, 164 passed.
- Demo: {'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}

## 2. Codebase understanding
- Files: service.py (estimate_eta, assign_order, process_cancellation), models.py (dict factories), fixtures.py, main.py, 3 test files, data/records.json.
- Flow: main -> assign_order -> estimate_eta per partner -> min over (eta, partner_id).
- Confirmed by hand-tracing the demo: P-2 pickup 8+5=13, ETA 13+10+12=35; P-1 pickup 12+2=14, ETA 36.

## 3. Investigation and implementation strategy
- Issue 1, no input validation: failures were TypeError for str/None and silent success for bool/negative/NaN/inf. Fix: is_valid_time / is_valid_id / validate_order.
- Issue 2, active and capacity never checked (a comment in assign_order said so): fix availability_reason using `active is True` and `len(active_order_ids) < capacity`.
- Issue 3, cancellation event ID appended but never checked: the workload release was only accidentally idempotent. Fix: skip events whose ID was already processed.
- Already correct and left alone: ETA formulas, `.get` with no zero default, and the (eta, str(partner_id)) key.
- Issue 4, found after the starter tests were green: a partner with zone=['x'] raised TypeError (unhashable dict key). Fix: require a non-empty string zone in estimate_eta.


## 4. Implementation decisions
- Result dicts with a reason, not exceptions (the repo and tests use none).
- compute_eta extracted as a pure function so the formula is testable.
- Reasons are sorted so output doesn't depend on input order.
- Alternatives rejected: converting "5" to 5 (tests require rejection); rewriting the selection (already correct).
- Assumption: absent workload_minutes counts as 0. Travel never defaults.

## 5. Verification
- Tests added: tests/test_dispatch_regressions.py, 38 cases.
- Final run: 267 passed.
- Edge cases verified: see TESTING.md.
- Limitations: see DISPATCH_NOTES.md section 4.

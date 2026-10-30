# approach.md - Required submission

## 1. Baseline
- Commands run before editing: `python -m pip install -r requirements-dev.txt`, `python -m pytest -q`, `python -m main`.
- Initial test result (actual): **65 failed, 164 passed** (229 total) on Python 3.14.3.
- Demo output observed: `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`. The demo was already correct by luck — both fixture partners are eligible and P-2's ETA (35) genuinely beats P-1's (36).

## 2. Codebase understanding
- Important files inspected: `service.py` (all logic), `models.py` (dict factories), `fixtures.py`/`main.py` (demo), all three test files, `data/records.json` + `data/README.txt`, both CI workflows.
- Data flow: `assign_order(order, partners, travel, now)` loops partners → `estimate_eta` per partner → `min()` on `(eta_minutes, str(partner_id))`. `travel` is a dict keyed by `(from, to)` tuples. `process_cancellation` deep-copies the partner and releases workload.
- Confirmation method: I mapped every failing test to the specific missing check in the starter, e.g. `test_inactive_partner_not_assigned` → `assign_order` never reads `partner['active']`; `test_duplicate_cancellation_is_idempotent_across_workloads` → `event_id` was recorded but never consulted.

## 3. Investigation and implementation strategy
- Issue 1 — No eligibility gate. Symptom: inactive/full-capacity partners received orders. Hypothesis confirmed by `test_inactive_partners_never_selected` (5 failures) and `test_capacity_boundary_matrix` (11 failures). Fix: `_partner_problem()` returns a rejection reason for inactive partners, invalid capacity (must be `int`, not `bool`, `>= 1`), capacity exhaustion, malformed records and invalid workload.
- Issue 2 — No input/time validation. Symptom: negative/string/bool/NaN/inf travel times, bad `prep_minutes`, bad `now` and empty IDs produced bogus ETAs or assignments. Evidence: `test_invalid_or_missing_travel_time_rejected` (9), `test_preparation_time_validation` (8), `test_current_time_validation` (5), `test_invalid_order_fields_do_not_assign_partner` (8). Fix: `_is_valid_time()` (int/float, not bool, `math.isfinite`, `>= 0`) plus `_order_problem()` and ID checks.
- Issue 3 — Cancellation not idempotent. Symptom: `event_id` was appended but never checked, so a duplicated event released workload twice. Evidence: 15 `test_duplicate_cancellation_is_idempotent_across_workloads` failures + `test_duplicate_cancellation_is_idempotent`. Fix: early return when `event_id` is already in `processed_cancellation_ids`; also remove the cancelled order from `minutes_by_order` and guard malformed fields.

## 4. Implementation decisions
- Main changes: layered validation (`_order_problem`, `_partner_problem`, `_evaluations`) feeding `estimate_eta` → `assign_order`; unassigned results now carry counted rejection reasons; cancellation dedup by `event_id`.
- Alternatives considered: (a) raising exceptions on invalid input — rejected, the test contract expects `eligible: False`/`partner_id: None`, not crashes; (b) silently coercing bad values to valid-looking ones — explicitly forbidden by the brief; (c) treating `active` as truthy — rejected in favour of `is True` because non-bool values are malformed records.
- Assumptions: `active` must be literally `True`; missing `active_order_ids`/`workload_minutes` default to empty/0 but present-and-malformed values reject the partner; a cancellation without `event_id` is deduplicated per partner (only the first ID-less event applies — conservative choice, see DISPATCH_NOTES.md).

## 5. Verification
- Tests added: `tests/test_regression.py` (eligibility, travel validation, order/partner malformation, ETA formula, tie-break determinism, cancellation edge cases, stretch feature) and `tests/test_dataset.py` (tuple-key conversion, deterministic replay of all 180 orders, idempotent replay of all 177 cancellations).
- Commands run and actual results: `python -m pytest -q` → **274 passed** (was 65 failed / 164 passed); `python -m main` → same correct output as baseline.
- Edge cases verified: all 15 required categories plus dataset replay (see TESTING.md).
- Remaining failures: none. Known limitation: an `event_id`-less cancellation is deduplicated per partner, so a second distinct ID-less event on the same partner is ignored (documented assumption).

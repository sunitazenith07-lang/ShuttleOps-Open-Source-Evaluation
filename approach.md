# approach.md - Required submission

## 1. Baseline
- Commands run before editing:
  - `python -m pip install -r requirements-dev.txt` — installed pytest 9.2.0 and dependencies
  - `python -m pytest -q` — ran the full test suite
  - `python -m main` — ran the offline demo
- Initial test result (include the actual summary):
  - **65 failed, 164 passed in 0.83s**
- Demo/output observed:
  - `python -m main` produced: `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`
  - The demo worked because the sample fixtures used valid data, but the underlying logic lacked validation guards

## 2. Codebase understanding
- Important files/functions inspected:
  - `service.py` — three core functions: `estimate_eta()`, `assign_order()`, `process_cancellation()`
  - `models.py` — `new_partner()` and `new_order()` are dict-factory helpers; partners have `active`, `capacity`, `active_order_ids`, `workload_minutes`, `zone`; orders have `order_id`, `restaurant_id`, `destination_zone`, `prep_minutes`
  - `fixtures.py` — sample order O-7 (restaurant R-2, destination Z-9, prep 10), two partners P-1 and P-2, partial travel map
  - `tests/test_contract.py` — 8 core contract tests (ETA formula, missing travel, inactive partner, full capacity, lowest ETA, tie-break, negative prep, idempotent cancellation)
  - `tests/test_acceptance_matrix.py` — 170 parameterized cases covering every validation boundary
  - `tests/test_edge_cases.py` — 31 expanded ETA formula scenarios including large values
- Candidate filtering, ETA calculation, and capacity flow traced:
  - `assign_order()` iterates all partners, calls `estimate_eta()` for each, collects eligible ones, and picks the one with the lowest ETA (tie-break by partner_id)
  - `estimate_eta()` looks up two travel legs: (partner.zone → restaurant) and (restaurant → destination_zone). If either is missing, partner is ineligible. Otherwise: `pickup = now + leg1 + workload`, `eta = pickup + prep + leg2`
  - `process_cancellation()` deep-copies the partner, removes the order from active list, subtracts workload, and records the event_id
- How I confirmed my understanding:
  - Traced the failing test assertions back to the exact lines in `service.py` where validation was missing. For example, `test_inactive_partners_never_selected[False0]` failed because `assign_order()` had no `if not partner['active']` check

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.

- **Issue 1: Missing travel-time validation**
  - Symptom: `test_invalid_or_missing_travel_time_rejected[-1-1]` — negative travel time `-1` was treated as eligible, producing a negative-offset ETA
  - Hypothesis: `estimate_eta()` only checked `if leg1 is None`, so any non-None value passed through
  - Evidence: String travel time `"2"` caused `TypeError: unsupported operand type(s) for +: 'int' and 'str'`; negative and bool values produced wrong ETAs silently
  - Fix: Added `_is_valid_travel_time()` that rejects non-int/float, booleans, negatives, NaN, and infinity

- **Issue 2: Missing active/capacity filtering**
  - Symptom: `test_inactive_partner_not_assigned` and `test_full_partner_not_assigned` both failed — inactive and full-capacity partners were being assigned
  - Hypothesis: The comment in `service.py` line 16 said "Starter is intentionally incomplete: active/capacity/time validation is missing"
  - Evidence: The loop in `assign_order()` called `estimate_eta()` for every partner without any eligibility check
  - Fix: Created `_is_eligible_partner()` checking `active is True`, capacity is a valid positive int, and `len(active_order_ids) < capacity`

- **Issue 3: Duplicate cancellation not idempotent**
  - Symptom: `test_duplicate_cancellation_is_idempotent` — after calling `process_cancellation()` twice with the same event_id `C1`, `processed_cancellation_ids` was `['C1', 'C1']` instead of `['C1']`
  - Hypothesis: The comment on line 28 said "Starter defect: event_id is recorded but not checked before applying the event"
  - Evidence: The code appended `event_id` unconditionally on every call
  - Fix: Added guard `if event_id in out['processed_cancellation_ids']: return out` at the top of the function

- **Issue 4: No input validation for order fields, prep time, and now parameter**
  - Symptom: Multiple `test_invalid_order_fields_do_not_assign_partner` and `test_current_time_validation` failures
  - Evidence: Empty order_id `""`, `None` restaurant_id, negative prep, boolean `now` — all produced assignments instead of rejections
  - Fix: Added `_is_valid_order()` for order field validation, and `_is_valid_numeric()` checks for prep and now inside `estimate_eta()`

## 4. Implementation decisions
- Main changes and why:
  - All fixes were made in `service.py` only — no changes to `models.py`, `fixtures.py`, `main.py`, or any existing test file
  - Created four private helper functions (`_is_valid_numeric`, `_is_valid_travel_time`, `_is_valid_order`, `_is_eligible_partner`) to keep the main functions clean and each validation rule testable in isolation
  - Used `isinstance(value, bool)` check before `isinstance(value, (int, float))` because Python's `bool` is a subclass of `int`
- Alternatives considered and why rejected:
  - Could have used `try/except TypeError` around arithmetic instead of explicit validation — rejected because it would miss negative values and NaN which compute silently
  - Could have validated inside `new_order()`/`new_partner()` constructors — rejected because the tests modify dicts after creation (e.g., `partner["active"] = False`), so validation must happen at dispatch time
- Assumptions:
  - `workload_minutes` on the partner is trusted as-is (no test requires its validation)
  - `minutes_by_order` missing an entry for a cancelled order defaults to 0 reduction (existing behaviour, preserved)
  - Only `bool` `True` is valid for `active` — integer `1` is rejected per the test expectations

## 5. Verification
- Tests added or changed:
  - Added `tests/test_regressions.py` with 71 new test cases across 10 test classes — no existing tests were modified, deleted, or weakened
- Commands run and actual results:
  - `python -m pytest -q` → **300 passed in 0.30s** (229 original + 71 new)
  - `python -m main` → `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`
- Edge cases verified:
  - Negative/string/bool/NaN/inf travel times, prep times, and `now` values
  - Empty/None/zero order IDs
  - Partners with `active=False`, `active=0`, `active=1`, `active=None`
  - Partners at capacity, over capacity, with invalid capacity types
  - Duplicate cancellation with same event_id
  - Tie-breaking with partners in reversed input order
  - Empty partner list, all-inactive, all-at-capacity, all-missing-routes scenarios
- Remaining failures or known limitations:
  - **None.** All 300 tests pass. No known limitations beyond those documented in DISPATCH_NOTES.md

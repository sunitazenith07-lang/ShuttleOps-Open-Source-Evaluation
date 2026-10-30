# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour
No major blocker stopped progress: the starter source explicitly flags the three intentional defects, and the failing acceptance matrix points directly at them. The genuine challenge was getting the validation semantics exactly right so that *every* case in the acceptance matrix behaves as specified, especially the `now` validation, which previously did not merely reject bad input but **crashed** `estimate_eta` with a `TypeError`.

## 2. Evidence
Before the fix, `python -m pytest -q` gave **164 passed, 65 failed**. Representative failures:
- `test_current_time_validation[5_1]` (`now="5"`): `TypeError: can only concatenate str (not "int") to str` at `service.py:9`.
- `test_current_time_validation[None]`: `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'` at `service.py:9`.
- `test_current_time_validation[-1]` and `[-10]`: negative `now` was accepted as eligible.
- `test_inactive_partner_not_assigned` / `test_full_partner_not_assigned`: inactive and at-capacity partners were still assigned.
- `test_duplicate_cancellation_is_idempotent`: `processed_cancellation_ids` became `['C1', 'C1']` instead of `['C1']`.

## 3. What I tried
- Traced each failing assertion back to `service.py` and confirmed the defect matched the in-code comments ("Starter is intentionally incomplete", "Starter defect").
- Wrote a minimal reproduction for the `now` crash: `estimate_eta(new_order("O","R","D"), new_partner("P","Z"), {("Z","R"):1,("R","D"):1}, now="5")` raised `TypeError` before the fix and returns `eligible=False` after.
- Checked the acceptance-matrix expectations to pin down exact validity rules: e.g. `active` must be `is True`; `capacity` must be a non-bool int >= 1; `now`/`prep`/travel must be finite non-bool numbers >= 0; identifiers must be non-empty strings.
- Ran the full suite after each change and confirmed the previously failing cases passed without breaking previously passing ones.

## 4. Resolution
Root causes were the three incomplete functions in `service.py`; I fixed the causes rather than hiding symptoms:
1. Added `_is_valid_number` / `_is_valid_identifier` helpers so `estimate_eta` validates `now`, both required travel legs, and `prep`, returning `eligible=False` instead of computing with bad data or crashing.
2. `assign_order` now pre-validates order fields and gates candidates on `active is True`, valid capacity >= 1, and `len(active_order_ids) < capacity` before computing ETAs.
3. `process_cancellation` now returns early when `event_id` is already in `processed_cancellation_ids`, and only releases workload when the order is actually active (floored at zero).

## 5. Proof and regression prevention
- `tests/test_regressions.py` adds a test for each fixed behaviour (invalid `now` parametrized over -1/-10/"5"/True/None/nan/inf; invalid travel times; invalid prep; inactive/full/invalid-capacity partners; malformed identifiers; cancellation idempotency; unknown-order cancellation; deterministic dataset dispatch).
- After the fix: `python -m pytest -q` → **266 passed, 0 failed**.
- Related case that could still break: if `data/records.json` or `fixtures.py` partner records use non-standard capacity or active representations, the strict `is True` / non-bool-int capacity rules would treat them as ineligible; that matches the acceptance contract but is worth re-checking if the dataset schema changes.

## 6. Unresolved challenge or next step
No unresolved functional issue. The stretch options in the problem statement (batch assignment in priority order, per-candidate explanation, ETA recalculation on prep change) were not attempted, per "choose at most one after the core works", because correctness and the required documentation took priority. If more time were available, I would implement batch-assignment in priority order as the stretch work.

# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour

No major blocker stopped progress: the starter source explicitly flags the three intentional defects, and the failing acceptance matrix points directly at them. The genuine challenge was getting the **validation semantics exactly right** so that every case in the acceptance matrix behaves as specified, especially the `now` validation, which previously did not merely reject bad input but **crashed** `estimate_eta` with a `TypeError`.

A secondary challenge was deciding where to draw the line between "strict" and "lenient" validation: should `active=1` or `active="yes"` count as active? Should `capacity=1.5` or `capacity=True` count as valid? The acceptance matrix gives precise answers, and getting those boundaries wrong would leave tests failing.

## 2. Evidence

Before the fix, `python -m pytest -q` gave **164 passed, 65 failed**. Representative failures:

| Test | Input | Before fix | After fix |
|------|-------|------------|-----------|
| `test_current_time_validation[5_1]` | `now="5"` | `TypeError: can only concatenate str (not "int") to str` at `service.py:9` | `eligible=False` |
| `test_current_time_validation[None]` | `now=None` | `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'` at `service.py:9` | `eligible=False` |
| `test_current_time_validation[-1]` / `[-10]` | `now=-1` / `now=-10` | Accepted as eligible | `eligible=False` |
| `test_preparation_time_validation` | `prep` = -1, "2", True, NaN, inf | Treated as valid | Rejected |
| `test_invalid_or_missing_travel_time_rejected` | leg1/leg2 = None, -1, "2", True, NaN, inf | Treated as valid | Rejected |
| `test_inactive_partners_never_selected` | `active=False, 0, None, "no"` | Partner assigned | `partner_id=None` |
| `test_capacity_boundary_matrix` | capacity = 0, -1, True, 1.5, None | Partner assigned | `partner_id=None` |
| `test_duplicate_cancellation_is_idempotent` | Same `event_id` twice | `processed_cancellation_ids == ['C1', 'C1']` | `['C1']` |

## 3. What I tried

1. **Traced each failing assertion back to `service.py`** and confirmed the defect matched the in-code comments ("Starter is intentionally incomplete", "Starter defect").

2. **Wrote a minimal reproduction for the `now` crash:**
   ```python
   estimate_eta(new_order("O","R","D"), new_partner("P","Z"),
                {("Z","R"):1,("R","D"):1}, now="5")
   ```
   This raised `TypeError` before the fix and returns `eligible=False` after.

3. **Checked the acceptance-matrix expectations** to pin down exact validity rules:
   - `active` must be `is True` (not truthy)
   - `capacity` must be a non-bool `int >= 1`
   - `now`/`prep`/travel must be finite non-bool numbers >= 0
   - Identifiers must be non-empty strings

4. **Ran the full suite after each change** and confirmed the previously failing cases passed without breaking previously passing ones.

5. **Verified the demo still works:** `python -m main` prints the same correct result before and after.

## 4. Resolution

Root causes were the three incomplete functions in `service.py`. I fixed the causes rather than hiding symptoms:

1. **Added `_is_valid_number` / `_is_valid_identifier` helpers** so `estimate_eta` validates `now`, both required travel legs, and `prep`, returning `eligible=False` instead of computing with bad data or crashing.

2. **`assign_order` now pre-validates order fields** and gates candidates on `active is True`, valid capacity >= 1, and `len(active_order_ids) < capacity` before computing ETAs.

3. **`process_cancellation` now returns early** when `event_id` is already in `processed_cancellation_ids`, and only releases workload when the order is actually active (workload floored at zero).

## 5. Proof and regression prevention

- `tests/test_regressions.py` adds a test for each fixed behaviour:
  - Invalid `now` parametrized over -1, -10, "5", True, None, nan, inf
  - Invalid travel times
  - Invalid prep
  - Inactive / full / invalid-capacity partners
  - Malformed identifiers
  - Cancellation idempotency
  - Unknown-order cancellation
  - Deterministic dataset dispatch over `data/records.json`
- After the fix: `python -m pytest -q` → **266 passed, 0 failed**.

## 6. Unresolved challenge or next step

No unresolved functional issue. The stretch options in the problem statement (batch assignment in priority order, per-candidate explanation, ETA recalculation on prep change) were not attempted, per "choose at most one after the core works", because correctness and the required documentation took priority. If more time were available, I would implement batch-assignment in priority order as the stretch work.

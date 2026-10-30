# approach.md - Implementation approach

## 1. Baseline

Before making any changes, I recorded the untouched starter state.

- Commands run:
  - `python -m pip install -r requirements-dev.txt` (installed pytest 9.2.0 on Python 3.11.9)
  - `python -m pytest -q`
- Initial test result: **164 passed, 65 failed** (the 65 failures are the intentionally incomplete starter behaviour described in the problem statement).
- Demo/output observed: `python -m main` printed
  `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.

## 2. Codebase understanding

I inspected every source file, data file, test file, and configuration file before editing.

### Files inspected

| File | Purpose | Key functions / contents |
|------|---------|--------------------------|
| `service.py` | Core business logic | `estimate_eta(order, partner, travel, now=0)`, `assign_order(order, partners, travel, now=0)`, `process_cancellation(partner, order_id, event_id)` |
| `models.py` | Data-shape factories | `new_partner(partner_id, zone, capacity=2)`, `new_order(order_id, restaurant_id, destination_zone, prep_minutes=10)` |
| `fixtures.py` | Demo scenario | `sample_inputs()` — builds order O-7, partners P-1/P-2, travel map |
| `main.py` | Offline demo entry point | Calls `assign_order` on `sample_inputs()` and prints the result |
| `tests/test_acceptance_matrix.py` | Graded acceptance contract | Parameterized cases covering ETA maths, invalid inputs, capacity, tie-breaking, cancellation idempotency |
| `tests/test_contract.py` | Contract-level assertions | Additional contract tests |
| `tests/test_edge_cases.py` | Edge-case tests | Boundary and malformed-input tests |
| `data/records.json` | Synthetic dataset v2 | 180 orders, 60 partners, 387 travel-time rows, 177 cancellation events, 10 edge-case categories |
| `pyproject.toml` | Project config | pytest testpaths = ["tests"], pythonpath = ["."] |
| `requirements-dev.txt` | Dev dependencies | `pytest>=8.0,<10.0` |
| `.github/workflows/tests.yml` | CI workflow | Runs pytest + demo on push/PR; keeps check red while tests fail |

### Code flow traced (before fix)

1. `estimate_eta(order, partner, travel, now=0)`:
   - Computed `leg1 = travel.get((partner.zone, order.restaurant_id))` and `leg2 = travel.get((order.restaurant_id, order.destination_zone))`.
   - Only guarded against `leg is None`. Did **not** validate `now`, `prep`, or the travel values themselves.
   - Computed `pickup = now + leg1 + workload`, `eta = pickup + prep + leg2`.
   - Crashed with `TypeError` when `now` was a string or `None` because it attempted `now + leg1 + workload` directly.

2. `assign_order(order, partners, travel, now=0)`:
   - Looped over every partner, called `estimate_eta`, took `min` by `(eta, str(partner_id))`.
   - **No validation**: did not check order id/restaurant_id/destination_zone, did not check prep time, did not check `active is True`, did not check capacity, did not check `len(active_order_ids) < capacity`.
   - Inactive partners, full-capacity partners, and partners with invalid capacity were all eligible for assignment.

3. `process_cancellation(partner, order_id, event_id)`:
   - Used `deepcopy(partner)` to avoid mutating the caller.
   - Appended `event_id` to `processed_cancellation_ids` **unconditionally** on every call.
   - Removed `order_id` from `active_order_ids` and reduced `workload_minutes` on every call.
   - A duplicate cancellation with the same `event_id` released workload and capacity **twice** and recorded the event id twice.

### How I confirmed understanding

I ran the baseline suite and mapped every failure to one of the three starter defects flagged in the source comments ("Starter is intentionally incomplete", "Starter defect"). Every failing test in `test_acceptance_matrix.py` corresponded to exactly one of these three root causes.

## 3. Investigation and implementation strategy

For each defect: symptom, hypothesis, evidence, fix.

---

### Issue 1 — `estimate_eta` accepted invalid time inputs and crashed on malformed `now`

**Symptom:**
- `test_current_time_validation` raised `TypeError` for `now="5"` and `now=None`.
- `test_preparation_time_validation` and `test_invalid_or_missing_travel_time_rejected` treated negative, string, boolean, NaN, and infinite travel/prep values as valid.

**Hypothesis:**
`estimate_eta` only checked `leg is None` and never validated `now`, `prep`, or the travel values themselves. It passed invalid values straight into arithmetic (`now + leg1 + workload`), causing crashes or nonsensical ETAs.

**Evidence:**
Baseline failures in `test_acceptance_matrix`:
- `test_current_time_validation[-1]`, `[5_1]`, `[True]`, `[None]`
- `test_preparation_time_validation` across many `prep` values
- `test_invalid_or_missing_travel_time_rejected` across `(leg1, leg2)` pairs

**Fix:**
Added two private helpers in `service.py`:

```python
def _is_valid_number(value):
    """A usable time value: a real (non-bool) int/float, finite and >= 0."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if not math.isfinite(value):
        return False
    return value >= 0


def _is_valid_identifier(value):
    """Order/restaurant/destination identifiers must be non-empty strings."""
    return isinstance(value, str) and len(value) > 0
```

`estimate_eta` now validates `now`, both travel legs (`leg1` partner→restaurant, `leg2` restaurant→destination), and `prep`. If any is invalid, it returns `{'partner_id': ..., 'eta_minutes': None, 'eligible': False}` instead of computing or crashing. Missing travel data is never treated as zero.

---

### Issue 2 — `assign_order` ignored partner active status, capacity, and malformed order fields

**Symptom:**
- `test_inactive_partner_not_assigned`, `test_full_partner_not_assigned`, `test_capacity_boundary_matrix`, `test_invalid_order_fields_do_not_assign_partner`, `test_negative_prep_time_is_rejected` all failed.

**Hypothesis:**
`assign_order` had no eligibility gating beyond whatever `estimate_eta['eligible']` returned. Since `estimate_eta` didn't check active/capacity either, invalid partners were assigned.

**Evidence:**
Baseline contract-test failures showing inactive partners (`active=False`, `0`, `None`, `"no"`) and full-capacity partners (`len(active_order_ids) >= capacity`) receiving orders.

**Fix:**
`assign_order` now validates order fields up front, then gates candidates before calling `estimate_eta`:

1. Validate `order_id`, `restaurant_id`, `destination_zone` are non-empty strings → otherwise return `_unassigned(order, 'invalid ...')`.
2. Validate `prep_minutes` is a valid number → otherwise return `_unassigned(order, 'invalid preparation time')`.
3. For each partner, skip if `partner.get('active') is not True`.
4. Skip if capacity is not a non-bool `int >= 1`.
5. Skip if `len(partner.get('active_order_ids', [])) >= capacity` (at or over capacity).
6. Only then call `estimate_eta`; collect eligible options.
7. If no options, return `_unassigned(order, 'no eligible partner or missing time data')`.
8. Choose `min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))`.

---

### Issue 3 — `process_cancellation` was not idempotent

**Symptom:**
- `test_duplicate_cancellation_is_idempotent` and `test_duplicate_cancellation_is_idempotent_across_workloads` produced `processed_cancellation_ids == ['C', 'C']` instead of `['C']`.

**Hypothesis:**
`event_id` was appended unconditionally and the workload release was applied on every call, so a duplicate cancellation released workload/capacity twice.

**Evidence:**
Contract-test failure showing the duplicated event id in `processed_cancellation_ids`.

**Fix:**
`process_cancellation` now:
1. Returns early if `event_id` is already in `processed_cancellation_ids` (idempotency guard).
2. Otherwise appends `event_id`.
3. Only releases workload when `order_id` is actually in `active_order_ids`.
4. Floors `workload_minutes` at zero: `max(0, workload - minutes_by_order.get(order_id, 0))`.
5. Returns a `deepcopy` so the caller's partner dict is not mutated.

## 4. Implementation decisions

### Main changes and why

1. **Centralized validation helpers** (`_is_valid_number`, `_is_valid_identifier`): invalid data is rejected uniformly in `estimate_eta` and `assign_order` instead of scattered ad-hoc checks. Travel data is never treated as zero; malformed `now`/prep cannot crash the demo.

2. **Eligibility gating in `assign_order`**: keeps `estimate_eta` focused purely on ETA maths while `assign_order` enforces the acceptance contract (active status, capacity, order-field validation). This matches how the contract tests invoke the functions.

3. **Idempotency guard in `process_cancellation`**: satisfies "process a cancellation event only once". Duplicate `event_id`s are ignored; workload is only released when the order is actually active.

### Alternatives considered and why rejected

- **Putting active/capacity checks inside `estimate_eta`**: rejected. `estimate_eta` is called directly by ETA-formula tests with a fresh valid partner; assignment-level gating belongs in `assign_order` to separate concerns.
- **Rejecting truthy `active` values like `1` or `"yes"`**: rejected. The acceptance matrix asserts `active is True` selects the partner and makes no assertion for `1`/`"yes"`, so I used the strict `is True` check.
- **Memoizing ETA results**: rejected. Cache invalidation on workload/cancellation changes is error-prone; the dataset is tiny and correctness matters more than micro-optimization.

### Assumptions

- `now` defaults to 0.
- Capacity must be a non-bool `int >= 1`.
- Identifiers are non-empty strings.
- All data is synthetic (no live GPS, mobile app, or real delivery-partner data).
- Tie-breaking: lowest ETA wins; ETA ties break by partner ID in ascending lexicographic order (`str(partner_id)`), independent of input order.

## 5. Verification

### Tests added or changed

Added `tests/test_regressions.py` with 37 tests covering:
- Invalid `now` parametrized over -1, -10, "5", True, None, nan, inf
- Invalid travel legs (None, negative, string, bool, NaN, inf)
- Invalid prep time (negative, None, string, bool, NaN, inf)
- Inactive, full-capacity, and invalid-capacity partners
- Malformed order identifiers (empty string, None, int)
- ETA tie-breaking by partner ID ascending
- Cancellation idempotency (duplicate event_id)
- Unknown-order cancellation (workload unchanged)
- Deterministic dispatch over a bounded sample of `data/records.json` (converting the 387 travel-time rows to the tuple-key map expected by `service.py`)

### Commands run and actual results

- `python -m pytest -q` → **266 passed, 0 failed** (baseline: 164 passed, 65 failed)
- `python -m main` → `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}` (unchanged, correct)

### Edge cases verified

Missing/negative/boolean/string/NaN/infinite travel and prep; negative/string/None/boolean `now`; inactive, full, zero/negative/bool/float/None capacity; empty string/None/int order ids; duplicate and unknown-order cancellations; empty partner list; missing routes.

### Remaining failures or known limitations

None visible. No test was deleted, skipped, weakened, or bypassed. CI was not edited. The stretch options (batch assignment, per-candidate explanation, ETA recalculation on prep change) were intentionally not attempted because correctness and documentation took priority.

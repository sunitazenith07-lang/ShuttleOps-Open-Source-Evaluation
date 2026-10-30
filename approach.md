# approach.md — Required submission

## 1. Baseline

**Commands run before editing:**

```
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m main
```

**Initial test result (actual summary):**

```
65 failed, 164 passed in 0.68s
```

**Demo output observed:**

```
{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
```

The demo ran without crashing and produced a correct result for the sample fixture
data. However, 65 tests were failing — all due to missing validation logic and two
intentional defects marked with comments in `service.py`.

## 2. Codebase understanding

**Important files/functions inspected:**

- `service.py` — three functions: `estimate_eta`, `assign_order`, `process_cancellation`
- `models.py` — `new_partner` and `new_order` factory functions
- `fixtures.py` — sample data used by the offline demo
- `main.py` — entry point that loads fixture data and calls `assign_order`
- `tests/test_contract.py` — 9 core contract tests
- `tests/test_acceptance_matrix.py` — 171 parameterised acceptance tests
- `tests/test_edge_cases.py` — 31 boundary-value ETA formula tests
- `data/README.txt` — schema for the larger synthetic dataset

**Candidate filtering, ETA calculation, and capacity flow traced:**

`assign_order` loops through all partners and calls `estimate_eta` for each.
`estimate_eta` looks up two travel legs using tuple keys and applies:

```
pickup = now + leg1 + workload_minutes
ETA    = pickup + prep_minutes + leg2
```

The original code only checked `if leg1 is None or leg2 is None`. It never validated
whether a value in the travel dict was meaningful (e.g. it accepted -1 as a valid
travel time). Partner eligibility (active status and capacity) was not checked at all
— the comment in `service.py` at line 16 explicitly flagged this as incomplete.

**How I confirmed my understanding:**

Traced the fixture data manually through the formula and verified the demo output
matched. Read every test assertion to understand the exact expected behaviour before
writing any fix.

## 3. Investigation and implementation strategy

**Issue 1 — No validation of travel time values**

- Symptom: `test_invalid_or_missing_travel_time_rejected` failed for negative
  numbers, strings, booleans, NaN, and infinity.
- Evidence: `travel[('Z','R')] = -1` was accepted as a valid time because the
  only check was `if leg1 is None`.
- Fix: added `is_valid_time(value)` helper that rejects booleans, non-numbers,
  negatives, NaN, and infinity; applied to both travel legs, `prep_minutes`, and `now`.

**Issue 2 — No partner eligibility checks**

- Symptom: `test_inactive_partner_not_assigned` and `test_full_partner_not_assigned`
  both failed — inactive and full-capacity partners were assigned.
- Evidence: the original comment at line 16 read "active/capacity/time validation
  is missing".
- Fix: added `active` check and capacity validation (`is_valid_capacity` plus
  headroom check) before calling `estimate_eta` in `assign_order`.

**Issue 3 — No order field validation**

- Symptom: `test_invalid_order_fields_do_not_assign_partner` failed for empty
  strings, None, 0, and invalid prep values.
- Fix: validate all four order fields at the start of `assign_order` using
  `is_valid_id` and `is_valid_time`.

**Issue 4 — Duplicate cancellation not blocked**

- Symptom: `test_duplicate_cancellation_is_idempotent` failed because
  `processed_cancellation_ids` became `['C1', 'C1']` instead of `['C1']`.
- Evidence: the original comment at line 28 read "event_id is recorded but not
  checked before applying the event".
- Fix: added an early-return guard at the top of `process_cancellation`:
  `if event_id in out['processed_cancellation_ids']: return out`

## 4. Implementation decisions

**Main changes and why:**

- Added three helper functions (`is_valid_time`, `is_valid_id`, `is_valid_capacity`)
  to centralise validation logic. `is_valid_time` is used in four places; repeating
  the same check inline would make future rule changes error-prone (DRY principle).
- Validation runs before any calculation. If the order or partner is invalid, the
  function returns immediately without touching the partner loop.
- Used `partner.get('active')` rather than `partner['active']` so that a missing
  `active` key is treated as falsy rather than raising a `KeyError`.

**Alternatives considered and why rejected:**

- Inline validation at each call site: rejected because `is_valid_time` is used four
  times and the repeated logic would be harder to maintain and easier to get wrong.
- Raising exceptions for invalid input: rejected because the tests expect a return
  value (`eligible=False` or `partner_id=None`), not a raised exception.

**Assumptions:**

- `now=0` is a valid current time (zero minutes from start of the simulation).
- `prep_minutes=0` is valid (instant food preparation).
- A partner whose `active` key is absent is treated the same as `active=False`.
- `capacity=1` with zero active orders means the partner can accept exactly one
  more order.

## 5. Verification

**Tests added:**

Added `tests/test_regression.py` with 6 new regression tests covering: sequential
cancellations of two orders on one partner, non-zero `now` flowing through
`assign_order`, mixed partner pools (inactive + full + missing route + eligible),
idempotency guard keyed on `event_id` not `order_id`, missing `active` key, and
missing `workload_minutes` key.

**Commands run and actual results:**

```
python -m pytest -q
235 passed in 0.21s

python -m main
{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
```

**Edge cases verified:**

- Negative travel time, prep time, and `now` → correctly rejected
- Boolean and string values for numeric fields → correctly rejected
- `float('nan')` and `float('inf')` → correctly rejected
- Inactive partners excluded regardless of valid routes
- Full-capacity partners excluded
- Duplicate cancellation event recorded only once, workload unchanged on repeat
- Missing travel route never treated as zero

**Remaining failures or known limitations:**

None. All 235 tests pass. The larger `data/records.json` dataset was reviewed for
schema understanding but not integrated into automated tests; the demo uses
`fixtures.py` as specified by the project.
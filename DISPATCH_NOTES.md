# DISPATCH_NOTES.md — Required submission

## 1. Worked ETA example

**Order:** O-7 | Restaurant: R-2 | Customer zone: Z-9 | Prep time: 10 min  
**Partner selected:** P-2 | Partner zone: Z-1 | Current workload: 5 min  
**Current time (now):** 0

| Step | Calculation | Result |
|------|------------|--------|
| Leg 1 (partner zone → restaurant) | Z-1 → R-2 | 8 min |
| Pickup time | now + leg1 + workload = 0 + 8 + 5 | **13 min** |
| Food preparation | 10 min | — |
| Leg 2 (restaurant → customer) | R-2 → Z-9 | 12 min |
| Full ETA | pickup + prep + leg2 = 13 + 10 + 12 | **35 min** |

**Actual service output (from `python -m main`):**

```
{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
```

**Why P-2 was chosen over P-1:**

P-1 is in zone Z-3 with 2 min of remaining workload:
- pickup = 0 + 12 + 2 = 14
- ETA = 14 + 10 + 12 = 36

P-2's ETA (35) is lower than P-1's ETA (36), so P-2 wins.

## 2. No-eligible-partner example

Consider order O-X (restaurant R-1, customer zone Z-5, prep 10 min) with three
candidates:

| Partner | Reason ineligible |
|---------|------------------|
| P-A (`active=False`) | Fails the active check in `assign_order` — skipped before ETA is calculated |
| P-B (`capacity=2`, `active_order_ids=['X','Y']`) | At full capacity (2 of 2) — skipped before ETA is calculated |
| P-C (`zone=Z-99`) | No entry for `('Z-99','R-1')` in the travel dict — `is_valid_time(None)` returns `False`, so `eligible=False` |

**Service result:**

```python
{
  'order_id': 'O-X',
  'partner_id': None,
  'eta_minutes': None,
  'reason': 'no eligible partner or missing time data'
}
```

This scenario is verified by `test_no_partner_and_missing_route_cases_are_safe`
and `test_correct_partner_selected_from_mixed_pool` in `tests/test_regression.py`.

## 3. Three edge cases

**Edge case 1 — Negative travel time is rejected**

- Input: `travel[('Z','R')] = -1` (negative value stored as a route time)
- Expected: `eligible=False`, `eta_minutes=None`
- Actual: `eligible=False`, `eta_minutes=None` ✅
- Why: `is_valid_time(-1)` returns `False` because `-1 < 0`. Missing travel
  data is never treated as zero — a negative value is equally invalid.
- Test: `test_invalid_or_missing_travel_time_rejected[-1-1]`

**Edge case 2 — Duplicate cancellation event is a complete no-op**

- Input: `process_cancellation` called twice with the same `event_id='C1'`
  on a partner who had order O1 with 9 min workload.
- Expected: after both calls, `workload_minutes=0` and
  `processed_cancellation_ids=['C1']` (not `['C1','C1']`)
- Actual: `workload_minutes=0`, `processed_cancellation_ids=['C1']` ✅
- Why: on the second call, `'C1' in out['processed_cancellation_ids']` is
  `True`, so the function returns immediately without modifying any state.
- Test: `test_duplicate_cancellation_is_idempotent`

**Edge case 3 — ETA tie broken by alphabetical partner ID**

- Input: two partners `A-PARTNER` (zone ZA) and `Z-PARTNER` (zone ZZ), both
  with travel time 5 min to the restaurant and 5 min from the restaurant,
  prep time 0. Input list order is `[Z-PARTNER, A-PARTNER]` (Z listed first).
- Expected: `partner_id='A-PARTNER'` (alphabetically smaller ID wins)
- Actual: `partner_id='A-PARTNER'` ✅
- Why: `min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))`
  compares `(10, 'A-PARTNER')` vs `(10, 'Z-PARTNER')`. ETAs are equal, so
  string comparison decides: `'A-PARTNER' < 'Z-PARTNER'`. Input list order
  has no effect on the result.
- Tests: `test_tie_break_by_partner_id`, `test_dispatch_selects_lowest_eta_and_stable_tie`

## 4. Assumptions and limitations

**Tie-breaking:** When two partners have identical ETAs, the partner whose
`partner_id` sorts earlier in lexicographic (alphabetical) string order is
selected. This is implemented via `str(item['partner_id'])` in the `min()` key,
ensuring consistent comparison even if partner IDs are stored as non-strings.

**Workload accounting:** `workload_minutes` represents the total minutes of
remaining delivery work for a partner. When an order is cancelled, the value
in `minutes_by_order[order_id]` is subtracted from `workload_minutes`, clamped
to zero with `max(0, ...)`. If the `workload_minutes` key is missing from the
partner dict, it defaults to 0 via `partner.get('workload_minutes', 0)`.

**Cancellation idempotency:** The `process_cancellation` function uses
`event_id` (not `order_id`) as the idempotency key. The same cancellation event
can never release workload or capacity more than once. Each processed `event_id`
is stored in `processed_cancellation_ids`. A subsequent call with the same
`event_id` — even with a different `order_id` — returns the unchanged partner
state immediately without touching any field.

**Boolean values:** Python's `bool` is a subclass of `int`, which means
`isinstance(True, int)` returns `True` and `True == 1`. To prevent `True` and
`False` from being silently accepted as valid times or capacities, all three
validation helpers check `isinstance(value, bool)` first and reject booleans
before the broader numeric type check.

**Unresolved limitation:** The `data/records.json` dataset is not exercised by
the automated test suite. Converting its travel-time records from JSON list
format into the tuple-key dictionary expected by `service.py` is the natural
next step but was not implemented in this submission.

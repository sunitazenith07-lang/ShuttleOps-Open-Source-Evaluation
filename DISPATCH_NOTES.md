# DISPATCH_NOTES.md — Worked examples and edge cases

## 1. Worked ETA example

Input from `fixtures.py`:

- Order: `O-7`, restaurant `R-2`, destination zone `Z-9`, preparation time `10` minutes.
- Candidate partner: `P-2`, zone `Z-1`, remaining workload `5` minutes.
- Current time (`now`): `0`.
- Travel: `(Z-1, R-2) = 8` minutes and `(R-2, Z-9) = 12` minutes.

Calculation:

```text
pickup = now + partner-to-restaurant + workload
       = 0 + 8 + 5
       = 13 minutes

ETA    = pickup + preparation + restaurant-to-customer
       = 13 + 10 + 12
       = 35 minutes
```

Actual result:

```python
{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13,
 'eta_minutes': 35, 'reason': 'assigned'}
```

The other fixture candidate, `P-1`, is ineligible because the travel entry `(Z-3, R-2)` is missing. That missing leg is treated as unknown, not as zero.

## 2. No-eligible-partner example

Input:

- Order `O-9`, restaurant `R-2`, destination zone `Z-9`, preparation `10`.
- `P-A`: inactive, zone `Z-1`.
- `P-B`: active but at capacity (`capacity=1`, one existing order), zone `Z-1`.
- `P-C`: active, zone `Z-3`, but no `(Z-3, R-2)` travel row is supplied.
- Travel supplied only for `(Z-1, R-2)=8` and `(R-2, Z-9)=12`.

Actual result:

```python
{'order_id': 'O-9', 'partner_id': None, 'eta_minutes': None,
 'reason': 'no eligible partner or missing time data '
           '(inactive=1, at_capacity=1, missing_or_invalid_time=1)'}
```

Why each candidate failed:

- `P-A` is not active.
- `P-B` has `1` active order and capacity `1`, so it is full.
- `P-C` has no complete pair of travel legs, so its ETA cannot be calculated reliably.

The order is left unassigned and the reason lists the categories that rejected each candidate.

## 3. Three edge cases

### Edge case 1 — negative travel time

Input: `estimate_eta(order, P, {('Z-1','R-2'): -1, ('R-2','Z-9'): 12})`.

Expected: reject the candidate rather than subtracting time from the ETA.

Actual:

```python
{'partner_id': 'P', 'eta_minutes': None, 'eligible': False}
```

Test: `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected`.

### Edge case 2 — duplicate cancellation event

Input: partner `P` with `active_order_ids=['O1']`, `workload_minutes=9` and `minutes_by_order={'O1': 9}`; call `process_cancellation(p, 'O1', 'C1')` twice.

Expected: the order and workload are released once, and `C1` is recorded once.

Actual after the second call:

```python
{'active_order_ids': [], 'workload_minutes': 0,
 'processed_cancellation_ids': ['C1']}
```

Test: `tests/test_contract.py::test_duplicate_cancellation_is_idempotent` and `tests/test_regressions.py::test_same_order_with_different_event_ids_is_not_released_twice`.

### Edge case 3 — lexicographic ETA tie

Input: two candidates `P-10` and `P-2` with identical travel times, preparation `0` and workload `0`.

Expected: both have the same ETA, so the smaller partner ID in lexicographic order wins. `P-10` is lexicographically smaller than `P-2`.

Actual:

```python
{'order_id': 'O', 'partner_id': 'P-10', 'pickup_minutes': 1,
 'eta_minutes': 2, 'reason': 'assigned'}
```

Test: `tests/test_regressions.py::test_tie_break_is_lexicographic_not_numeric`.

## 4. Assumptions and limitations

- **Tie-breaking:** equal ETAs are resolved by ascending lexicographic `partner_id`. Input order is irrelevant.
- **Workload accounting:** pickup includes the partner's existing `workload_minutes`. A missing workload defaults to zero for compatibility with `new_partner`; an explicitly negative or non-numeric workload makes the partner ineligible.
- **Capacity:** a partner is eligible only when strictly active (`active is True`), capacity is a non-boolean integer of at least 1, and the number of active order IDs is below capacity.
- **Missing travel:** both required legs are mandatory. Missing, negative, non-numeric, boolean, `NaN` or infinite travel values make the candidate ineligible; they are never replaced with zero.
- **Cancellation idempotency:** a repeated event ID is ignored, so workload and capacity are not released twice. Distinct event IDs for the same order cannot release workload twice either, because the order is already absent from `active_order_ids`.
- **Malformed cancellation minutes:** if `minutes_by_order` has no trustworthy number for the cancelled order, the order is removed but the workload is left unchanged rather than guessing an amount. This is an explicit limitation.
- **Determinism:** assignment uses `(eta_minutes, partner_id)` and reason counts do not depend on candidate input order.
- **Not implemented:** the optional stretch items (batch priority assignment, per-candidate explanations, or preparation-time recalculation) were intentionally left out to keep the required behaviour and validation focused.

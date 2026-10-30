# challenges.md — Challenges and debugging

## 1. Challenge or confusing behaviour

The hardest part was not the ETA formula itself; it was deciding what counts as a *reliable* input. The visible matrix deliberately mixes `None`, negative numbers, strings, booleans, `NaN` and `inf` with valid numbers. A simple `value is not None` check was not enough, and Python's `bool` being a subclass of `int` made `True`/`False` easy to accept accidentally.

The second tricky area was cancellation. The starter recorded event IDs, which looked like deduplication, but it recorded them *after* applying the cancellation. The test failure made the ordering bug explicit.

## 2. Evidence

Representative baseline output:

```text
FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[True-1]
FAILED tests/test_acceptance_matrix.py::test_current_time_validation[5_1] - TypeError
FAILED tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[True-0]
FAILED tests/test_contract.py::test_duplicate_cancellation_is_idempotent
E       AssertionError: assert (0 == 0 and ['C1', 'C1'] == ['C1'])
```

`test_current_time_validation[5_1]` failed with:

```text
TypeError: can only concatenate str (not "int") to str
service.py:9: pickup=now+leg1+partner.get('workload_minutes',0)
```

That was direct evidence that validation had to happen before the arithmetic, not after it.

The duplicate-cancellation failure showed the exact symptom: workload reached zero, but the event list was `['C1', 'C1']`. Capacity and workload had not been released twice in that particular test because the order was already absent, but the event was still processed twice. With a different event/order combination the same ordering could release the wrong state.

## 3. What I tried

1. I ran the full suite before changing anything and grouped failures by behaviour: validation, active/capacity, travel data, cancellation.
2. I traced `assign_order` → `estimate_eta` for an inactive partner and confirmed that no active check existed anywhere.
3. I tested the Python boolean issue directly: `isinstance(True, int)` is `True`, so a generic `isinstance(value, int)` capacity/time check accepts booleans. I added an explicit `isinstance(value, bool)` rejection.
4. I considered catching `TypeError` around the ETA addition, but rejected that because it would turn malformed data into a generic error path rather than a controlled ineligible result.
5. For cancellation I moved the `event_id in processed_cancellation_ids` check to the start of the function and returned a copy immediately on a duplicate.

## 4. Resolution

Root causes:

- `assign_order` treated every partner as a candidate.
- `estimate_eta` validated only for missing keys and then trusted the values.
- `process_cancellation` applied the mutation before checking whether the event was already known.

The fix was to centralise validation in `_is_valid_id` and `_is_non_negative_number`, use those checks in both the estimator and the assignment filter, and perform the cancellation duplicate check before any mutation. This addresses the causes rather than hiding them: malformed values now produce `eligible=False` or an unassigned result with a reason, instead of being silently converted or raising.

## 5. Proof and regression prevention

Existing tests now pass, including:

- `tests/test_contract.py::test_missing_travel_is_not_zero`
- `tests/test_acceptance_matrix.py::test_capacity_boundary_matrix`
- `tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads`
- `tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected`

New regression tests in `tests/test_regressions.py` protect the cases that were easy to miss:

- negative workload is not assigned;
- a missing route for one candidate does not block another;
- `P10` beats `P2` in a lexicographic tie;
- malformed partner records are skipped;
- assignment does not mutate its inputs;
- the same order cancelled with two different event IDs is not released twice;
- a duplicate event ID for a different order is ignored;
- the expanded JSON dataset produces deterministic results when the partner list is reversed.

## 6. Unresolved challenge or next step

One deliberate limitation remains: when `minutes_by_order` contains a non-numeric value, the cancellation removes the order from `active_order_ids` but leaves `workload_minutes` unchanged because there is no trustworthy number to subtract. The regression test `test_cancellation_with_malformed_minutes_does_not_guess_workload` records that choice. A production system would likely reject the malformed event and alert an operator instead of partially applying it.

The next investigation would be a shared event store if cancellation events can arrive for the same order at different partners; the current API only has one partner record, so deduplication is necessarily per partner.

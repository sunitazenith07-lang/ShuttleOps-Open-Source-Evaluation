# approach.md — Approach and implementation decisions

## 1. Baseline

- Commands run before editing:
  - `python --version` → `Python 3.13.15`
  - `python -m pytest -q` → **65 failed, 164 passed in 0.61s**
  - `python -m main` → `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`
- The red baseline was expected. Most failures came from four missing behaviours: field/time validation, active/capacity filtering, safe handling of malformed travel data, and cancellation idempotency.
- The starter demo already produced a reasonable ETA for the one sample where the data happened to be valid, so I did not use the demo output alone as evidence that assignment logic was correct. I traced the tests and the source instead.

## 2. Codebase understanding

Files inspected: `README.md`, `STUDENT_START_HERE.md`, `STUDENT_PROBLEM_STATEMENT.md`, `CONTRIBUTING.md`, the pull-request template, `service.py`, `models.py`, `fixtures.py`, `main.py`, all three test files, `pyproject.toml`, `requirements-dev.txt`, the workflow, and the schema/sample records in `data/`.

The data flow is:

1. `new_order` / `new_partner` create the dictionaries used by the service.
2. `estimate_eta` looks up two travel tuple keys: `(partner zone, restaurant_id)` and `(restaurant_id, destination_zone)`.
3. `assign_order` iterates over partners and chooses the eligible minimum ETA.
4. `process_cancellation` copies a partner, removes the cancelled order and subtracts its workload.

The original `assign_order` loop called `estimate_eta` for every partner. It never checked `active`, capacity or malformed partner records. `estimate_eta` only checked for `None` travel values and then did arithmetic directly. `process_cancellation` appended every event ID without first checking whether it had already been processed.

I confirmed this by reading each assertion and by running the baseline, then re-running individual failing groups while changing the service.

## 3. Investigation and implementation strategy

- **Issue 1 — invalid order and time values could be assigned.** Tests such as `test_negative_prep_time_is_rejected`, `test_preparation_time_validation` and `test_current_time_validation` failed. `prep_minutes=None`, `"2"`, `True`, `nan` and `inf` either produced an assignment or raised `TypeError` inside the addition. Fix: added small validators for identifiers and finite non-negative numbers. Validation happens inside `estimate_eta` as well as `assign_order`, so direct estimator calls are safe too.
- **Issue 2 — inactive, full and malformed partners were selected.** In the starter, `test_inactive_partner_not_assigned` and the capacity matrix failed because no filtering existed. Fix: require `active is True`, a non-boolean integer capacity of at least 1, and an `active_order_ids` length below capacity. Missing `active_order_ids` is treated as an empty list; malformed partner records are skipped.
- **Issue 3 — missing/invalid travel was not handled consistently.** `None` was rejected, but negative, string, boolean, `nan` and `inf` values were used in arithmetic. Fix: both travel legs must pass the same finite non-negative number check. Missing data returns `eligible=False`, never a zero-minute leg.
- **Issue 4 — duplicate cancellations were applied repeatedly.** `processed_cancellation_ids` was appended but never checked. Fix: return an unchanged deep copy when the event ID is already present; otherwise remove the order, subtract its stored minutes with a zero floor, and record the event once.

## 4. Implementation decisions

- **Validation helpers instead of scattered conditionals.** `_is_valid_id` and `_is_non_negative_number` are used by both public operations, giving one definition of a valid time. Booleans are explicitly rejected even though Python treats `bool` as an `int`.
- **Strict active flag.** Only `active is True` passes. Values such as `1`, `"yes"` or `None` are treated as malformed/inactive rather than truthy.
- **Capacity is trusted only when well formed.** Capacity must be an `int` (not `bool`) and at least 1. A capacity of `0`, `-1`, `1.5`, `None` or `True` makes the partner ineligible.
- **Minimum scan with an explicit sort key.** `min(options, key=lambda item: (eta_minutes, partner_id))` preserves the required ETA ordering and lexicographic partner-ID tie-break. There is no dependence on input order.
- **Deterministic explanation.** When nobody is eligible, the reason contains category counts such as `inactive=1, at_capacity=1, missing_or_invalid_time=1`. Counts do not change when the partner list is reordered.
- **Cancellation before mutation.** The duplicate check happens before any list or workload change, so a repeated event cannot release capacity twice. The input partner is copied with `deepcopy`.

Alternatives rejected: treating missing travel as zero (violates the contract), raising exceptions for malformed records (the service must return a safe unassigned result), filtering only inside `assign_order` (direct `estimate_eta` calls would still crash), and mutating the caller's partner object (harder to reason about and can duplicate side effects).

## 5. Verification

- Added `tests/test_regressions.py` with 12 tests covering malformed orders/partners, negative workload, missing routes, lexicographic tie-breaking, non-mutation, cancellation event deduplication, malformed cancellation minutes, tuple/set cancellation state, and the expanded JSON dataset.
- Final command: `python -m pytest -q` → **241 passed in 0.21s**.
- Final demo: `python -m main` → the same valid assignment `P-2`, pickup `13`, ETA `35`.
- Verified edge cases include: no partners, all routes missing, negative/string/boolean/NaN/infinite travel, inactive/full/invalid-capacity partners, invalid `now`, invalid order identifiers, tied ETAs, duplicate cancellation IDs, and distinct cancellation IDs for the same order.
- Known limitations: a missing `workload_minutes` defaults to zero for backward compatibility with `new_partner`; if `minutes_by_order` contains a malformed value, the order is removed but the workload is left unchanged rather than guessing a number. Cancellation deduplication is per partner, matching the function's input shape.

# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour
The hardest part was not the ETA formula itself but deciding when a candidate is ineligible and making cancellation truly idempotent. The starter looked almost correct: it rejected `None` travel legs and appended an event id, so the failures were in the boundary cases rather than the happy path.

## 2. Evidence
- Baseline run: `65 failed, 164 passed`.
- `test_duplicate_cancellation_is_idempotent` failed because `processed_cancellation_ids` became `['C1', 'C1']` instead of `['C1']`.
- `test_inactive_partner_not_assigned` and `test_full_partner_not_assigned` failed because `estimate_eta` did not check `active` or capacity.
- `test_invalid_or_missing_travel_time_rejected` failed because `NaN`, `inf`, negatives, booleans, and strings were accepted as travel times.
- `test_preparation_time_validation` failed for the same reason on `prep_minutes`.

## 3. What I tried
1. Ran `py -m pytest -q` on `main` and recorded the 65 failures.
2. Read `main:service.py`; its comments explicitly marked active/capacity/time validation as missing and event-id checking as missing.
3. Inspected the test assertions to determine the exact accepted types: `isinstance(x, (int, float)) and not isinstance(x, bool)`, finite, and `>= 0`.
4. Implemented validators once in helpers and reran the suite; failures dropped to 0.
5. Checked cancellation edge cases manually with a probe script: absent order, workload larger than recorded minutes, and repeated event id.

## 4. Resolution
Root cause: the starter performed arithmetic directly on unvalidated inputs and recorded cancellation events without checking whether they had already been processed. I added type/range/finite checks for ids, order fields, times, capacity, workload, and travel legs; required `active is True`; enforced `active_count < capacity`; and made `process_cancellation` return early when `event_id` is already in `processed_cancellation_ids`. Malformed list/dict fields are coerced safely, and workload is clamped with `max(0, current - minutes)`.

## 5. Proof and regression prevention
- `py -m pytest -q` now reports **229 passed, 0 failed**.
- Key tests: `test_duplicate_cancellation_is_idempotent`, `test_duplicate_cancellation_is_idempotent_across_workloads`, `test_capacity_boundary_matrix`, `test_current_time_validation`, `test_invalid_or_missing_travel_time_rejected`.
- A related case that could still break: a caller that mutates `active_order_ids` without updating `minutes_by_order` would make cancellation subtract the wrong amount; the code cannot detect that inconsistency.

## 6. Unresolved challenge or next step
The implementation is single-process and in-memory. If this were used by multiple workers, cancellation idempotency would need a durable event store or locking. I would validate that next with a concurrency test around shared partner dictionaries.

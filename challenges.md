# challenges.md

## 1. Challenges and confusing behaviours

**A. 65 failures that looked like 65 problems.** The first run printed a wall of failures across seven test groups. Fixing them one-by-one would have produced special cases.

**B. `True` is an `int` in Python.** `isinstance(True, int)` is `True`, so `True` passed any naive numeric check and behaved as 1 minute (travel) or capacity 1. The same applies to `active=1` vs `active=True`.

**C. Duplicate cancellation: the order removal was already guarded, the record was not.** The starter only released workload if the order was still in `active_order_ids`, so on a straight retry workload was *not* double-released — yet the test still failed. That was confusing at first.

**D. The dataset contains cancellation cases the tests do not cover:** 7 events with no `event_id`, and event IDs that appear more than once (e.g. `DSP-CXL-0018` twice for `PARTNER-018`).

## 2. Evidence
- A: `pytest -q` → `65 failed, 164 passed`. Grouping with `grep FAILED | sort | uniq -c` gave 7 distinct test functions (table in `approach.md`).
- B: on the starter, `test_invalid_or_missing_travel_time_rejected[True-1]` failed (`eligible` was `True`); `test_capacity_boundary_matrix[True-0]` failed (partner selected).
- C: `test_duplicate_cancellation_is_idempotent_across_workloads[0]` failed with `processed_cancellation_ids == ['C', 'C']` while `workload_minutes == 0` was already correct. All 15 parametrised workloads failed for this same reason, including `minutes=0`, which proved workload was not the issue.
- D: `Counter(tuple(sorted(e)) for e in events)` → `{('event_id','order_id','partner_id'): 170, ('order_id','partner_id'): 7}`.

## 3. What I tried
1. Grouped failures by function and read each group's parametrisation to extract the exact rule (e.g. prep is valid iff `isinstance(prep,(int,float)) and not bool and >= 0 and not NaN and != inf`).
2. Ran single parametrised cases with `-k` to see the actual vs expected value (C was found this way).
3. Wrote one predicate `_is_minutes()` and checked it against every time-value test group at once rather than per-field checks.
4. Profiled the dataset's cancellation events to decide what to do with missing/reused IDs, then replayed the whole event stream through `process_cancellation` partner-by-partner to confirm workload never went negative and no ID was recorded twice.

## 4. Resolution
- A: root causes were missing validation, missing eligibility filter, and a missing idempotency check. Three focused changes fixed all 65 without special-casing any test value.
- B: every numeric check excludes `bool` explicitly; `active` is compared with `is True`.
- C: the real defect was that the event *record* was not idempotent. Fix: if `event_id` is already processed, return the copy unchanged — no removal, no release, no append. This also covers the case the starter didn't: the same `event_id` with a *different* `order_id` (would previously have released a second order).
- D: events without an ID are ignored (cannot be de-duplicated); a reused ID is ignored regardless of payload.

## 5. Proof and regression prevention
- Original suite: `229 passed` (was 65 failed).
- `tests/test_regression.py`: `test_reused_event_id_with_different_payload_is_ignored`, `test_cancellation_without_event_id_is_not_applied`, `test_truthy_non_bool_active_flag_is_not_treated_as_active`, `test_dataset_cancellation_stream_never_double_releases`, plus 180 per-order dataset checks. 57 of the new tests fail on the original starter.
- Full run: `443 passed in 0.11s`.

## 6. Unresolved limitations / next steps
- `process_cancellation` is pure (returns a new partner). Nothing ties an order to its partner globally, so a cancellation sent to the *wrong* partner is silently a no-op apart from recording the ID. A dispatcher-level `order_id → partner_id` index would catch this.
- Orders with `status: CANCELLED` (60 in the dataset) are still assignable: `status` is not part of the stated contract, so I did not invent a rule for it.
- `assign_order` does not update the chosen partner's `active_order_ids`/workload; batch assignment would need that to keep capacity consistent across orders.
- `processed_cancellation_ids` is a list, so the duplicate check is O(n) per event; fine for the dataset (max 5 events per partner) but a set would be needed at scale.

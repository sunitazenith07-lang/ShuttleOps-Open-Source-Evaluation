# challenges.md — debugging evidence

## 1. ETA validation and Python numeric types
The starter checked only for missing travel entries. A negative travel value could still be treated as valid, a string could raise `TypeError`, and Python treats `bool` as a subclass of `int`. I reproduced these cases with the ETA acceptance tests. The fix validates dictionary-shaped records, non-empty identifiers, non-negative finite numeric values and exact numeric types so malformed records and `True`/`False` are not treated as valid inputs.

## 2. Partner availability was not part of candidate selection
The original `assign_order()` accepted any partner with a valid ETA. It did not check `active` or compare active order count with `capacity`. Tests for inactive partners and full partners failed because a partner ID was still returned. I moved these eligibility checks before ETA ranking and require `active is True`, a positive integer capacity and a free slot.

## 3. Cancellation replay used an event ID without deduplication
The original `process_cancellation()` always appended `event_id`. Calling it twice with the same event removed the order only once, but stored the event twice. The test assertion expected one processed ID, and the full suite retained 16 failures after assignment was fixed. The fix checks the event ID before applying any cancellation and returns the unchanged copied partner for a duplicate.

A related edge case is a repeated event ID with a different order payload. The first event is authoritative; the replay is ignored so one event cannot cancel two orders. Unknown-order events are also recorded once to prevent later replay with a different payload.

## 4. Evidence and verification
- Untouched starter: **164 passed, 65 failed**.
- After ETA validation: **201 passed, 34 failed**.
- After assignment filtering: **219 passed, 16 failed**.
- After malformed-record hardening, cancellation handling and ten new regression tests: **245 passed, 0 failed**.
- Focused assignment tests: **30 passed**; malformed-record regressions: **5 passed**; focused cancellation regressions: **5 passed**.

## 5. Remaining limitations
The implementation expects dictionary records, list/tuple partner collections and tuple-keyed dictionary travel data as used by the supplied project. The local suite was run on Python 3.13.5; GitHub Actions uses Python 3.11, so the PR's CI result still needs to be checked. No performance benchmark was run.

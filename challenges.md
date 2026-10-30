# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
The duplicate-cancellation failure showed ['C','C'], but workload was already correct. It was unclear what exactly was broken.

## 2. Evidence
AssertionError: assert ['C', 'C'] == ['C'] (test_duplicate_cancellation_is_idempotent). The workload assertions passed because the first cancel already removed the order from active_order_ids.

## 3. What I tried
- Read the test and service.py. Checked that the release block is guarded by `order_id in active_order_ids`.
- Inspected data/records.json: 7 of 177 cancellation events have no event_id, and the notes mention "duplicate event ID with differing payload".

## 4. Resolution
Root cause: the event ID was never checked, so deduplication depended on a side effect. Now an event whose ID was already processed returns an unchanged copy. Events without an ID are not stored, because storing None would make every later ID-less event look like a duplicate.

## 5. Proof and regression prevention
test_duplicate_cancellation_releases_once, test_same_event_id_for_another_order_is_ignored. Still risky: a corrupt minutes_by_order value, test_cancellations_without_event_id_are_each_applied

## 6. Unresolved
Non-dict partner passed directly to estimate_eta or process_cancellation. Next step: validate partner shape in one place.

Second case: after the starter tests were green, a manual probe with zone=['x'] raised TypeError (unhashable dict key). Fixed with an invalid-zone check in estimate_eta; covered by test_invalid_partner_zone_is_excluded_not_a_crash.

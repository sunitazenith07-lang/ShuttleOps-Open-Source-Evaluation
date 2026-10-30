# challenges.md

## 1. Challenge or confusing behaviour
The hardest part was making the dispatch rules precise enough to handle missing, invalid, and duplicate data without accidentally treating an edge case as a valid candidate. The tricky decisions were:
- route values are only valid if they exist and are finite, non-negative numbers;
- a partner cannot be assigned when inactive or already at capacity;
- duplicate cancellation events must not release the same workload twice.

## 2. Evidence
I confirmed this by reading the failing tests and then tracing them back to `service.py`.
- `test_invalid_or_missing_travel_time_rejected`
- `test_inactive_partner_not_assigned`
- `test_full_partner_not_assigned`
- `test_duplicate_cancellation_is_idempotent`

The root symptom was that the starter logic accepted candidates too early and mutated cancellation state before checking whether a duplicate event had already been processed.

## 3. What I tried
I followed the data flow from the constructors in `models.py` into the assignment and cancellation logic in `service.py`, then checked the tests that were failing. I also traced a couple of minimal examples by hand:
- a missing route should make `eligible` false even if the partner is otherwise valid;
- a duplicate cancellation should leave `workload_minutes` unchanged after the first release;
- a zero or negative capacity should never be treated as usable.

## 4. Resolution
The fix was to centralize validation instead of mixing it into the selection logic. I added helper checks that reject malformed IDs, non-numeric times, NaN/infinite values, and negative preparation/travel entries.

I also fixed the cancellation logic so it does this in order:
1. stop immediately if the event ID is already in `processed_cancellation_ids`;
2. only release workload if the order is actually in the partner's active list;
3. subtract the tracked order workload and remove the order from the partner's bookkeeping.

This addresses the real cause rather than hiding the symptom.

## 5. Proof and regression prevention
The fix is covered by the visible suite and the new regression checks:
- `test_eta_rejects_missing_partner_id`
- `test_assign_order_rejects_invalid_capacity_even_when_active`
- the existing duplicate-cancellation and capacity tests

I did not need to weaken any tests or skip failing cases.

## 6. Unresolved challenge or next step
No major unresolved issues remain in this repository. The current code passes the visible suite and the offline demo. If I had more time, I would add one more small layer of logging or a batch-assignment helper for processing multiple orders in priority order.
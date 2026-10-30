# DISPATCH_NOTES.md — SmartDispatch examples

## 1. Worked ETA example
Sample order from `fixtures.py`:
- Order: `O-7`; restaurant: `R-2`; destination: `Z-9`; preparation: 10 minutes.
- Candidate `P-2`: current zone `Z-1`; remaining workload: 5 minutes.
- Travel `Z-1` → `R-2`: 8 minutes; travel `R-2` → `Z-9`: 12 minutes.

Calculation:
- Pickup = current time 0 + 8 travel + 5 workload = **13 minutes**.
- ETA = 13 pickup + 10 preparation + 12 final travel = **35 minutes**.

The other fixture partner, `P-1`, has 2 minutes workload and 12 minutes for each route leg, producing pickup 14 and ETA 36. The dispatcher therefore selects `P-2` with ETA 35. The observed demo output was `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.

## 2. No-eligible-partner example
A partner has `active=True`, `capacity=1`, and `active_order_ids=['OLD-1']`. The partner is already at capacity because one active order fills its only slot. Even if both travel-time entries exist and produce a valid ETA, `assign_order()` excludes this partner before ETA ranking. With no other candidates, the result has `partner_id=None`, `eta_minutes=None`, and reason `no eligible partner or missing time data`.

## 3. Edge cases
1. **Missing route:** remove either required tuple key from the travel map. Expected: ineligible candidate and `eta_minutes=None`. Verified by `test_eta_is_ineligible_when_either_required_route_is_missing`.
2. **Equal ETA:** give partners `P-A` and `P-B` identical route times and reverse their input order. Expected: lexicographically smaller ID is selected. Verified by `test_tie_break_by_partner_id` and the acceptance tie matrix.
3. **Duplicate cancellation:** cancel order `O1` with event `C-1`, then submit `C-1` again with a different order ID `O2`. Expected: second payload is ignored; `O2` remains active and workload is not reduced again. Verified by `test_reused_event_id_with_different_order_payload_is_ignored`.
4. **Workload boundary:** cancel an order whose recorded minutes exceed current workload. Expected: resulting workload is zero, never negative. Verified by `test_cancellation_workload_never_goes_below_zero`.

## 4. Assumptions and limitations
- `active` must be the literal Boolean `True`; truthy strings or integers are not accepted as active status.
- Capacity must be a positive integer and `len(active_order_ids)` must be strictly less than capacity before a new assignment.
- Candidate ranking is ETA ascending, then partner ID ascending lexicographically.
- A non-empty cancellation event ID is the idempotency key. Reusing an event ID ignores the replay even if its order ID differs.
- An unknown-order cancellation event is recorded once so that the same event cannot later be replayed with a different payload.
- Invalid/blank event IDs are treated as no-ops. Invalid time values do not create ETA estimates.
- The implementation uses the supplied dictionary/list data model and tuple-keyed travel map; no live GPS or external delivery data is used.

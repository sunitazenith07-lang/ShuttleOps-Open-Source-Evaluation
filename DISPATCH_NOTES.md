# DISPATCH_NOTES.md — Required submission

## 1. Worked ETA example
- Order: `O-7` (`restaurant_id=R-2`, `destination_zone=Z-9`, `prep_minutes=10`).
- Candidate partner: `P-2` (`zone=Z-1`, `workload_minutes=5`, `active_order_ids=['OLD-1']`, `capacity=2`).
- Partner-to-restaurant travel (`Z-1` -> `R-2`): 8 minutes.
- Remaining workload: 5 minutes.
- Restaurant preparation: 10 minutes.
- Restaurant-to-customer travel (`R-2` -> `Z-9`): 12 minutes.
- Calculation: `pickup = 0 + 8 + 5 = 13`; `ETA = 13 + 10 + 12 = 35`.
- Actual result: `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.
- Partner `P-1` (`zone=Z-3`) is ineligible because the required route `R-2 -> Z-9` is missing.

## 2. No-eligible-partner example
- Order: `O-X` (`restaurant_id=R-2`, `destination_zone=Z-9`, `prep_minutes=10`).
- Candidate `P-FULL`: `active=True`, `capacity=1`, `active_order_ids=['A']` -> full capacity.
- Candidate `P-OFF`: `active=False` -> inactive.
- Both required routes are available, but neither candidate passes eligibility.
- Actual result: `{'order_id': 'O-X', 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}`.

## 3. Three edge cases
1. Tie-breaking by partner ID.
   - Input: order `O-T` with prep 0; partners `A` and `Z` in zone with equal travel 3 and destination travel 4.
   - Expected: both ETA 7, choose `A` because `A < Z`.
   - Actual: `{'partner_id': 'A', 'pickup_minutes': 3, 'eta_minutes': 7, 'reason': 'assigned'}`.
   - Test: `test_tie_break_by_partner_id`, `test_ties_break_by_partner_id_independent_of_input_order`.
2. Missing travel data is never zero.
   - Input: `estimate_eta(new_order('O','R','D'), new_partner('P','Z'), {})`.
   - Expected: ineligible, `eta_minutes=None`.
   - Actual: `{'partner_id': 'P', 'eta_minutes': None, 'eligible': False}`.
   - Test: `test_missing_travel_is_not_zero`.
3. Duplicate cancellation is idempotent.
   - Input: partner with `active_order_ids=['O1']`, `workload_minutes=9`, `minutes_by_order={'O1': 9}`; process event `C1` twice.
   - Expected: workload 0 after first cancellation and unchanged after second; `processed_cancellation_ids=['C1']`.
   - Actual: first `workload_minutes=0`; second `workload_minutes=0`, `processed_cancellation_ids=['C1']`.
   - Test: `test_duplicate_cancellation_is_idempotent`.

## 4. Assumptions and limitations
- Tie-breaking is `(eta_minutes, str(partner_id))` in ascending order.
- Workload is treated as remaining minutes and is decremented by the value recorded in `minutes_by_order`.
- Cancellation idempotency is keyed by `event_id` per partner record.
- Missing travel routes make a candidate ineligible; they are never treated as zero.
- The service is in-memory and not concurrency-safe; cancellation consistency assumes one writer per partner.

# DISPATCH_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked ETA example
- **Order:** `order_id="O-7"`, `restaurant_id="R-2"`, `destination_zone="Z-9"`, `prep_minutes=10`
- **Candidate Partner:** `partner_id="P-2"`, current zone=`"Z-1"`, `workload_minutes=5`, `capacity=2`, `active_order_ids=['OLD-1']`
- **Current Simulation Time:** `now = 0`
- **Travel Times:**
  - Partner to Restaurant (`('Z-1', 'R-2')`): `8 minutes`
  - Restaurant to Customer (`('R-2', 'Z-9')`): `12 minutes`
- **Calculation:**
  - $\text{Pickup Time} = \text{now} + \text{travel(Z-1 } \to \text{ R-2)} + \text{workload} = 0 + 8 + 5 = 13\text{ minutes}$
  - $\text{Estimated Delivery ETA} = \text{Pickup Time} + \text{prep\_minutes} + \text{travel(R-2 } \to \text{ Z-9)} = 13 + 10 + 12 = 35\text{ minutes}$
- **Actual Result:**
  - `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

## 2. No-eligible-partner example
- **Order:** `order_id="O-99"`, `restaurant_id="R-9"`, `destination_zone="Z-9"`, `prep_minutes=15`
- **Candidates Evaluated:**
  - `Partner-1`: Inactive (`active=False`) $\to$ Ineligible.
  - `Partner-2`: Capacity full (`active_order_ids=['A', 'B']`, `capacity=2`) $\to$ Ineligible.
  - `Partner-3`: Active with available capacity, but travel entry for `('Z-3', 'R-9')` is missing from travel dictionary $\to$ Ineligible (missing travel is never treated as zero).
- **Actual Result:**
  - `{'order_id': 'O-99', 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}`

## 3. Three edge cases
1. **Boolean as numeric input (`prep_minutes = True`):**
   - *Input:* Order with `prep_minutes = True`.
   - *Expected:* Rejected as invalid number; partner not assigned.
   - *Observed Result:* `{'order_id': ..., 'partner_id': None, 'reason': 'invalid order or time fields'}`.
   - *Verified by:* `tests/test_acceptance_matrix.py::test_preparation_time_validation[True]`.
2. **Missing travel route entry:**
   - *Input:* Travel dictionary lacks `('REST-1', 'DEST-1')`.
   - *Expected:* Candidate marked ineligible; missing travel never assumed to be 0.
   - *Observed Result:* `{'eligible': False, 'eta_minutes': None}`.
   - *Verified by:* `tests/test_contract.py::test_missing_travel_is_not_zero`.
3. **Duplicate cancellation event:**
   - *Input:* `process_cancellation` called with `event_id="CANCEL-01"` twice for the same partner.
   - *Expected:* Workload deducted once; event recorded once in `processed_cancellation_ids`.
   - *Observed Result:* Second call returns unmodified partner state with single event ID in history.
   - *Verified by:* `tests/test_contract.py::test_duplicate_cancellation_is_idempotent`.

## 4. Assumptions and limitations
- **Tie-Breaking:** If two partners have identical ETAs, lexicographical string comparison on `partner_id` guarantees deterministic outcomes regardless of input order.
- **Missing Travel Data:** Missing route entries indicate an unreachable route and must never default to zero minutes.
- **Cancellation Idempotency:** Assumes unique `event_id` strings are generated upstream for each distinct cancellation action.

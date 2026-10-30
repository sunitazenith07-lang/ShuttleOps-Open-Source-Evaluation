# DISPATCH_NOTES.md

## 1. Worked ETA example
Example from the offline demo:
- Order: `O-7`
- Restaurant: `R-2`
- Destination zone: `Z-9`
- Prep time: `10` minutes
- Candidate partner: `P-2`, zone `Z-1`
- Remaining workload: `5` minutes
- Travel: `("Z-1", "R-2") = 8`, `("R-2", "Z-9") = 12`

ETA calculation:
- pickup_minutes = now + partner_to_restaurant + workload = `0 + 8 + 5 = 13`
- eta_minutes = pickup_minutes + prep_minutes + restaurant_to_customer = `13 + 10 + 12 = 35`

Observed result from `python -m main`:
- `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

## 2. No-eligible-partner example
A partner can be rejected if any of the following is true:
- it is inactive;
- it is at or over capacity;
- required travel data is missing;
- the time values are malformed, negative, or non-finite.

Example:
- Order `O` with restaurant `R` and destination `D`
- Candidate partner `P`, active but `capacity = 0`
- Travel data exists: `("Z", "R") = 1`, `("R", "D") = 1`

Expected behaviour: the partner is not considered a valid assignment because the capacity is invalid.
Observed behaviour: `assign_order()` returns `{'order_id': 'O', 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}`.

## 3. Three edge cases
1. Missing travel data
   - Input: `estimate_eta(order, partner, {})`
   - Expected: ineligible with `eta_minutes is None`
   - Actual: passes `test_eta_is_ineligible_when_either_required_route_is_missing`

2. Duplicate cancellation
   - Input: call `process_cancellation(partner, 'O', 'C1')` twice
   - Expected: second call should not release workload or duplicate event processing
   - Actual: passes `test_duplicate_cancellation_is_idempotent`

3. Tie-breaking
   - Input: two partners with identical ETA values but IDs `A` and `Z`
   - Expected: partner `A` wins because IDs are compared lexicographically
   - Actual: passes `test_tie_break_by_partner_id`

## 4. Assumptions and limitations
- Tie-break rule: the partner with the smaller partner ID string wins when ETA values are equal.
- Workload accounting: only current `workload_minutes` is used to delay pickup; cancellation successfully removes the matching order's workload once.
- Cancellation idempotency: a cancellation event is processed at most once per partner; repeated event IDs are ignored.
- Current limitation: the project is intentionally a compact dispatch engine and does not include GPS, external routing APIs, or live partner geolocation. The logic stays deterministic and safe for synthetic data only.

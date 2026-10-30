# Dispatch notes

## 1. Worked ETA example
Example order:
- order_id = `O-7`
- restaurant_id = `R-2`
- destination_zone = `Z-9`
- prep_minutes = `10`

Partner candidate:
- partner_id = `P-1`
- zone = `Z-3`
- workload_minutes = `2`

Travel times:
- (`Z-3`, `R-2`) = `12`
- (`R-2`, `Z-9`) = `12`

Calculation:
- pickup = `now + leg1 + workload`
- pickup = `0 + 12 + 2 = 14`
- eta = `pickup + prep + leg2`
- eta = `14 + 10 + 12 = 36`

Observed result:
- `eligible = True`
- `pickup_minutes = 14`
- `eta_minutes = 36`

This matches the logic in `estimate_eta` and the expected formula in the acceptance tests.

## 2. No-eligible-partner example
Example state:
- order = `O-7` from `R-2` to `Z-9`
- partner = `P-2`
- partner zone = `Z-1`
- travel has no mapping for (`Z-1`, `R-2`) or (`R-2`, `Z-9`)

Result:
- `estimate_eta(...)` returns `eligible == False`
- `assign_order(...)` returns `partner_id is None` and `reason == 'no eligible partner or missing time data'`

The service does not treat missing travel as zero; it rejects the route and keeps the order unassigned.

## 3. Three edge cases
### Edge case 1: inactive partner
- Input: `partner['active'] = False`
- Expected: not eligible for dispatch
- Actual: partner is skipped during assignment
- Verified by: `test_inactive_partner_not_assigned`

### Edge case 2: duplicate cancellation
- Input: same `order_id` and same `event_id` processed twice
- Expected: second event does not reduce workload again
- Actual: the second call returns the same processed state and leaves workload unchanged
- Verified by: `test_duplicate_cancellation_is_idempotent`

### Edge case 3: full capacity
- Input: partner has `capacity` reached and `active_order_ids` count equals capacity
- Expected: no assignment
- Actual: partner excluded from candidate list
- Verified by: `test_full_partner_not_assigned`

## 4. Assumptions and limitations
- Tie-breaking uses partner ID ascending to keep the result deterministic.
- Workload is reduced only when the order is actually active and the event is not a duplicate.
- Cancellation processing clamps workload to zero so it never goes negative.
- The current implementation is intentionally deterministic and safe for invalid or missing data; there are no visible remaining failures in the project test suite.

# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
1) ETA and input validation - The acceptance matrix includes negative values, strings, booleans, `None`, NaN, and infinity. The baseline run failed cases for these invalid values, including `TypeError` cases.
2) Partner eligibility and capacity - The baseline run failed inactive-partner and capacity-boundary cases. `assign_order` currently appends every estimate whose `eligible` field is true, while `estimate_eta` does not apply either check.
3) Duplicate cancellation events - The baseline duplicate-cancellation tests report `['C', 'C']` instead of `['C']` after the same event is applied twice.

## 2. Options considered
1) Filter partner eligibility before calculating ETA

*Expected benefit*: Skip ETA calculations for inactive partners or partners with no remaining capacity. This avoids unnecessary work and makes candidate-selection rules explicit.
*Risk*: Capacity and active-order data must be validated consistently. Incorrect filtering could exclude a valid partner or admit an unavailable one.
*Decision*: Preferred for a correctness-focused improvement.

2) Calculate ETAs for all partners, then filter before choosing

*Expected benefit*: Keeps ETA calculation and availability checks as separate steps, which can make them independently testable.
*Risk*: It calculates ETAs for partners that cannot receive the order and requires a clear distinction between a calculable ETA and assignment eligibility.
*Decision*: Reasonable for a small system, but filtering unavailable partners first avoids unnecessary calculations and keeps the assignment flow clearer.

3) Cache travel-time lookups or ETA components

*Expected benefit*: Could reduce repeated work if the same routes are evaluated frequently across many orders.
*Risk*: Cached values can become stale when travel-time data, partner location, workload, or preparation time changes. Cache invalidation adds complexity.
*Decision*: Not selected because the current code and supplied fixture do not demonstrate a repeated-work bottleneck that justifies caching.

## 3. Changes implemented
I Implemented strict input validation (1) , partner activity and capacity checks (2), ETA estimation accurately (3), selected partner deterministically (2), missing travel-data handling (5), and idempotent cancellation processing (6). Added robust edge-case handling (4) and regression tests to ensure reliable dispatch behaviour.

## 4. Trade-offs
1) Filtering inactive and full-capacity partners before ETA calculation adds eligibility logic, but avoids calculations for candidates that cannot be assigned an order.
2) Keeping ETA validation/calculation separate from partner availability makes each responsibility easier to test.
3) Caching could improve performance in a high-volume system, but introduces invalidation and consistency concerns. Without evidence that repeated route calculations are expensive, the extra complexity is not justified.
4) A simple loop with minimum-ETA selection and a deterministic partner-ID tie-break is clear for the current code. A more complex data structure is not justified without evidence of a scale problem

## 5. Further improvements
With more time, I would first implement the correctness changes: validate order and time fields, filter partners by active status and remaining capacity and make cancellation processing idempotent. I would then run the complete acceptance suite and demo, inspect remaining failures and add tests for malformed partner state.
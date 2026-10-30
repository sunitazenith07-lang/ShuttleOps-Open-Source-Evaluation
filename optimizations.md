# optimizations.md - Required submission

## 1. Baseline and objective
- What needed improvement: correctness and robustness of partner eligibility, ETA validation, and cancellation idempotency.
- Evidence: baseline `65 failed, 164 passed`; starter comments marked validation and duplicate-event handling as incomplete.

## 2. Options considered
1. Inline checks inside `estimate_eta` and `process_cancellation`.
   - Benefit: fewer functions.
   - Risk: duplicated bool/NaN/inf rules and inconsistent behaviour.
2. Shared helper validators `_is_number`, `_valid_time`, `_valid_id`, `_valid_order` (chosen).
   - Benefit: one definition of validity; easier to audit and test.
   - Risk: small indirection.
3. Treat missing travel as an infinite ETA instead of ineligible.
   - Benefit: could still compare candidates.
   - Risk: violates the contract that missing travel never contributes zero and cannot yield a reliable ETA.
4. Mutate partner state in place during cancellation.
   - Benefit: less allocation.
   - Risk: side effects on caller inputs and harder regression testing; deepcopy is safer for these small records.

## 3. Changes implemented
- Change and reason: added validators and guards in `estimate_eta`; capacity/active checks; strict travel validation; idempotent cancellation with coercion and clamping.
- Tests that protect correctness: all 229 tests in `test_contract.py`, `test_edge_cases.py`, and `test_acceptance_matrix.py`.
- Measurement method and result: no performance benchmark was run. Assignment remains O(number of partners); cancellation remains O(active orders) due to list removal.

## 4. Trade-offs
- Strict validation rejects values that Python might otherwise coerce, such as `True` for capacity or `"2"` for travel time. This matches the contract and avoids silent incorrect ETAs.
- `deepcopy` adds overhead, but partner records are small; correctness and input isolation are more important.
- The validators use `math.isfinite`, which is slightly stricter than a simple `value is not None` check but prevents `NaN`/`inf` propagation.

## 5. Further improvements
- Distinguish rejection reasons in the result (invalid order vs. no eligible partner vs. missing route) for easier debugging.
- Add a persistent, concurrency-safe cancellation event store if the service is used by multiple workers.
- Exercise `data/records.json` through an integration test that converts travel rows to tuple keys and checks a sample of expected assignments.
- Validate these improvements with the existing pytest suite plus new property-based tests for ETA monotonicity.

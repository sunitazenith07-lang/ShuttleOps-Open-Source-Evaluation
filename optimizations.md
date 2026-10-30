# optimizations.md

## 1. Baseline and objective
The main issue was not raw speed but correctness and clarity. The starter logic did not validate route data, capacity, or cancellation idempotency, so the code could produce wrong dispatches and invalid state changes.

The evidence was the failing assertions in the visible tests: invalid travel data, inactive/full partners, and repeated cancellation releases.

## 2. Options considered
1. Inline checks in each function
   - Benefit: very local and easy to place.
   - Risk: repeated logic, more room for inconsistency, harder to maintain.

2. Shared validation helpers in `service.py`
   - Benefit: one place for rules like non-negative travel time checks and valid identifiers.
   - Risk: minimal; the project is small, and the helper functions are straightforward.

3. Hard-coding special cases for the sample data
   - Benefit: quick to make the demo look correct.
   - Risk: fails the contract and hidden edge cases. This was rejected.

## 3. Changes implemented
- I introduced helper functions to validate identifiers, finite non-negative numbers, and positive integer capacities.
- I used a single selection rule for `assign_order()`: iterate eligible partners, keep only valid ones, then choose `(eta_minutes, partner_id)`.
- I made cancellation processing idempotent so duplicate event IDs are ignored after the first valid release.

Tests covering correctness:
- `test_invalid_or_missing_travel_time_rejected`
- `test_capacity_boundary_matrix`
- `test_duplicate_cancellation_is_idempotent_across_workloads`
- `test_ties_break_by_partner_id_independent_of_input_order`

Measurement method and result:
- I did not claim a benchmark improvement because this fix prioritizes correctness and maintainability. The suite was verified by running `python -m pytest -q`, which completed in 0.25s with 231 passing tests.

## 4. Trade-offs
This approach favors correctness and maintainability over micro-optimizations. For a small service, a few helper checks are more reliable than trying to squeeze performance out of a tiny loop. The trade-off is a tiny bit of extra code, but it prevents invalid or duplicate events from corrupting partner state.

## 5. Further improvements
If this project grew larger, I would consider a small batch-dispatch routine that processes orders in priority order and a structured reason object for why a candidate was rejected. I would validate those additions with the existing test matrix and targeted regression tests before changing the selection logic.
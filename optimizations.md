# Optimizations

## 1. Baseline and objective
The main problem was not performance; it was correctness. The service layer needed to reject invalid data, handle edge cases consistently, and maintain deterministic assignment for every valid input.

The evidence was clear from the failing tests: the assignment engine was allowing invalid or unsuitable candidates through the dispatch flow, and duplicate cancellation events were changing partner state more than once.

## 2. Options considered
Option 1: add validation only at the end of the dispatch path.
- Benefit: minimal code change.
- Risk: the wrong candidate could still be selected before the system notices the problem.
- Result: rejected because validation must happen before ranking candidates.

Option 2: add validation and early filtering in the ETA function and assignment function.
- Benefit: keeps invalid states out of the selection flow and makes the business rule explicit.
- Risk: slightly more code, but far easier to reason about.
- Result: chosen.

Option 3: hard-code special cases for known tests.
- Benefit: quick fix for a few fixtures.
- Risk: fails for hidden and broader edge cases.
- Result: rejected.

## 3. Changes implemented
- Added reusable validation helpers for numeric and order-field safety.
- Added early rejection for invalid travel data, so missing routes are never treated as zero.
- Filtered partners before ETA assignment by active status and capacity.
- Added duplicate event detection before cancellation updates.
- Ensured workload never drops below zero after a cancellation event.

These changes improve maintainability and correctness without introducing unnecessary complexity. They also protect the code from future invalid data inputs.

## 4. Trade-offs
The main trade-off is simplicity versus strictness.
- A permissive implementation would be shorter, but it would silently accept invalid business states.
- The stricter version adds a few checks, but it prevents wrong assignments and invalid ETA values.

This is the correct choice for a dispatch engine because incorrect assignment is more serious than a small amount of validation code.

## 5. Further improvements
If more time were available, I would consider:
- a small helper module for dispatch policy rules so the validation logic is centralized
- a structured `reason` field for each rejected candidate to explain why it was skipped
- more detailed telemetry around travel-time gaps, full-capacity partners, and cancellation events

These would improve debugging and operational visibility, but they would not change the core correctness requirement. The current fix already preserves the acceptance contract and keeps the logic easily readable.
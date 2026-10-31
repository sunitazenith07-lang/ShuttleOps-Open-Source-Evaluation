# challenges.md - COMPULSORY submission

> This draft records the issues visible from source inspection. It does not claim that runtime debugging or test experiments were performed.

## 1. Challenge or confusing behaviour
The most important behavior to reason about is cancellation idempotency. The starter code records a cancellation event ID but does not check whether that ID has already been processed before removing an order and subtracting workload.

A second important edge case is missing travel data: a candidate cannot receive a reliable ETA if either required route leg is absent.

## 2. Evidence
- In the supplied `process_cancellation()` implementation, the event ID is appended to `processed_cancellation_ids`, but there is no preceding membership check.
- In the supplied `estimate_eta()` implementation, missing travel entries are rejected when either lookup returns `None`.
- In the supplied `assign_order()` implementation, active status and capacity are not checked before a candidate is considered.

No runtime assertion, log, or failing test output has been provided.

## 3. What I tried
- Inspected the three service functions and traced how `main.py` supplies the fixture data.
- Compared the starter behavior with the seven stated requirements.
- Identified the missing active/capacity checks and duplicate-event guard by reading the relevant function bodies.
- Runtime experiments and pytest runs: not reported yet.

## 4. Resolution
Proposed resolutions:
- Validate required identifiers and finite, non-negative time values before arithmetic.
- Reject a candidate if either required travel-time key is absent or its value is invalid.
- Filter inactive partners and partners at capacity before comparing ETAs.
- Check `processed_cancellation_ids` before changing active orders or workload.

These are proposed code changes; the author should update this section with the final adopted implementation and test evidence.

## 5. Proof and regression prevention
No regression test has been confirmed as added or run. Tests should demonstrate:
- A repeated cancellation event leaves workload and active orders unchanged on the second call.
- A missing travel leg makes that candidate ineligible.
- A full or inactive partner is not selected.
- Equal ETAs select the lexicographically smaller partner ID.

## 6. Unresolved challenge or next step
The implementation and test status need to be confirmed. The next step is to run the repository test suite, add focused regression tests for the cases above, and record exact command output. Also decide how cancellation should behave when `minutes_by_order` or `workload_minutes` contains malformed data, ensuring the event is not partially applied.
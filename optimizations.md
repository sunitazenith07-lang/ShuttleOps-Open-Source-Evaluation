# optimizations.md - Required submission

> No performance optimization or speedup is claimed. The changes discussed here primarily target correctness and maintainability.

## 1. Baseline and objective
- What needed improvement: correctness and clarity of candidate filtering, input validation, ETA computation, missing-data handling, and cancellation idempotency.
- What evidence suggested an improvement could help: inspection of the starter `service.py` shows that active status and capacity are not checked, time values are not comprehensively validated, and cancellation event IDs are appended without a duplicate check.
- No timing, memory, or throughput measurements have been supplied.

## 2. Options considered
- Validate inline in each function:
  - Benefit: validation is close to the operation using the value.
  - Risk: duplicated checks can drift between functions.
- Use shared validation helpers:
  - Benefit: consistent ID and time validation.
  - Risk: helpers need clear names and tests because several functions depend on them.
- Treat missing travel as zero:
  - Rejected because it fabricates an ETA and can cause an invalid partner to win.
- Reject a candidate when required travel data is absent:
  - Preferred because it preserves the reliability requirement.
- Mutate the original partner dictionary during cancellation:
  - Rejected in favor of preserving the starter's `deepcopy` behavior and returning a new state.

## 3. Changes implemented
- Change and reason: The conversation produced proposed code using shared `_valid_id` and `_valid_time` helpers, explicit travel-key checks, capacity filtering, deterministic tuple-based selection, and a processed-event check.
- Tests that protect correctness: No added or executed test has been confirmed. Tests should cover each requirement and cancellation replay.
- Measurement method and result: Not measured; no performance claim is made.

## 4. Trade-offs
- Shared helpers reduce repeated validation logic but add a small abstraction layer.
- Explicit missing-data rejection can leave an order unassigned more often than treating missing values as zero, but avoids unreliable ETAs.
- Duplicate-ID rejection is safer than making an arbitrary choice between ambiguous partner records.
- Deep-copying partner state protects the caller's original object but has a copying cost. No measurement has been made.

## 5. Further improvements
- Add focused unit tests and run `python -m pytest -q`; record the actual summary.
- Define atomic cancellation behavior so event recording and workload release cannot become inconsistent when state data is malformed.
- Consider dataclasses or typed schemas for orders and partners if the project scope permits.
- Benchmark only if performance becomes a demonstrated concern, using representative partner-list sizes and repeatable measurements.

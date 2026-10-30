# optimizations.md — implementation notes

## 1. Baseline and objective
The goal was correctness and clear failure behaviour, not speed. The baseline suite reported 65 failures, including accepting unavailable partners, invalid times, and duplicate cancellation records.

## 2. Options considered
- **Validate once at assignment and trust ETA calculation:** less repeated validation, but `estimate_eta` is also a public function used directly by tests and callers. It must protect its own arithmetic inputs.
- **Validate in each public function with small shared helpers (chosen):** keeps direct ETA use safe while avoiding repeated validation expressions.
- **Add a new model class or dependency:** could make data types stricter, but would alter the project's dictionary-based structure unnecessarily.

## 3. Changes implemented
- Added small validation helpers for identifiers, order fields, and minute values.
- Filtered inactive, full, and malformed partners before comparing ETAs.
- Checked cancellation event IDs before changing partner state.
- Added regression tests for untested malformed inputs and cancellation event reuse.
- No runtime performance improvement was measured or claimed.

## 4. Trade-offs
The additional validation checks make the code slightly longer, but help prevent exceptions and incorrect assignments when inputs are malformed. Missing workload is treated as invalid rather than zero because assuming zero could underestimate delivery time. The assignment process scans eligible partners once and then selects the minimum ETA, so the selection work grows linearly with the number of partners.

## 5. Further improvements
If dispatching much larger batches, benchmark realistic partner/order volumes first. Possible next steps are stronger typed models and explicit result types for exclusion reasons, but those should be introduced only if the project needs them and after verifying compatibility with the current API.

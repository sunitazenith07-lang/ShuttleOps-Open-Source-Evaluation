# optimizations.md — optimizations and trade-offs

## 1. Objective
Prioritize correctness and predictable dispatch decisions. The starter performed ETA calculations for partners that could already be ruled out by availability or capacity. No performance benchmark was run, so no speedup is claimed.

## 2. Implemented choices
- Filter inactive, full-capacity, malformed and invalid-ID partner records before calculating their ETA. This avoids unnecessary route lookups for candidates that cannot be assigned.
- Use `min()` with `(eta_minutes, partner_id)` rather than sorting all candidates. This directly expresses the required ordering and keeps selection linear in the number of eligible candidates.
- Validate record shapes, identifiers and minute values before arithmetic; reject booleans, negative values, NaN and infinity rather than coercing malformed inputs.
- Use the cancellation event ID as an idempotency key and check it before mutating the copied partner record.
- Remove the cancelled order's entry from `minutes_by_order` and clamp workload at zero to keep the returned partner state consistent.

## 3. Correctness evidence
- Focused ETA tests: **112 passed**.
- Focused assignment tests: **30 passed**.
- New cancellation regression tests: **5 passed**.
- Malformed-record regressions: **5 passed**. Full suite: **245 passed, 0 failed**.
- These are correctness results, not measured runtime or memory improvements.

## 4. Trade-offs
Strict validation rejects malformed records rather than guessing their meaning. This is safer for assignment decisions but means callers must provide explicit Boolean active status, positive integer capacity and the expected collection shapes. `min()` requires storing eligible estimates in a list; a one-pass best-candidate implementation could reduce temporary memory for a very large partner set, but would add branching and was not justified without measurements.

The processed event IDs remain a list to preserve the existing data shape and easy serialization. A set could make repeated-ID lookup faster for very large histories, but would require conversion at persistence boundaries and was not necessary for this challenge's scale.

## 5. Further improvements
Benchmark selection with substantially larger synthetic partner lists before changing the algorithm. If cancellation histories become large, compare list-based event lookup with a set-backed internal index while preserving the external serialized format. Add tests before broadening accepted input types.

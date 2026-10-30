# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
Correctness and clarity were the problems, not speed. No performance problem was observed.

## 2. Options considered
- Early rejection of an invalid order in assign_order: benefit, one clear reason instead of one per partner. Implemented.
- Sorting excluded-reasons: deterministic text. Cost O(n log n) on a small list. Implemented.
- Extracting compute_eta: easier to test and explain. Implemented.
- Indexing the travel table by restaurant: rejected, the lookup is already O(1) per partner.
- Rounding ETAs to avoid float tie errors: rejected, inputs are whole minutes.

## 3. Changes implemented
Above. Protected by the 38 regression tests. Nothing was benchmarked. The full suite runs in about 0.1 s, which is not a measurement of the change.

## 4. Trade-offs
Result dicts instead of exceptions keep callers simple but make them read `reason`.

## 5. Further improvements
Decimal or integer-second ETAs, partial-data fallback, a batch assignment that updates partner load, and one place that validates partner records.
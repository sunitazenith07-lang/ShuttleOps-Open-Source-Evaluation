# Optimizations

## 1. Baseline and objective
The starter's risk was inconsistent ad hoc validation. The objective was centralized checks and a simple linear candidate pass without unnecessary infrastructure.

## 2. Options considered
- **Inline validation:** rejected because booleans and non-finite values could be handled inconsistently.
- **Cache travel routes:** rejected because caching would add stale-data and lifecycle concerns with little demonstrated benefit for this dataset.
- **Central private helpers:** implemented because they improve consistency in constant time per check.

## 3. Changes implemented
- Added shared ID, time, and order validation in `service.py`.
- Assignment evaluates eligible candidates once and selects the minimum tuple in one pass; duplicate cancellation returns before mutation.
- Correctness is protected by the complete ETA, validation, dispatch, and cancellation suites.

No runtime speed measurement was taken, so no performance improvement is claimed.

## 4. Trade-offs
A few helper functions improve clarity and reduce rule duplication. The simple linear pass is retained because partner lists are small and readability/determinism matter more than micro-optimization. Deep-copying cancellation state protects caller input but copies partner data proportional to its size.

## 5. Further improvements
For a much larger partner list, zone indexing could reduce candidate counts; it should be benchmarked before adoption. Batch assignment could preprocess travel routes, but correctness and stale-state behavior would need tests.

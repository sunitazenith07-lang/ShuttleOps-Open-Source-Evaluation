# optimizations.md — Optimizations and trade-offs

## 1. Baseline and objective

The starting point had correctness problems, not a measured performance problem. The priority was therefore correctness, deterministic output and clear failure reasons. The main repeated work is two travel lookups per candidate and a linear scan over all partners for each order. With the supplied 60-partner dataset this is small, so I did not add caching or indexing before the logic was correct.

Evidence for the need to improve the code rather than optimise it first: the untouched baseline was **65 failed, 164 passed**, including validation and cancellation failures. A faster implementation of the wrong selection rule would not help.

## 2. Options considered

1. **Sort all candidates by `(eta, partner_id)` and take the first.** Simple and deterministic, but builds a full sorted list when only the minimum is needed. I used `min()` with the same key instead: O(P) time and O(P) space for the eligible options already required for the selection.
2. **Pre-index travel by `(from, to)` or by partner zone.** This could reduce dictionary lookups, but the travel mapping is already a dictionary keyed by the exact tuple. Building another index for a single order would add allocation and complexity without a measured benefit.
3. **Cache ETAs per order/partner pair.** Useful for repeated batch assignment, but `assign_order` is stateless and accepts arbitrary dictionaries, so a cache would need invalidation rules and could return stale data after a cancellation. Rejected for this scope.
4. **Use a set for processed cancellation IDs.** Set membership is O(1) instead of O(n) for a list. However, the required output and existing tests expect the ordered list `processed_cancellation_ids`, and cancellation lists are small. Converting to a set on every call would add work and lose the recorded order. Kept the list.
5. **Fail fast on an invalid order.** Implemented: `assign_order` validates the order once before scanning partners. This avoids repeating the same checks for every candidate and gives a clearer reason.

## 3. Changes implemented

- Centralised scalar validation in two helpers, so every candidate uses the same rules and there are no duplicated, subtly different checks.
- Validated the order once in `assign_order`; `estimate_eta` still validates when called directly, because it is part of the public surface used by the tests.
- Converted an incoming iterable of partners to a list once, so a generator cannot be consumed accidentally more than once and malformed input cannot raise during iteration.
- Used a single `min()` scan with an explicit `(eta_minutes, partner_id)` key. This is deterministic and avoids a full sort.
- Added deterministic reason counters instead of embedding candidate order or exception text in the result.
- Deep-copied partner state only in `process_cancellation`, where mutation is required. Read-only operations never copy the full partner list.

Tests protecting these choices: all visible assignment, tie-break, cancellation and validation tests, plus `tests/test_regressions.py::test_assignment_does_not_mutate_inputs` and the expanded-dataset determinism check.

Measurement: I did not run a micro-benchmark, so I am not claiming a speedup. The full suite runtime observed after the change was **241 passed in 0.21s**; that is a suite runtime, not a before/after performance comparison.

## 4. Trade-offs

- **Readability vs micro-optimisation:** helper calls add a small amount of overhead per candidate, but make the validation rules auditable and prevent divergent checks. At 60 partners this is negligible.
- **Strict validation vs leniency:** rejecting `1`/`"yes"` as `active` and rejecting non-integer capacity avoids silently assigning to malformed records. The trade-off is that callers must use the documented shapes (`active=True`, integer capacity) rather than relying on truthiness.
- **Per-candidate options list:** keeping eligible estimates in a list uses O(P) memory. Streaming the minimum would use O(1), but would complicate the reason handling and tie-break explanation. The dataset size makes the clearer version preferable.
- **Cancellation list vs set:** list membership is slower for very large histories, but preserves the ordered output and matches the contract/tests. If cancellation histories grew large, an auxiliary set could be maintained alongside the list.

## 5. Further improvements

With more time I would:

1. Add an optional batch entry point that validates the order set once and reuses the sorted partner candidates, measuring the improvement on the 180-order dataset.
2. Add a travel-index builder for the JSON dataset so repeated `(from, to)` rows are normalised once with explicit duplicate handling.
3. Profile a large synthetic run (for example 10,000 partners) before choosing between a heap, sorted list and linear minimum.
4. Add structured reason codes alongside the human-readable reason strings if a UI needs to translate them.

Each of these should be validated against the same contract and regression suite before being adopted; none is necessary for the current correctness target.

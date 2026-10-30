# ⚙️ Optimizations and Trade-offs

## Objective and measurement

The measured problem was correctness: the untouched starter run had 65 failures and 164 passes, while the final visible suite reported 233 passed. No runtime or memory benchmark was run, so no speedup is claimed.

## Options considered

| Option | Potential benefit | Trade-off | Decision |
|---|---|---|---|
| Convert malformed values such as `"10"` into numbers | Accepts loosely formatted input. | Hides malformed data and makes the input contract unpredictable. | Reject invalid values explicitly. |
| Sort every eligible candidate by ETA | Produces a complete ranking. | The service only returns the best candidate, so a full sort does extra work. | Use `min()` with ETA and partner ID as the key. |
| Mutate the original partner during cancellation | Avoids copying the record. | Can create side effects for other code holding the same object. | Preserve copy-and-return behavior with `deepcopy()`. |
| Add a more complex candidate-ranking structure | Might help with very large workloads. | Adds complexity without an observed bottleneck or benchmark. | Keep a simple candidate scan. |
| Treat missing travel as zero | Allows an estimate when route data is incomplete. | Produces a misleading ETA and violates the requirement. | Mark that candidate ineligible. |

## Maintainability and complexity

- A shared numeric-validation helper keeps time checks consistent.
- A dedicated capacity helper makes partner eligibility easier to review.
- Checking a cancellation ID before changing state makes the one-time event rule explicit.
- Assignment scans the partner list once, so its candidate-selection work is linear in the number of partners; each route lookup uses the supplied mapping. This is a code-structure observation, not a measured performance claim.
- Four regression tests were added, including a route converted from the expanded dataset. The full visible suite reports 233 passed.

## Trade-offs and next steps

The simple scan is easy to understand and appropriate for the supplied offline challenge. If representative, larger workloads later show a performance issue, profile first, then compare alternatives while keeping the correctness tests.

Potential future work, not implemented here:

1. Add a data adapter for converting the JSON dataset into validated service inputs.
2. Add targeted tests for malformed cancellation records and extreme arithmetic boundaries.
3. Consider caching or route indexing only if profiling demonstrates that lookup or scanning is a bottleneck.

No batch assignment, candidate explanation, or ETA recalculation stretch feature was implemented.


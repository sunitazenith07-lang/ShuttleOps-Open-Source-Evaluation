# ⚙️ Optimizations and Trade-offs

## Objective

The measured issue was correctness: the starter test run had 65 failures and 164 passes. No performance benchmark was run, so no speedup is claimed.

## Options considered

| Option | Benefit | Trade-off | Choice |
|---|---|---|---|
| Convert malformed values such as "10" into numbers | Could accept loosely formatted input | Hides malformed data and makes the input contract less predictable | Reject invalid values explicitly |
| Sort every candidate by ETA | Produces a fully ordered candidate list | The service only needs the best candidate | Use min() with ETA and partner ID as the comparison key |
| Mutate the original partner during cancellation | Avoids making a copy | Can create side effects for other code holding the same object | Keep the existing copy-and-return behavior with deepcopy() |
| Add a more complex candidate-ranking structure | Could help at very large scale | Adds complexity without evidence of a bottleneck | Keep the simple candidate scan |

## Changes that improve maintainability

- A shared numeric validation helper keeps time checks consistent.
- A dedicated capacity helper makes partner eligibility easier to read.
- Cancellation event checking happens before any state change, making the idempotency rule explicit.

Four regression cases were added in tests/test_regressions.py, including a route from the expanded dataset. The full visible suite reports 233 passed. These changes were not benchmarked for runtime or memory use.

## Trade-offs and next steps

The candidate scan is linear in the number of partners, and travel lookup uses the supplied mapping. This is straightforward for the current offline challenge. If real workload measurements later show a performance problem, profile representative inputs first and compare alternatives while preserving the correctness tests.

No batch assignment, candidate explanation, or ETA recalculation stretch feature was implemented.

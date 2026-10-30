# Approach and implementation

Record of Codex's AI-assisted work at the user's request, not independent student authorship.

## Baseline and code flow
Read the problem statement, repository guide, source, tests, data schema/catalog and workflows.
Python 3.12.14; requirements-dev.txt was satisfied in an isolated environment.
Untouched test suite: 65 failed, 164 passed. Demo: P-2, pickup 13, ETA 35.
models.py constructs records; fixtures.py supplies demo inputs; main.py calls assign_order.
assign_order calls estimate_eta for candidates. process_cancellation returns a deep copy.
The dataset has 180 orders, 60 partners, 387 routes and 177 cancellation events.

## Root causes
Time arithmetic accepted booleans, negative times, NaN/infinity and malformed values.
Assignment ignored active status and capacity. Cancellation recorded event IDs but never
checked them and retained stale minutes entries. Invalid record shapes could raise exceptions.

## Implementation decisions
Shared predicates validate IDs, times and list fields before use. estimate_eta validates
both candidate eligibility and route availability so direct callers get consistent results.
Only exact active=True and positive integer capacity qualify. Preserve the specified formula.
Select the minimum (ETA, partner ID) in one pass. Duplicate partner IDs are excluded to
avoid input-order-dependent ambiguity. Already-active orders cannot be recommended again
to the same partner. Functions do not mutate caller records.
Cancellation validates the event and ledger, checks replay before changes, releases only an
active order, removes its minutes entry and clamps remaining workload at zero.
Missing minutes retain workload rather than inventing an estimate; malformed minutes reject
without partial changes. Numeric overflow produces ineligibility/no-op rather than unsafe state.

## Alternatives and trade-offs
Did not coerce string times or truthy active flags, because malformed data must not be silently
reinterpreted. Kept simple dictionaries and history lists instead of introducing new storage.
Did not reserve capacity in assign_order: the existing API is a recommendation service.

## Verification
45 new regression cases cover malformed inputs, immutable inputs, known ETA, ties,
cancellation replays/conflicting payloads, overflow and dataset invariants.
Final: 274 passed. Offline demo still gives P-2 / 13 / 35. Existing tests and CI unchanged.
See TESTING.md and DISPATCH_NOTES.md for cases, assumptions and remaining limitations.

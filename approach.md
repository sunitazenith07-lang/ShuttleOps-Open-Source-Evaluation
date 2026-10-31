# Implementation approach

## Work record

This implementation, the added tests, and this documentation were prepared with Codex assistance. The results below describe work actually performed during that session, not an independent debugging history. The evaluation prohibits AI assistance, so this work needs to be discussed with the instructor before submission.

## Starting point

The untouched starter produced **65 failed, 164 passed**. The user first reported that result, and Codex reproduced it on a workspace copy before editing. Dependencies were installed with `python -m pip install -r requirements-dev.txt`. The baseline test command was `python -m pytest -q`.

The baseline demo output was not saved before editing, so there is no before-and-after demo claim here. The verified final demo is recorded in DISPATCH_NOTES.md.

## Understanding the flow

`models.py` creates order and partner dictionaries. `fixtures.py` supplies the small example used by `main.py`. The demo passes that data to `assign_order()` in `service.py` and prints the result.

`assign_order()` checks candidates through `estimate_eta()`. Capacity and workload mean different things: capacity limits the number of active orders, while workload adds minutes to pickup time. The selected result is a decision; the function does not add an order to a partner's active list.

`process_cancellation()` is separate. It returns a copy of a partner with the cancelled order removed and its recorded minutes released. The larger JSON dataset provides extra examples. Its travel rows need converting into `(from, to)` dictionary keys before calling the service.

## Investigation and fixes

The initial failures pointed to three main gaps:

1. The starter used time values without validating them. Negative values could produce incorrect ETAs, and strings could cause arithmetic errors. Order identifiers also needed checking. The fix validates required fields and accepts only non-negative, finite integer or float durations, excluding booleans.
2. The assignment loop accepted candidates without checking active status or capacity. The fix checks these before calculating an ETA. A partner must have `active is True`, a positive integer capacity, and fewer active orders than that capacity.
3. Cancellation event IDs were appended without checking whether they had already been processed. The fix checks the event history first. Replaying an event returns unchanged state, including when someone tries to reuse that event ID for a different order.

Stress tests then found an arithmetic overflow during cancellation and an input-order-dependent result for duplicate partner IDs. Their reproductions and fixes are in challenges.md.

## Ambiguity review: approach and decisions

After the first 344 tests passed, the code was compared again with the written requirements instead of assuming that passing tests covered every interpretation. Small examples were run to separate accounting defects from API choices the brief did not fully specify.

The review reproduced incomplete cancellation accounting and reassignment of already-active orders. Cancellation now requires the active-order list, total workload, and per-order accounting map. For an active order, its own recorded minutes must also be present and valid; missing information leaves state and event history unchanged. Assignment rejects an order already active on any supplied partner, even if that partner is inactive.

The brief does not explicitly define duplicate-assignment requests, so rejecting an already-active order is a conservative implementation decision. The existing recommendation-only assignment API and state-only cancellation return value were preserved. These are documented limits rather than completed fixes. Reproductions are in challenges.md and test evidence is in TESTING.md.

## Implementation choices

Changes are concentrated in `service.py`. The constructors, demo, fixtures, original tests and workflows did not need changes. Validation helpers keep the same rules in one place rather than repeating checks in several functions.

The selection loop keeps the best eligible candidate seen so far. ETA comes first, then partner ID in lexicographic order. Pickup time is a final comparison only when both earlier values are identical. This makes the returned result stable even for duplicate partner records with rounded floating-point ETAs.

Missing travel data is rejected, not filled with zero. Failed candidates contribute reasons to the unassigned result. Reasons are sorted so their order is stable.

Adding validation to the constructors alone would not protect dictionaries loaded directly from JSON. Validation at the service boundary covers those callers too. Batch assignment and other stretch features were left out to keep the change focused.

## Verification and limits

The 229 original tests were preserved. `tests/test_regressions.py` adds 40 cases, `tests/test_stress.py` adds 75, and `tests/test_accounting.py` adds 8, giving **352 tests**. The latest local run on Python 3.15.1 returned **352 passed in 0.83s**. TESTING.md records the command and examples.

No known failures remain in the executed suite. Hidden tests and every possible Python object have not been covered. The current implementation expects ordinary dictionary records and list/tuple partner collections. It does not reserve capacity, persist state, or coordinate concurrent dispatch calls.

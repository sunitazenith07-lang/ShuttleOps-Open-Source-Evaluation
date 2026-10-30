## What did you change?

Completed the SmartDispatch delivery-partner assignment and ETA engine.

### Implementation
- Added strict validation for order identifiers, restaurant identifiers, destination zones, preparation time, partner data, workload, travel legs, and current time.
- Added finite, non-negative numeric validation so negative values, strings, booleans, NaN, and infinity cannot produce an ETA.
- Updated `estimate_eta()` to distinguish missing travel data from valid zero-minute routes.
- Updated `assign_order()` to consider only active partners with a valid capacity and available workload capacity.
- Updated candidate selection to use the complete ETA and then sort equal results by partner ID in ascending lexicographic order.
- Updated cancellation handling to use an event-ID history and prevent duplicate cancellations from reducing workload or active order capacity twice.
- Preserved non-mutating cancellation behavior by copying partner state before processing an event.

### Required submission files
- Completed `approach.md` with baseline results, code-flow analysis, implementation decisions, and verification evidence.
- Completed `challenges.md` with the missing-route distinction, validation difficulties, cancellation idempotency, resolution steps, and proof.
- Completed `optimizations.md` with correctness-focused alternatives, implemented changes, trade-offs, and future possibilities.
- Completed `TESTING.md` with actual environment, commands, pass count, and edge-case evidence.
- Completed `DISPATCH_NOTES.md` with a worked ETA, a no-eligible-partner example, edge cases, assumptions, and limitations.

## Root cause

The starter implementation calculated an ETA without validating the order or input types, did not filter inactive or fully booked partners, and treated some invalid partner/travel values as usable numbers. Missing routes could therefore produce incorrect assignments, negative values could change the calculated ETA, and malformed records could reach arithmetic operations without a safe contract.

Cancellation handling also recorded duplicate event IDs without checking them before changing partner state. As a result, the same cancellation could remove an active order and subtract its workload more than once.

The fixes move validation and eligibility checks into the service logic instead of changing fixtures or weakening tests. Duplicate event IDs are checked before any cancellation mutation.

## Tests

- [x] I ran `./.venv/bin/python -m pytest -q`.
- [x] I ran `python3 -m main`.
- [x] I used the existing regression tests to verify the change.
- [x] I did not delete, skip, weaken or bypass existing tests.

Actual test summary:

```text
229 passed in 0.05s
```

Actual demo output:

```text
{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
```

No remaining visible test failures are known.

## Required problem-solving documents (all three mandatory; 15 marks total)

- [x] `approach.md` completed (5 marks).
  - Records the initial 65-failure baseline, traced data flow, root causes, implementation choices, and final verification.
- [x] `challenges.md` completed (COMPULSORY; 5 marks).
  - Documents missing-route versus zero-duration handling, cancellation identity, debugging evidence, resolution, and future malformed-record testing.
- [x] `optimizations.md` completed (5 marks).
  - Compares centralized validation, route caching, and candidate-selection options, including correctness and performance trade-offs.

## Edge cases checked

| Case | Expected behavior | Actual result |
|---|---|---|
| Negative preparation time (`-5`) | Reject the order and leave it unassigned | `partner_id=None`; `test_negative_prep_time_is_rejected` passed |
| Missing first or second travel route | Keep ETA ineligible instead of treating missing time as zero | `eligible=False`, `eta_minutes=None` |
| Partner capacity 1 with one active order | Reject the partner as fully booked | `partner_id=None` |
| Equal ETA for partners `A` and `Z` | Select partner ID `A` after lexicographic tie-breaking | Partner `A` selected |
| Duplicate cancellation event `C1` for `O1` | Release workload and capacity once only | Workload `0`; processed IDs remained `['C1']` |
| Negative, NaN, infinity, string, or boolean time | Reject safely without arithmetic | ETA returned ineligible |
| Unknown cancellation order | Preserve existing workload and active orders | Existing state remained unchanged |

## Design decisions / limitations

- Missing and invalid travel data are treated as unavailable. Legitimate zero-minute travel remains valid.
- The delivery ETA formula is:
  - Pickup time = current time + partner-to-restaurant travel + remaining partner workload.
  - ETA = pickup time + restaurant preparation time + restaurant-to-customer travel.
- A candidate must have `active=True`, an integer capacity of at least one, fewer active orders than capacity, and valid partner/travel/workload values.
- Equal ETAs are resolved by the string partner ID in ascending order.
- Cancellations use event IDs as the idempotency key. Workload reductions are floored at zero.
- `DISPATCH_NOTES.md` contains the challenge-specific worked ETA, no-eligible-partner example, three edge cases, assumptions, and limitations.
- This implementation is intentionally scoped to synthetic challenge records. Live traffic, persistence, database schemas, and external GPS services are not included.

## Integrity confirmation

- [x] This is my own individual work.
- [x] I have followed the evaluation's AI-use policy.
- [x] I can explain my changes and make a small live modification if asked.

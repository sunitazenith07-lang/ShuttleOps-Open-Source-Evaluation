# Optimizations and trade-offs

## Objective

The main improvement needed was correctness and predictable behavior on invalid data. The baseline had 65 failures, including cases where invalid times remained eligible, capacity was ignored, and duplicate events were appended repeatedly. No performance bottleneck was measured.

## Options considered

- A single validated candidate pass keeps eligibility and ETA selection in one understandable flow. This is the chosen design; it takes linear time in the number of partners and stores only eligible candidates.
- A route index, cached ETA, or vectorized calculation could reduce repeated lookup work in a much larger dispatch workload. I did not add these because the supplied dataset has 60 partners, the travel map already supports constant-time tuple-key lookup, and no benchmark showed that lookup or scanning was a bottleneck.
- Silently coercing strings, booleans, or missing values to numbers would accept more input but could produce unreliable ETAs. The service rejects those values instead.

## Changes and evidence

The implementation validates each candidate before calculating its ETA, then performs one minimum selection using ETA and partner ID. Cancellation IDs are checked before mutating the copied state, preventing repeated release of the same order. These changes address correctness; I did not benchmark them or claim a speedup. The full visible suite reports **235 passed** after the implementation.

## Trade-offs and next steps

Strict record validation can reject legacy records with incomplete fields; this is safer than assigning with guessed values. Copy-on-write cancellation uses memory proportional to one partner record, which keeps callers' inputs untouched and is small for the current model. The linear scan is `O(P)` per order and is appropriate for the supplied data size.

For a production-sized workload, I would first benchmark realistic order and partner counts, then consider indexing travel routes or batching assignments. I would also move cancellation deduplication into durable storage with an atomic event key if multiple workers could process events concurrently. Neither improvement is measured or implemented here.

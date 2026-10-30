# Optimizations and trade-offs

AI-assisted engineering record. No runtime speedup is claimed; no benchmark was performed.

## Implemented
Use shared validation helpers instead of duplicating numeric/type rules in handlers.
Select the best candidate while iterating rather than retaining all eligible estimates:
minimum selection is O(n). A preliminary ID count also takes O(n) time and O(n) memory
and excludes ambiguous duplicate IDs deterministically. No candidate sort is needed.
Tests verify lowest ETA, lexicographic ties and reversed input order.

## Options considered
A sorted candidate list would make future explanation output easier but adds O(n log n)
work and unnecessary retained estimates for this recommendation-only API.
A set of processed cancellation IDs could speed membership checks for long histories, but
preserving the list schema is simpler for this exercise; lookup remains O(h).
Mutating partner input would avoid copying but breaks caller-state safety. Retain deepcopy
on cancellation and no mutation during estimates; regression tests protect both behaviors.
Do not replace unknown travel times with zero: speed or convenience cannot justify false ETAs.

## Future work
Benchmark larger candidate pools before optimizing further. Add transactional capacity
reservations and durable idempotency keys for concurrent dispatch, with integration tests
for competing assignments. Add structured validation diagnostics if callers require more
specific no-candidate reasons. No optional stretch item was implemented.

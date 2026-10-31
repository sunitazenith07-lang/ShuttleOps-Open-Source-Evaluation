# Optimizations and trade-offs

## Objective

The priority was correctness and predictable failure handling, not a measured performance problem. The original pass over partners was already linear, but it evaluated candidates that were inactive or already full.

## Changes made

Assignment now filters unavailable partners before estimating their routes. It retains one linear pass through the partner list and uses `min()` with `(eta, partner_id)` for deterministic selection. Validation helpers remove repeated type checks and make the rules visible in one place.

No performance number is claimed: the test run is a correctness check, not a benchmark. The relevant protection is the 232-passing-test suite, including capacity and ETA matrices.

## Trade-offs and next steps

Strictly requiring non-empty string identifiers and `active is True` rejects loosely formatted external data, which is safer than silently coercing it. Building a list of eligible estimates is clear for this small engine; a future large-scale version could track the current best candidate while iterating to avoid the temporary list. A production design should add typed models, route-data ingestion validation, persistence, and atomic capacity reservations before optimizing throughput.

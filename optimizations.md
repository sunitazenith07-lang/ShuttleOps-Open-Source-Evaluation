# Optimization notes

## 1. Objective and measured baseline

The change addressed correctness, clarity and maintainability, not a measured performance problem. The original suite had **65 failures and 164 passes**; the final suite had **235 passes**. These are correctness results, not runtime benchmarks. No speedup is claimed.

## 2. Alternatives considered

### Coerce values into numbers

Converting strings such as `"10"` to numbers could be convenient, but it can conceal malformed input and turn questionable data into an apparently valid ETA. This was rejected. The service accepts actual non-negative finite numeric values, with Booleans explicitly excluded.

### Validate all fields only at the dispatch entry point

This would avoid repeating order validation while scanning partners, but `estimate_eta` is independently called by tests and other potential callers. Keeping the ETA preconditions there protects that function's own contract. Partner activity and capacity remain in `assign_order`, where selection policy belongs.

### Keep the original minimal guards

This would use fewer lines, but the original `None`-only route check allowed negative, non-numeric and non-finite times through. It also left the capacity, inactive-partner and duplicate-event defects intact. Explicit guards are a small readability cost for predictable failure behavior.

### Replace candidate collection with a one-pass best-candidate accumulator

The current dispatch builds an `options` list and then calls `min`. A one-pass accumulator could retain only the current best candidate and reduce temporary memory. It was not implemented: supplied data is small, no memory/runtime problem was measured, and the current two-stage flow makes candidate validation and ranking easy to inspect.

## 3. Current complexity and trade-offs

For `n` partner records, dispatch evaluates each record once and then finds the minimum among eligible candidates. With ordinary dictionary lookups for travel routes, expected work is linear, `O(n)`. The options list uses `O(n)` additional space in the all-eligible case. This is an analysis of the code structure, not a benchmark.

The selected design prioritizes one clear validation path for ETA computation, a separate eligibility filter, and an explicit deterministic ranking key. It avoids coercion and silent defaults. Some repetitive guards are intentional because public inputs can be malformed.

## 4. Correctness checks protecting the design

The existing suite covers the ETA formula, zero values, missing/invalid routes, preparation-time validation, current-time validation, active state, capacity boundaries, deterministic ties and cancellation behavior. `tests/test_regressions.py` adds malformed-record, overflow and input-immutability cases. The final complete run passed **235 tests**.

No separate benchmark, memory profile or comparison of alternative implementations was run.

## 5. Possible next steps

If partner volumes grow, benchmark realistic dispatch batches before changing the algorithm. A one-pass best-candidate implementation could then be compared against the current list-plus-`min` approach for runtime and allocation, while asserting identical behavior for invalid candidates, missing routes and ETA ties. Persistence for processed cancellation IDs is a separate reliability improvement; it requires an explicit storage contract and restart-oriented tests rather than an in-memory optimization.

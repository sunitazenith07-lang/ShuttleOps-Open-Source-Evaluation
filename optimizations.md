# optimizations.md - Required submission

> AI-use declaration: `AI_USAGE_TEMPLATE.md`.

## 1. Baseline and objective
- Goal was correctness first; performance was a secondary check. Measured on the full dataset (Python 3.14.3, `timeit`, best of 5 repeats): **180 `assign_order` calls over 60 partners = 0.022–0.033 s across separate runs (roughly 120–185 µs per order)**; **177 `process_cancellation` calls ≈ 0.001 s**. Timings change with machine load, so read them as an order of magnitude, not a benchmark. At this scale there is no hotspot; the work is already cheap.
- Evidence: `python -m pytest -q` runs all 288 tests in about 0.35–0.45 s. The timings come from re-running the dataset replay several times. After the final validation changes (overflow and ETA-range checks, commit `3ddc5d2`), three more best-of-5 runs each measured 0.022 s for the 180 assignments and 0.0009 s for the 177 cancellations, so the extra checks made no measurable difference.

## 2. Options considered
- **Set for `processed_cancellation_ids`** — expected benefit O(1) event lookup vs O(E) list scan. Rejected: tests assert `processed_cancellation_ids == ['C1']` (list shape is part of the contract) and event lists per partner are tiny; converting would add a parallel structure for no measurable gain.
- **Sort candidates then pick first** — rejected; `min()` with a tuple key is already single-pass O(P) and clearer.
- **Early exit when the order itself is invalid** — implemented: `assign_order`/`evaluate_candidates` skip partner evaluation entirely on a malformed order, turning a wasted O(P) scan into O(1).
- **Single-pass candidate evaluation shared by `assign_order` and `explain_assignment`** — partially implemented: both share `_evaluations`, but `explain_assignment` still runs it twice (once inside `assign_order`, once for the report). Accepted trade-off: it is a debugging/feature path, not the hot path, and keeping `assign_order`'s signature stable mattered more than avoiding one extra O(P) pass.
- **Caching travel lookups** — rejected; dict tuple-key lookup is already O(1); a cache would only add invalidation complexity.
- **Avoiding `deepcopy` in `process_cancellation`** — rejected; copy-on-write semantics are required (the original record must stay untouched, verified by `test_cancellation_does_not_mutate_original_partner`).

## 3. Changes implemented
- Change: early return on invalid order in `assign_order`/`evaluate_candidates`; shared `_evaluations` helper so selection and explanation cannot diverge; O(1) tuple-key travel lookups retained.
- Tests protecting correctness: all 288 tests, including `test_all_dataset_orders_assign_deterministically` and `test_demo_fixture_assigns_p2_with_eta_35`.
- Measurement: timings above; no attempt was made to "optimize" further because measured cost is already negligible.

## 4. Trade-offs
- Correctness/readability preferred over micro-optimisation: e.g. keeping the `processed_cancellation_ids` list preserves the public shape; `_partner_problem` returning a reason string costs a few allocations but produces explainable rejections (also powering the stretch feature).
- Memory: the only meaningful allocation is `deepcopy` per cancellation — O(size of one partner record), bounded and required for immutability semantics.
- `explain_assignment` performs two O(P) evaluation passes; documented and accepted for interface stability.
- Robustness over brevity: `_is_valid_time` catches `OverflowError`, and `estimate_eta` re-validates the final ETA. Each is one extra O(1) check per candidate, with no measured cost (see section 1). In exchange, the code cannot crash on huge ints or assign an infinite ETA.

## 5. Further improvements
- With more data: index partners by zone, keep `active_order_ids` as a set for O(1) membership in cancellation, and maintain `processed_cancellation_ids` as a set alongside a list if event volume grew. Validation: re-run the dataset replay plus a synthetic 10k-partner benchmark and compare `timeit` timings before and after.

## Complexity summary
- `estimate_eta`: O(1) — two dict lookups and arithmetic.
- `assign_order`: O(P) partners, each O(1), plus O(P) `min()`; O(P) candidate space.
- `process_cancellation`: O(A + E) where A = active orders (list `remove`/`in`) and E = processed events (list `in`); space O(partner record) for the copy.

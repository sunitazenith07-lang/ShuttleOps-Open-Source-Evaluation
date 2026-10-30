# optimizations.md

## 1. Baseline and objective
The starter was small and fast; its problem was correctness, not speed. Objectives, in priority order: (1) correctness against the contract, (2) readability — one place per rule, (3) avoid wasted work where it is free to do so. The dataset (180 orders × 60 partners, 387 routes) was used as the realistic workload.

## 2. Options considered

| Option | Expected benefit | Risk | Decision |
|---|---|---|---|
| Filter partners (active/capacity/record shape) **before** computing ETA | Skip route lookups and arithmetic for partners that can never win | None — eligibility doesn't depend on ETA | **Implemented** |
| Shared validation predicates (`_is_minutes`, `_is_id`, `_is_capacity`) | One definition of "valid time"; 5 fields validated identically | Slightly less explicit per-field messages | **Implemented** |
| Single-pass `min()` over `(eta, partner_id)` instead of sorting all candidates | O(n) vs O(n log n); no list sort needed | None | **Kept** from starter, removed `str()` coercion |
| Validate the order once in `assign_order` instead of per partner | Saves repeated checks | `estimate_eta` is public and must still be safe when called alone | **Partly** — `assign_order` rejects bad orders up front; `estimate_eta` still re-validates (cost is trivial) |
| Pre-index travel by restaurant / cache leg2 per order | leg2 is identical for every partner of an order | Extra code for a dict lookup that is already O(1) | **Rejected** — not worth the complexity |
| `processed_cancellation_ids` as a set | O(1) duplicate check | Changes the record's type; tests assert it equals a list | **Rejected** for now (see §5) |

## 3. Changes implemented
- **Eligibility pre-filter.** `assign_order` calls `partner_rejection()` first and only calls `estimate_eta()` for partners that pass. On the dataset, 27 of 60 partners pass, so ETA is computed **4,860 times instead of 10,800** across all 180 orders (counted directly).
- **Deterministic ordering without coercion.** `partner_id` is validated as a non-empty `str`, so the key `(eta_minutes, partner_id)` is a total order; no `str()` call, no mixed-type comparison. `test_dataset_assignment_is_independent_of_partner_order` shuffles all 60 partners and checks every one of the 180 assignments is unchanged. This matters: **170 of the 170 assignable dataset orders have a tie on the best ETA** (partners were generated in pairs, e.g. `PARTNER-013`/`PARTNER-033` both at 52 min for `DSP-ORD-0002`).
- **No input mutation.** `assign_order` reads only; `process_cancellation` deep-copies. Tested by `test_assign_order_does_not_mutate_inputs` and `test_cancellation_returns_copy_and_rejects_non_mapping`.

**Measurement (timeit, 50 repetitions, Python 3.14.7, local machine):**
- Full `assign_order` over all 180 orders: **≈ 6.7 ms** per pass.
- For comparison, calling the new `estimate_eta` for *every* partner with no pre-filter: **≈ 8.8 ms** per pass.

These are single-machine numbers for a small dataset; the absolute times are tiny. The real point of the filter is that inactive/full partners never reach ETA logic at all, which is also a correctness property.

## 4. Trade-offs
- Validation adds per-call checks (`isinstance`, `math.isfinite`) — a small constant cost, accepted because skipping it is what caused the 65 failures.
- Returning a `rejected` list makes the result larger (up to one entry per partner), but it is what makes an unassigned order explainable. It costs one small dict per rejected partner.
- Strict typing (`active is True`, `partner_id` must be `str`) may reject loosely-typed records that a lenient system would accept. I chose predictability over leniency.

## 5. Further improvements (not implemented, not measured)
- Store processed cancellation IDs in a set alongside the list (or keep a dispatcher-level set) for O(1) duplicate checks at scale; validate by benchmarking with thousands of events per partner.
- Batch assignment that updates the chosen partner's `active_order_ids`/workload after each order, so capacity stays consistent within a batch; validate with a test that assigns more orders than total capacity.
- Index partners by zone and pre-compute `leg1` per (zone, restaurant) when many partners share a zone.

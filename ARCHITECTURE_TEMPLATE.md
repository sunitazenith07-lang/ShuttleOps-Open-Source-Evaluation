# Architecture Notes

## Project map
- `main.py` — demo entry point: builds the sample inputs and prints one `assign_order` result.
- `fixtures.py` — returns the small demo case (one order, two partners, three travel legs).
- `models.py` — plain-dict factories `new_order` / `new_partner`; there are no classes, so records stay easy to inspect and copy.
- `service.py` — all engine logic, in layers: validation helpers (`_is_valid_time`, `_is_valid_id`, `_order_problem`, `_partner_problem`) → per-partner ETA (`estimate_eta`) → candidate evaluation (`_evaluations`, `evaluate_candidates`) → selection (`assign_order`) → the optional `explain_assignment`. `process_cancellation` is a separate state-transition path.
- `data/records.json` — the evaluation dataset (`dataset_version` 2): 180 orders, 60 partners, 387 travel records, 177 cancellation events, 10 edge-case categories. Travel is stored as `{"from","to","minutes"}` rows and converted to tuple keys before use.
- `tests/` — five files: the original acceptance matrix, contract, edge-case and dataset expectations, plus the added `test_regression.py` and `test_dataset.py` replays.

## Data model
- **Order:** `order_id`, `restaurant_id`, `destination_zone`, `prep_minutes`.
- **Partner:** `partner_id`, `zone`, `active`, `capacity`, `active_order_ids`, `workload_minutes`, `minutes_by_order` (order → its minutes, so cancellation can release exactly what it added), `processed_cancellation_ids` (event deduplication).
- **Travel:** `{(from_id, to_id): minutes}` — one dict lookup per leg, and a missing key cleanly means "no route".
- **Assignment result:** `order_id`, `partner_id`, `pickup_minutes`, `eta_minutes`, `reason` — the same five keys whether assigned or not (`None` for the values when unassigned).
- **Evaluation** (`explain_assignment`): per-partner verdict — the ETA or the rejection reason.

## Data flow
1. The caller passes `order`, `partners`, `travel`, `now` into `assign_order`.
2. `_order_problem` validates the order first; a malformed order returns an unassigned result immediately.
3. Each partner goes through `_partner_problem` (active flag, capacity vs `active_order_ids`, well-formed fields), then `estimate_eta`, which requires both travel legs: `partner.zone → restaurant_id` and `restaurant_id → destination_zone`.
4. `pickup = now + partner_to_restaurant + workload`; `eta = pickup + prep + restaurant_to_customer`. Non-finite results are rejected.
5. `min()` on `(eta, str(partner_id))` picks the lowest ETA with ascending lexicographic tie-break. If nobody qualifies, the rejection reasons are counted into `reason`.
6. Cancellation path: `process_cancellation` deep-copies the partner, skips already-seen `event_id`s, removes the order from `active_order_ids`, releases its minutes from `workload_minutes` via `minutes_by_order`, and records the event. Malformed state is left untouched rather than overwritten.

## Storage design
- Everything is in-memory Python dicts and lists; the service layer does no I/O, which keeps it deterministic and trivially testable.
- Travel uses tuple keys because the lookup is O(1) and `travel.get((a, b))` returning `None` is exactly the "missing route" signal the rules need — missing travel is never treated as zero.
- `minutes_by_order` exists so cancellation releases the same minutes an order contributed, instead of guessing from the aggregate `workload_minutes`.
- `records.json` is converted at load time (rows → tuple keys), so the on-disk format can stay a flat table while the engine uses the mapping it expects.

## Diagram
```
caller (main.py / tests)
  │  order, partners[], travel{}, now
  ▼
assign_order ── _order_problem ──► invalid order ──► unassigned result
  │ per partner
  ├─ _partner_problem ──► inactive / full / malformed ──► skip
  └─ estimate_eta ── needs legs (zone→rest) + (rest→dest)
        │
        ▼
   min(eta, partner_id) ──► assigned result
        │ none eligible
        ▼
   unassigned result + reason counts

explain_assignment: same scan, returns every candidate's verdict.

process_cancellation(partner, order_id, event_id)
  └─ deep copy → event already processed? → remove order →
     release minutes_by_order[order] from workload → record event id
```

## Three improvements suggested
1. **Set-based lookups at scale:** `active_order_ids`, `processed_cancellation_ids` and `minutes_by_order` membership are O(1) as sets/dict keys; converting and re-benchmarking with `timeit` would matter only on much larger data than the current dataset.
2. **Zone indexing:** a `zone → partners` index would let the engine skip partners guaranteed to lack the first travel leg, reducing the candidate scan on large inputs.
3. **ID-less cancellation events:** today a cancellation with no `event_id` dedupes as first-per-partner, so a second genuinely different ID-less event is ignored. If the specification required those events, deduplicating by `order_id` instead would be the fix — applied only after re-running the dataset replay to confirm no regression.

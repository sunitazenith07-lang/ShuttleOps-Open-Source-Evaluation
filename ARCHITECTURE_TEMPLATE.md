# Architecture Notes

## Project map
- `models.py` — Factory functions (`new_partner`, `new_order`) that initialize standard dictionary structures for delivery partners and customer orders.
- `service.py` — Core domain logic containing:
  - `_is_non_empty_str` & `_is_non_neg_num`: Input validation helpers (enforcing non-empty strings and finite, non-boolean, non-negative numbers via `math.isfinite`).
  - `estimate_eta`: Computes pickup and delivery ETA for a single `(order, partner)` pair using a travel lookup table.
  - `assign_order`: Filters eligible partners, computes ETAs, and selects the optimal partner using lowest ETA and lexicographic `partner_id` tie-breaking.
  - `process_cancellation`: Pure/immutable state transition function that idempotently removes a cancelled order from a partner and releases associated workload.
- `fixtures.py` — Sample order, partner list, and zone-to-restaurant travel matrix for local testing and demonstrations.
- `main.py` — CLI entry point that loads `sample_inputs()` and prints the result of `assign_order()`.

## Data model
- **Order (`dict`)**:
  - `order_id` (`str`): Unique non-empty order identifier (e.g., `'O-7'`).
  - `restaurant_id` (`str`): Origin restaurant identifier (e.g., `'R-2'`).
  - `destination_zone` (`str`): Customer delivery zone identifier (e.g., `'Z-9'`).
  - `prep_minutes` (`int | float`): Finite, non-negative food preparation time in minutes.
- **Partner (`dict`)**:
  - `partner_id` (`str`): Unique non-empty partner identifier (e.g., `'P-1'`).
  - `zone` (`str`): Partner's current zone location (e.g., `'Z-3'`).
  - `active` (`bool`): Availability flag; must be strictly `True` for assignment.
  - `capacity` (`int`): Maximum number of concurrent active orders allowed.
  - `active_order_ids` (`list[str]`): List of currently assigned order IDs.
  - `workload_minutes` (`int | float`): Finite, non-negative remaining busy minutes across active orders.
  - `minutes_by_order` (`dict[str, int | float]`): Mapping of `order_id -> workload minutes` used to release workload upon cancellation.
  - `processed_cancellation_ids` (`list[str]`): Log of processed cancellation `event_id`s to guarantee idempotency.
- **Travel Matrix (`dict[tuple[str, str], int | float]`)**:
  - Maps `(origin_zone_or_restaurant, destination_restaurant_or_zone)` tuples to finite, non-negative travel times in minutes.

## Data flow
1. **Order Assignment (`assign_order`)**:
   - Receives `order`, `partners`, `travel`, and `now`.
   - Validates `order` fields (`order_id`, `restaurant_id`, `destination_zone`, `prep_minutes`), `now` (confirming finite, non-negative numbers), and container types. If invalid, immediately returns an unassigned result dictionary.
   - Iterates through `partners`, skipping malformed records, inactive partners (`active is not True`), partners at or above capacity (`len(active_order_ids) >= capacity`), and partners with negative or non-finite workload.
   - Calls `estimate_eta(order, partner, travel, now)` for each candidate to look up `leg1` `(partner.zone, order.restaurant_id)` and `leg2` `(order.restaurant_id, order.destination_zone)` and verify both legs are finite non-negative numbers.
   - Collects all eligible estimates and selects the minimum using `(eta_minutes, str(partner_id))`.
2. **Order Cancellation (`process_cancellation`)**:
   - Receives `partner`, `order_id`, and `event_id`.
   - Deep-copies `partner` and sanitizes internal lists and workload values.
   - Checks if `event_id` is valid and not already in `processed_cancellation_ids`.
   - Removes `order_id` from `active_order_ids`, subtracts `minutes_by_order.get(order_id, 0)` from `workload_minutes` (floored at `0`), appends `event_id` to `processed_cancellation_ids`, and returns the updated copy.

## Storage design
- **In-Memory Dictionary State**: All entities (`order`, `partner`, `travel`) are stored as plain Python dictionaries and lists in memory with zero external database dependencies.
- **Immutability on State Transitions**: `process_cancellation` uses `copy.deepcopy` before modifying partner fields, ensuring functional purity and preventing unintended side effects on caller references.
- **O(1) Route & Workload Lookups**: Travel legs use tuple-keyed dictionaries `travel[(from, to)]` and per-order workloads use `minutes_by_order[order_id]` for constant-time $O(1)$ lookups.

## Diagram
```
[Input: order, partners, travel, now]
                 │
                 ▼
      ┌─────────────────────┐
      │ Validate Order &    │──(Invalid / Non-finite)──► Return Unassigned
      │ Global Time (now)   │                            (reason: invalid order/time)
      └──────────┬──────────┘
                 │ (Valid)
                 ▼
      ┌─────────────────────┐
      │ Filter Partners:    │
      │ - active is True    │
      │ - orders < capacity │
      │ - finite workload>=0│
      └──────────┬──────────┘
                 │
                 ▼
      ┌─────────────────────┐
      │ estimate_eta():     │
      │ - Lookup leg1, leg2 │
      │ - Check isfinite>=0 │
      │ - pickup = now +    │
      │   leg1 + workload   │
      │ - eta = pickup +    │
      │   prep + leg2       │
      └──────────┬──────────┘
                 │
                 ▼
      ┌─────────────────────┐
      │ Any Eligible?       │──(No)────────────────────► Return Unassigned
      └──────────┬──────────┘                            (reason: no eligible partner)
                 │ (Yes)
                 ▼
      ┌─────────────────────┐
      │ Select min() by:    │
      │ (eta, partner_id)   │
      └──────────┬──────────┘
                 │
                 ▼
       [Return Assigned Result]
```

## Three improvements suggested
1. **Replace Plain Dictionaries with Typed `dataclasses` or `Pydantic` Models**: Moving from raw dictionaries to `dataclass` or `Pydantic` schemas would enforce type safety and finite-number validation at object creation time rather than requiring repetitive `isinstance` and `math.isfinite` checks across service functions.
2. **Overlap Restaurant Preparation Time with Partner Travel (`max` vs. `+`)**: Currently, the specification mandates `eta = pickup + prep_minutes + leg2`. In a real-world dispatch system, restaurants prepare food while the courier travels to the restaurant, so modeling departure from the restaurant as `max(pickup, now + prep_minutes) + leg2` would yield more realistic ETAs.
3. **Use a `set` (or Bounded LRU Cache) for `processed_cancellation_ids`**: Checking `event_id in out['processed_cancellation_ids']` on a Python `list` is $O(N)$. Converting `processed_cancellation_ids` to a `set` (or maintaining an indexed idempotency store) would reduce duplicate-event lookups to $O(1)$ as history grows.
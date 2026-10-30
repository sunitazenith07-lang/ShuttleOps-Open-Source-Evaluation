# Architecture Notes

## Project map
- `models.py`: Factory helper functions (`new_order`, `new_partner`) that construct standardized dictionary payloads.
- `service.py`: Core dispatch and state logic containing validation helpers (`_is_valid_number`, `_is_valid_time`, `_valid_order`, `_valid_partner_for_assignment`) and the public API (`estimate_eta`, `assign_order`, `process_cancellation`).
- `fixtures.py`: Synthetic sample orders, delivery partner states, and zone-to-zone travel time maps.
- `main.py`: CLI entry point that runs the offline simulation against synthetic fixture data.
- `tests/`: Automated pytest test suite (`test_contract.py`, `test_edge_cases.py`, `test_acceptance_matrix.py`).

## Data model
- **Order (`dict`):** `order_id` (`str`), `restaurant_id` (`str`), `destination_zone` (`str`), and `prep_minutes` (`int | float >= 0`).
- **Partner (`dict`):** `partner_id` (`str`), `zone` (`str`), `active` (`bool`), `capacity` (`int >= 1`), `active_order_ids` (`list[str]`), `workload_minutes` (`int | float >= 0`), `minutes_by_order` (`dict[str, int | float]`), and `processed_cancellation_ids` (`list[str]`).
- **Travel Matrix (`dict`):** Mapping of `(origin_zone_or_restaurant, destination_restaurant_or_zone)` tuples to non-negative travel times (`int | float >= 0`).

## Data flow
- **Assignment flow:** `assign_order` validates the incoming `order` -> loops through `partners` and filters out inactive or full candidates via `_valid_partner_for_assignment` -> calls `estimate_eta` for each valid candidate (`pickup = now + leg1 + workload`, `eta = pickup + prep + leg2`) -> selects the eligible partner with the minimum `(eta_minutes, str(partner_id))` -> returns the dispatch result dict.
- **Cancellation flow:** `process_cancellation` receives a `partner`, `order_id`, and `event_id` -> deep-copies the partner dict -> checks if `event_id` is already in `processed_cancellation_ids` (returning early if so) -> removes `order_id` from `active_order_ids`, subtracts its minutes from `workload_minutes` (floored at `0`), records `event_id`, and returns the updated partner dict.

## Storage design
- Purely in-memory, stateless functional design using standard Python dictionaries, lists, and tuple-keyed lookup maps (`fixtures.py` for static simulation data).
- State transitions (such as `process_cancellation`) use `copy.deepcopy` to return new dictionary snapshots rather than mutating caller objects in place, avoiding side effects across retries.

## Diagram
```text
[Order + Partners + Travel Map]
              |
              v
      +---------------+
      | assign_order  | ---> (Invalid Order) ---> [Return Unassigned]
      +---------------+
              |
  (_valid_partner_for_assignment)
              |
              v
      +---------------+
      | estimate_eta  | ---> (Missing/Bad Route) -> [eligible: False]
      +---------------+
              |
      (eligible: True)
              |
              v
 [Min (eta_minutes, partner_id)] ---> [Return Assigned Partner & ETA]
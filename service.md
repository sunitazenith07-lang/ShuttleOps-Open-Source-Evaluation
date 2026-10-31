# Dispatch Service

`service.py` contains the core ETA, partner-assignment, and cancellation
behavior for SmartDispatch. It is a small, in-memory service: it accepts Python
mappings and a travel-time mapping, returns dictionaries, and does not read or
write files, call external services, or persist assignment state.

## Data expected by the service

Orders and partners are dictionaries in the format created by `models.py`.
Equivalent mapping objects are accepted by the ETA and assignment functions.

An order used for ETA calculation or assignment needs:

| Field | Requirement |
|---|---|
| `order_id` | Non-empty string |
| `restaurant_id` | Non-empty string |
| `destination_zone` | Non-empty string |
| `prep_minutes` | Non-negative finite integer or float; booleans are not accepted |

A partner used for assignment needs:

| Field | Requirement |
|---|---|
| `partner_id` | Non-empty string |
| `zone` | Non-empty string |
| `active` | Exactly `True` |
| `capacity` | Positive integer; booleans are not accepted |
| `active_order_ids` | List or tuple with fewer entries than capacity |
| `workload_minutes` | Optional for ETA; defaults to `0`, otherwise must be a non-negative finite number |

Travel times are supplied as a mapping with tuple keys:

```python
travel = {
    (partner_zone, restaurant_id): minutes_to_restaurant,
    (restaurant_id, destination_zone): minutes_to_customer,
}
```

Both route entries are required for an ETA. A travel time must be a
non-negative finite integer or float. Zero is valid; missing or invalid values
are not treated as zero.

## Public functions

### `estimate_eta(order, partner, travel, now=0)`

Calculates a single partner's pickup time and delivery ETA. The `now` value is
the current time in the same minute-based units used by the route, workload,
and preparation values. It must be non-negative and finite.

The calculations are:

```text
pickup_minutes = now + partner_to_restaurant_travel + workload_minutes
eta_minutes = pickup_minutes + prep_minutes + restaurant_to_destination_travel
```

For valid input and route data, it returns:

```python
{
    "partner_id": "P-1",
    "pickup_minutes": 13,
    "eta_minutes": 35,
    "eligible": True,
}
```

If the order, partner zone, time values, travel mapping, or either route is
invalid or missing, it returns an ineligible result with `eta_minutes=None`.
The helper estimates an ETA only; partner activity and capacity are checked by
`assign_order`, not by this function.

### `assign_order(order, partners, travel, now=0)`

Validates the order, filters the supplied partner list, estimates ETAs for
remaining candidates, and assigns the order to the best candidate. Candidates
must have valid identifiers and zones, `active is True`, a valid positive
capacity, and fewer active orders than that capacity. They must also have
valid travel data and time inputs.

The selected candidate has the lowest ETA. Equal ETAs are resolved by
ascending lexicographic `partner_id`, independently of candidate input order.

A successful result contains the order ID, partner ID, pickup time, ETA, and
`"assigned"` reason:

```python
{
    "order_id": "O-7",
    "partner_id": "P-2",
    "pickup_minutes": 13,
    "eta_minutes": 35,
    "reason": "assigned",
}
```

An invalid order returns no partner, a `None` ETA, and reason
`"invalid order data"`. If the order is valid but no partner qualifies, the
result has no partner, a `None` ETA, and reason
`"no eligible partner or missing time data"`.

### `process_cancellation(partner, order_id, event_id)`

Returns an updated deep copy of a partner mapping; the input mapping is not
modified. A valid, previously unseen event ID is recorded. If the order is
currently active, it is removed and its per-order workload is subtracted from
`workload_minutes`, with the result clamped at zero. A repeated event ID does
not apply the cancellation again.

An event ID must be a non-empty string to be processed. An invalid event ID
returns the copied partner state without applying or recording the event. A
valid event for an unknown or inactive order does not release workload, but
the event is recorded so repeated delivery remains idempotent.

The optional cancellation fields are `active_order_ids` and
`processed_cancellation_ids` (lists), `minutes_by_order` (a mapping), and
`workload_minutes` (a non-negative finite number). If the per-order minutes or
current workload are invalid or missing, the order is still removed but the
workload value is left unchanged.

## Worked example

```python
order = {
    "order_id": "O-7",
    "restaurant_id": "R-2",
    "destination_zone": "Z-9",
    "prep_minutes": 10,
}
partner = {
    "partner_id": "P-2",
    "zone": "Z-1",
    "active": True,
    "capacity": 2,
    "active_order_ids": [],
    "workload_minutes": 5,
}
travel = {
    ("Z-1", "R-2"): 8,
    ("R-2", "Z-9"): 12,
}
```

With `now=0`, pickup is `0 + 8 + 5 = 13` minutes, and ETA is
`13 + 10 + 12 = 35` minutes. The offline demo in `main.py` uses this scenario
and prints a successful assignment to `P-2`.

## Running and testing

Run the automated tests from the repository root:

```powershell
python -m pytest -q
```

Run the offline example:

```powershell
python -m main
```

See [TESTING.md](./TESTING.md) for the recorded test environment, results, and
edge-case coverage.

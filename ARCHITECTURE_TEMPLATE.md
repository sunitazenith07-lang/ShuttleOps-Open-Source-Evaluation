# Architecture notes

## Project map

- `service.py` has the rules for choosing a delivery partner and handling cancellations.
- `models.py` makes example order and partner records.
- `main.py` runs a small example.
- `data/` holds the sample records, and `tests/` holds the checks for the code.

## Data model

An order has an ID, a restaurant, a destination, and a preparation time. A partner has an ID, a location, a capacity, and information about its current orders and workload. Travel times are kept in a dictionary that maps one route to its time.

## Data flow

The program checks the order and the partners. It skips partners that are inactive, full, or missing needed travel times. For the remaining partners, it works out an ETA and picks the lowest one. If two ETAs are equal, it picks based on the partner ID. Cancellation handling removes an order from a partner and avoids applying the same event twice.

## Storage design

The program keeps orders and partner details in Python dictionaries and lists while it runs. Sample data is kept in files in `data/`. It does not use a database.

## Diagram

```text
Order + partners + travel times
               |
               v
        Check and estimate
               |
               v
        Choose a partner
```

## Three improvements suggested

1. Save partner updates so they are still available after the program stops.
2. Check input records early and show a clear message when something is missing.
3. Update a partner's workload after assigning an order, so the next assignment uses the latest information.

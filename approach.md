# 🧭 Approach and Implementation

## Baseline

| Check | Recorded result |
|---|---|
| Python | 3.14.7 (project requirement: 3.10+) |
| Starter tests | 65 failed, 164 passed |
| Offline demo | Assigned O-7 to P-2; pickup 13 min; ETA 35 min |
| Dependency installation | Ran python -m pip install -r requirements-dev.txt; pytest 9.1.1 already satisfied the requirement |

Commands used: python -m pytest -q and python -m main.

## Code flow reviewed

- models.py creates the order and partner records.
- fixtures.py supplies the synthetic inputs for the offline demo.
- main.py passes those inputs to assign_order() and prints its result.
- service.py validates records, estimates candidate ETAs, chooses a partner, and processes cancellations.
- The visible tests and the test workflow were reviewed to understand expected behavior and automated checks.

## Investigation and implementation

| Observed issue | Change in service.py | Reason |
|---|---|---|
| Invalid, missing, or non-finite time values could be accepted or cause arithmetic errors. | Added validation for finite, non-negative numeric values and required identifiers. | Invalid data must not produce a misleading ETA or crash the calculation. |
| Inactive or full partners could be selected. | Added a partner status and capacity check before ETA calculation. | Only active partners with an available slot can receive an order. |
| Duplicate cancellation IDs were recorded without being checked first. | Check the event ID before changing active orders or workload. | Repeated delivery events must not release workload twice. |

The ETA formula remains:

- Pickup = current time + partner-to-restaurant travel + remaining partner workload.
- ETA = pickup + restaurant preparation + restaurant-to-customer travel.

Missing travel data is rejected rather than treated as zero. Candidates are compared by ETA, then partner ID in ascending lexicographic order.

## Design decisions

- Reject malformed values instead of silently converting them. For example, the string "10" is not accepted as ten minutes.
- Keep validation and assignment logic in service.py, where those inputs are consumed.
- Use a deep copy when processing a cancellation so the input partner record is not changed in place.
- Keep the implementation focused on required behavior; no optional stretch feature was added.

## Verification

| Command | Result |
|---|---|
| python -m pytest -q | 233 passed |
| python -m main | Completed; O-7 assigned to P-2, pickup 13 min, ETA 35 min |
| git diff --check | Passed |

Added tests/test_regressions.py with four regression cases; existing tests were not changed. GitHub pull-request CI and hidden evaluation checks have not been run.

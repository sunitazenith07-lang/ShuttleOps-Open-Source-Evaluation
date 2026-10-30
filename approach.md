# 🧭 Approach and Implementation

## Baseline and evidence

| Check | Recorded result |
|---|---|
| Python | 3.14.7 (project requirement: 3.10+) |
| Starter test run | `python -m pytest -q` → 65 failed, 164 passed |
| Offline demo before/final check | `python -m main` → O-7 assigned to P-2; pickup 13 min; ETA 35 min |
| Dependency setup | Ran `python -m pip install -r requirements-dev.txt`; pytest 9.1.1 was already installed and satisfied the requirement |

The initial test failures showed that the starter had incomplete behavior. The test output and assertions were used to group the failures around time validation, partner eligibility/capacity, and duplicate cancellation handling.

## Code and data flow explored

- `models.py` creates order and partner dictionaries.
- `fixtures.py` builds the small synthetic inputs used by the offline demo.
- `main.py` passes those inputs to `assign_order()` and prints the result.
- `service.py` validates inputs, estimates ETAs, chooses a partner, and processes cancellation events.
- The tests define expected edge behavior. The workflow file shows what automated checks run.
- The expanded `data/records.json` uses travel rows, while the service expects tuple-key mappings. A regression test converts the rows to the service's expected format and exercises a complete route.

## Investigation and implementation

| Observed issue | Change in `service.py` | Reason |
|---|---|---|
| Invalid, missing, or non-finite time values could be accepted or cause arithmetic errors. | Validate finite, non-negative numeric values and required identifiers before ETA arithmetic. | Invalid data should not produce a misleading ETA or crash the calculation. |
| Inactive or full partners could be selected. | Check active status and valid available capacity before estimating ETA. | Only active partners with an open slot can receive an order. |
| Duplicate cancellation IDs were recorded without being checked first. | Check the event ID before changing active orders or workload. | Repeated delivery events must not release workload twice. |
| Missing travel data could be interpreted as a usable time or fail later in arithmetic. | Require both route legs and reject missing/invalid values. | The service cannot infer a travel duration that was not supplied. |

The ETA formula is:

- **Pickup** = current time + partner-to-restaurant travel + remaining partner workload.
- **ETA** = pickup + restaurant preparation + restaurant-to-customer travel.

Missing travel data is rejected rather than treated as zero. Candidates are compared by ETA, then partner ID in ascending lexicographic order.

## Design decisions and alternatives

- Reject malformed values instead of silently converting them. For example, the string `"10"` is not accepted as ten minutes.
- Keep validation and assignment logic in `service.py`, where the values are consumed.
- Use a deep copy for cancellation processing so the input partner object is not changed in place.
- Check cancellation event IDs before applying state changes.
- Use a simple candidate scan and `min()` selection. Sorting all candidates was unnecessary because only the best candidate is returned.
- Keep the implementation focused on required behavior; no optional stretch feature was added.

## Verification

| Command | Recorded result |
|---|---|
| `python -m pytest -q` | 233 passed |
| `python -m main` | Completed; O-7 assigned to P-2, pickup 13 min, ETA 35 min |
| `git diff --check` | Passed |

Added `tests/test_regressions.py` with four regression cases: duplicate cancellation ID with a different payload and original-input preservation, huge integer time rejection, malformed assignment/travel inputs, and assignment using routes converted from `data/records.json`. Existing test files were not changed or weakened. GitHub pull-request CI and hidden evaluation checks have not been run.


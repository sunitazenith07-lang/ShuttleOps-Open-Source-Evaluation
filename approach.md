# approach.md

## 1. Baseline
- Commands run before editing:
  - `python -m pytest -q`
- Initial test result:
  - The starter suite failed heavily before I changed the dispatch logic. The failure pattern showed missing validation for missing/invalid travel routes, partner capacity checks, and duplicate cancellation handling.
- Demo/output observed:
  - I did not record a pre-fix `python -m main` run before editing. After the fix, the demo output was `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.

## 2. Codebase understanding
- Important files/functions inspected:
  - `models.py` for `new_order()` and `new_partner()` data shapes.
  - `service.py` for `estimate_eta()`, `assign_order()`, and `process_cancellation()`.
  - `fixtures.py` for the sample order and partner inputs used in the offline demo.
  - `tests/test_contract.py`, `tests/test_edge_cases.py`, and `tests/test_acceptance_matrix.py` for the acceptance contract and edge-case checks.
- Candidate filtering, ETA calculation, and capacity flow traced:
  - An order should only be assigned to a partner that is active, below capacity, and has valid route data for both legs.
  - ETA is `pickup = now + partner_to_restaurant + workload`, then `pickup + prep + restaurant_to_destination`.
  - When several partners have the same ETA, the lower partner ID string wins.
- How I confirmed my understanding:
  - I read the problem statement and the test assertions together, then traced each failing case back to the logic in `service.py`.

## 3. Investigation and implementation strategy
- Issue 1: missing or invalid route times were not being rejected, so `estimate_eta()` could hand back a false-positive result.
  - Evidence: failing tests in `test_invalid_or_missing_travel_time_rejected` and `test_eta_is_ineligible_when_either_required_route_is_missing`.
  - Fix: validate route values as finite, non-negative numbers before computing ETA.
- Issue 2: inactive or full partners were still being considered candidates.
  - Evidence: `test_inactive_partner_not_assigned`, `test_full_partner_not_assigned`, and the capacity matrix cases.
  - Fix: `assign_order()` now filters to `active is True` and `len(active_order_ids) < capacity`.
- Issue 3: duplicate cancellations could release the same workload twice because event IDs were recorded before checking for duplicates.
  - Evidence: `test_duplicate_cancellation_is_idempotent` and the repeated-workload cancellation coverage.
  - Fix: return early if the event ID was already processed, and only release workload after confirming the order is active for that partner.

## 4. Implementation decisions
- Main changes and why:
  - Added validation helpers in `service.py` to reject malformed IDs, NaN/inf values, negative times, and invalid booleans.
  - Kept the ETA formula explicit and deterministic: `pickup_minutes` and `eta_minutes` are computed directly, and the winner is selected by `(eta_minutes, partner_id)`.
  - Ensured `process_cancellation()` is idempotent by checking the event ID before mutating `active_order_ids`, `minutes_by_order`, or `workload_minutes`.
- Alternatives considered and why rejected:
  - Hard-coding a single fixture result would have satisfied one demo but failed the contract and validation tests.
  - I avoided adding extra state or a global cache because the project is small and the solution should remain simple and predictable.
- Assumptions:
  - `capacity` is a positive integer; values like `0`, negative numbers, `None`, booleans, and strings are not valid.
  - `workload_minutes` and travel times are treated as non-negative, finite numbers; missing fields are rejected rather than assumed to be zero.

## 5. Verification
- Tests added or changed:
  - Added regression checks for missing partner IDs and invalid capacity handling in `tests/test_edge_cases.py`.
- Commands run and actual results:
  - `python -m pytest -q` -> `231 passed in 0.25s`
  - `python -m main` -> `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`
- Edge cases verified:
  - missing route data
  - negative prep time
  - inactive partner
  - full capacity
  - duplicate cancellation
  - tie-break by partner ID
- Remaining failures or known limitations:
  - None observed in the current repository; the visible suite passes and the demo runs successfully.
# approach.md

## 1. Baseline

- I used `python3 -m pytest -q` before the fixes in this debugging session.
- The result at that point was **65 failed, 164 passed**. The failures showed that several parts of the starter logic were incomplete.
- `python3 -m main` ran and printed an assignment for order `O-7`: partner `P-2`, pickup time `13`, ETA `35`.

## 2. Codebase understanding

- I looked at `service.py`, the helper functions in `models.py`, the example data in `fixtures.py`, and the tests under `tests/`.
- `estimate_eta` calculates pickup time and ETA. `assign_order` filters partners and chooses the lowest ETA. `process_cancellation` removes an order and its workload.
- The test cases helped show which inputs each function needed to handle.

## 3. Investigation and implementation strategy

- **Travel, prep, current time and workload:** Some invalid time values were still accepted or caused a type error. I used `is_valid_minutes` to check that each value is a finite, non-negative number before doing the ETA calculation.
- **Order fields:** An empty order ID could still be assigned. I added `is_valid_identifier` and return an unassigned result if the order ID, restaurant ID or destination zone is empty or not a string.
- **Partner selection:** Inactive partners and partners at capacity were still considered. `assign_order` now skips partners that are not active `True`, have invalid capacity data, or have no open capacity.
- **Cancellations:** Repeating the same event recorded its ID twice. `process_cancellation` now returns without applying an event that is already recorded.
- **Dataset records:** Processing the supplied records showed that orders marked `CANCELLED` could still be assigned and that some cancellation events had no event ID. Cancelled orders now stay unassigned, and events without a usable ID leave partner data unchanged.

I used an AI assistant to help interpret test failures and make/check changes after I confirmed with my instructor that this kind of help was allowed.

## 4. Implementation decisions

- I reused `is_valid_minutes` for all ETA values that need to be non-negative times instead of adding a separate check for each bad input.
- I kept the ETA formula the same and added checks before the arithmetic.
- For partner activity, I require `active` to be exactly `True`; values such as `1` or `"yes"` do not count as active.
- I did not add performance optimizations. The work was about correctness.

## 5. Verification

- Added workload regression cases to `tests/test_acceptance_matrix.py` and dataset integration tests for all 180 orders and 177 cancellation events.
- After the changes, `python3 -m pytest -q` reported **237 passed**.
- `python3 -m main` ran and printed `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.
- I also ran focused tests for invalid time values, inactive partners, capacity limits, cancellation duplicates and invalid order fields; the focused groups passed.
- Hidden tests are not available in the repository.

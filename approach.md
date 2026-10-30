1. Baseline & Initial State

When I first cloned the repository and ran the test suite, here is what I observed:
- Ran `python -m pip install -r requirements-dev.txt` (installed pytest 9.2.0 and dependencies).
- Ran `python -m pytest -q`, which resulted in: **65 failed, 164 passed** (as expected from the brief, the starter code had intentional gaps in validation and edge-case handling).
- Running `python -m main` gave a clean demo output `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`, but the underlying logic was missing safety guards for malformed or edge-case data.


2. Codebase Overview

I spent some time exploring the core modules:
- `service.py`: Contains the main decision logic (`estimate_eta`, `assign_order`, `process_cancellation`).
- `models.py`: Simple dict-factory helpers (`new_partner`, `new_order`).
- `fixtures.py`: Sample test orders, partners, and travel maps.
- `tests/`: Extensive contract, acceptance matrix, and edge case test suites.

My initial review of `service.py` confirmed that while the core ETA arithmetic formulas were outlined, eligibility checks (active status, capacity limits), travel-time validation (preventing negative/zero/missing data bypasses), and cancellation idempotency were incomplete.


3. Key Issues Fixed

I focused my changes strictly inside `service.py` without touching the models, fixtures, or existing test files:

- **Travel Time Validation:**
  - *Problem:* Negative travel times, strings, booleans, and `NaN`/`inf` were either slipping through or causing runtime errors.
  - *Fix:* Implemented a strict `_is_valid_travel_time()` helper to validate numeric types (excluding booleans since Python treats `bool` as a subclass of `int`), non-negative values, and finite ranges. Missing travel data is now correctly treated as unknown rather than zero.

- **Active Status & Capacity Filtering:**
  - *Problem:* Inactive partners and partners at full capacity were being assigned orders.
  - *Fix:* Added `_is_eligible_partner()` to ensure partners have `active=True`, valid positive capacity, and active order counts strictly below their limit.

- **Cancellation Idempotency:**
  - *Problem:* Calling `process_cancellation()` twice with the same `event_id` released workload and capacity twice.
  - *Fix:* Added an explicit check at the top of `process_cancellation()` to return early if the `event_id` is already in `processed_cancellation_ids`.

- **Robust Input & Order Validation:**
  - *Problem:* Malformed order IDs, `None` fields, and negative preparation times were being processed.
  - *Fix:* Added input validation guards for order attributes and numeric ranges (`now`, `prep_minutes`).


4. Testing & Verification

To ensure high confidence, I added a new test file `tests/test_regressions.py` covering 71 additional edge cases across various failure modes, while leaving all existing tests untouched.

- **Final Test Suite Run:** `python -m pytest -q`
- **Result:** **300 passed in 0.30s** (229 original tests + 71 new regression tests).
- **Demo Check:** `python -m main` runs successfully and outputs valid deterministic assignments.

All requirements, edge cases, and tie-breaking rules (lexicographic partner ID sorting on ETA ties) are fully satisfied.
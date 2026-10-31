# approach.md - Required submission

> Status note: This draft distinguishes inspected starter-code behavior from proposed changes. Update the implementation and verification sections after running the code and tests yourself.

## 1. Baseline
- Commands run before editing: Not reported. The repository was cloned and the starter files were available locally, but no baseline command output has been provided.
- Initial test result (include the actual summary): Not available; no pytest summary has been supplied.
- Demo/output observed: The supplied `fixtures.py` defines an order `O-7`, restaurant `R-2`, destination `Z-9`, and two partners. The expected result can be calculated from the fixture, but an actual execution result has not been reported.

## 2. Codebase understanding
- Important files/functions inspected:
  - `service.py`: `estimate_eta`, `assign_order`, `process_cancellation`.
  - `models.py`: `new_order`, `new_partner`.
  - `fixtures.py`: `sample_inputs`.
  - `main.py`: invokes `sample_inputs()` and prints `assign_order(...)`.
- Candidate filtering, ETA calculation, and capacity flow traced:
  - The starter `assign_order` loops over partners, calls `estimate_eta`, retains estimates marked eligible, and chooses the minimum `(eta_minutes, str(partner_id))`.
  - The starter `estimate_eta` looks up partner-to-restaurant and restaurant-to-destination travel entries. It rejects a missing entry, but does not validate all input values.
  - The starter assignment logic does not enforce active status or capacity.
  - The starter cancellation function removes an active order and subtracts its recorded workload, but does not check whether the cancellation event ID was already processed.
- How you confirmed your understanding: By inspecting the supplied function bodies and following the call from `main.py` to `fixtures.py` and `service.py`. Runtime confirmation is still pending.

## 3. Investigation and implementation strategy
- Issue 1: Input validation is incomplete in the starter implementation. The ETA calculation can receive malformed identifiers or invalid/negative time values. Proposed fix: validate identifiers and finite, non-negative numeric values before arithmetic.
- Issue 2: Candidate filtering omits active-status and capacity checks. Proposed fix: consider only active partners whose active-order count is below capacity.
- Issue 3: Cancellation event IDs are appended without first checking for duplicates. Proposed fix: make cancellation processing idempotent by checking the event ID before changing active orders or workload.
- Evidence: These defects are visible in the supplied starter function bodies. No failing test output or runtime log has been supplied.

## 4. Implementation decisions
- Main changes and why:
  - Keep the public function names and result dictionaries to reduce unnecessary interface changes.
  - Reject missing travel entries explicitly; do not treat missing travel data as zero.
  - Calculate pickup as current time + partner-to-restaurant travel + remaining workload.
  - Calculate ETA as pickup + restaurant preparation + restaurant-to-customer travel.
  - Select by ETA, then partner ID in ascending lexicographic order.
  - Check a cancellation event ID before releasing workload.
- Alternatives considered and why rejected:
  - Replacing missing travel data with zero was rejected because it creates an unjustifiably optimistic ETA.
  - Selecting the first eligible partner was rejected because it does not guarantee the lowest ETA.
  - Reprocessing duplicate cancellation events was rejected because it can release workload more than once.
- Assumptions:
  - `active_order_ids` is the source of truth for the number of occupied order slots.
  - `minutes_by_order` maps an active order ID to the workload minutes to release on cancellation.
  - Travel data is keyed by `(origin_zone, destination_id_or_zone)` tuples, matching the starter fixture.
  - The `now` argument and all time values use the same unit, which the starter names as minutes.

## 5. Verification
- Tests added or changed: None confirmed in the supplied conversation.
- Commands run and actual results: No test command/result has been reported. Do not enter a passing result until it has actually been run.
- Edge cases to verify:
  1. Missing partner-to-restaurant travel entry.
  2. Missing restaurant-to-customer travel entry.
  3. Inactive partner and partner at capacity.
  4. Equal ETAs with different partner IDs.
  5. Duplicate cancellation event.
  6. Negative, boolean, non-numeric, NaN, or infinite time values.
  7. Empty partner list and malformed partner records.
- Remaining failures or known limitations:
  - The proposed implementation has not been confirmed as applied or tested.
  - The exact hidden-test interface and expected reason strings are unknown.
  - Cancellation behavior when workload metadata is malformed needs an explicit policy and tests.

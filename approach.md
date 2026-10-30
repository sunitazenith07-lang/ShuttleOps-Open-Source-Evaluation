# approach.md - Required submission

## 1. Baseline
- Commands run before editing:
  - `py -m pytest -q` on the starter (`main` branch), Python 3.13.15.
  - `py -m main` for the offline demo.
- Initial test result: **65 failed, 164 passed** (229 total) in 0.60s.
- Demo/output observed: `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.

## 2. Codebase understanding
- Important files/functions inspected:
  - `service.py`: `estimate_eta`, `assign_order`, `process_cancellation`, and helpers.
  - `models.py`: `new_partner`, `new_order`.
  - `fixtures.py`: `sample_inputs`.
  - `main.py`: offline demo entry point.
  - `tests/test_contract.py`, `tests/test_edge_cases.py`, `tests/test_acceptance_matrix.py`.
  - `data/records.json` and `data/README.txt` for schema and edge-case categories.
- Candidate filtering, ETA calculation, and capacity flow traced:
  - `estimate_eta` validates the order, `now`, partner active status, capacity, workload, and both travel legs; then computes `pickup = now + leg1 + workload` and `eta = pickup + prep_minutes + leg2`.
  - `assign_order` iterates partners, keeps eligible estimates, and selects `min(..., key=(eta_minutes, str(partner_id)))`.
  - `process_cancellation` copies the partner, checks the event id for idempotency, removes the order from `active_order_ids`, subtracts its recorded minutes from `workload_minutes` (clamped at 0), and records the event id.
- How I confirmed my understanding:
  - Read all assertions in the three test files and the starter comments marking intentional defects.
  - Ran the baseline suite and reproduced 65 failures.
  - Compared `main:service.py` with the corrected `service.py` to confirm each change maps to a failed assertion.

## 3. Investigation and implementation strategy
- Issue 1: missing/invalid inputs were not rejected.
  - Symptom: baseline `estimate_eta` assumed dict inputs and did not validate ids, prep time, `now`, active status, capacity, workload, or travel values; malformed values could produce `NaN`/`inf` or invalid ETAs.
  - Evidence: `test_invalid_order_fields_do_not_assign_partner`, `test_current_time_validation`, `test_preparation_time_validation`, `test_invalid_or_missing_travel_time_rejected`.
  - Fix: added `_is_number`, `_valid_time`, `_valid_id`, `_valid_order`, and `_partner_active_count`; `estimate_eta` now returns ineligible for any invalid input.
- Issue 2: capacity and active status were ignored.
  - Symptom: inactive or full-capacity partners could be selected.
  - Evidence: `test_inactive_partners_never_selected`, `test_capacity_boundary_matrix`, `test_inactive_partner_not_assigned`, `test_full_partner_not_assigned`.
  - Fix: require `partner["active"] is True` and integer `capacity >= 1` with `active_count < capacity`.
- Issue 3: missing travel data risked being treated as usable.
  - Symptom: baseline only checked `leg1 is None or leg2 is None`, so `NaN`, `inf`, negatives, booleans, or strings could pass.
  - Evidence: `test_missing_travel_is_not_zero`, `test_eta_is_ineligible_when_either_required_route_is_missing`.
  - Fix: both legs must pass `_valid_time`; missing/invalid routes make the candidate ineligible and never contribute zero.
- Issue 4: duplicate cancellation released workload/capacity twice.
  - Symptom: starter recorded `event_id` but did not check it before applying the event.
  - Evidence: `test_duplicate_cancellation_is_idempotent`, `test_duplicate_cancellation_is_idempotent_across_workloads`.
  - Fix: if `event_id in processed_cancellation_ids`, return unchanged; also coerce malformed fields and clamp workload at 0.

## 4. Implementation decisions
- Main changes and why:
  - Centralized validation in small helpers so `estimate_eta`, `assign_order`, and `process_cancellation` share one definition of a valid non-negative finite number.
  - Kept `assign_order` side-effect free: it selects a partner but does not mutate capacity/workload; callers update partner state through cancellation or their own assignment bookkeeping.
  - Used `deepcopy` in `process_cancellation` to avoid mutating the caller's partner.
- Alternatives considered and why rejected:
  - Inline validation in each function: rejected because it duplicates the bool/NaN/inf rules and risks drift.
  - Treating missing travel as infinity and still comparing ETAs: rejected because the contract requires no reliable ETA when a required route is missing.
  - Mutating the partner in place during cancellation: rejected because tests compare before/after values and reuse inputs.
- Assumptions:
  - Travel keys are `(zone, restaurant_id)` and `(restaurant_id, destination_zone)` tuples.
  - `now` defaults to 0 and must be a non-negative finite number.
  - `minutes_by_order[order_id]` is the workload contribution of that order.
  - Event ids are unique per cancellation event.

## 5. Verification
- Tests added or changed: no test files were modified; the existing 229 tests now pass and act as regression coverage.
- Commands run and actual results:
  - `py -m pytest -q` -> **229 passed, 0 failed, 0 errors, 0 skipped** in 0.17s.
  - `py -m main` -> `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.
- Edge cases verified: missing routes, inactive partners, full capacity, tie-breaking, negative times, invalid `now`, duplicate cancellation, cancellation of an absent order, workload clamping.
- Remaining failures or known limitations: none in the automated suite. The service is in-memory only and is not concurrency-safe; event-id collisions (for example `None`) are not guarded.

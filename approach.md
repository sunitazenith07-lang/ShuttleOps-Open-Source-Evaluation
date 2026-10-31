# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing:
    python -m pytest -q
- Initial test result (include the actual summary):
================================================================== short test summary info ===================================================================
FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[-1-1] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[1--1] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[-1--1] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[2-1] - TypeError: unsupported operand type(s) for +: 'int' and 'str'
FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[1-2] - TypeError: unsupported operand type(s) for +: 'int' and 'str'
FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[True-1] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[1-False] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[nan-1] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[1-inf] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_preparation_time_validation[-1] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_preparation_time_validation[-5] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_preparation_time_validation[-100] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_preparation_time_validation[None] - TypeError: unsupported operand type(s) for +: 'int' and 'NoneType'
FAILED tests/test_acceptance_matrix.py::test_preparation_time_validation[10_0] - TypeError: unsupported operand type(s) for +: 'int' and 'str'
FAILED tests/test_acceptance_matrix.py::test_preparation_time_validation[True] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_preparation_time_validation[inf] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_preparation_time_validation[nan] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_inactive_partners_never_selected[False0] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_inactive_partners_never_selected[False1] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_inactive_partners_never_selected[False2] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_inactive_partners_never_selected[0] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_inactive_partners_never_selected[None] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[1-1] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[1-2] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[2-2] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[3-3] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[4-4] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[5-5] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[0-0] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[-1-0] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[True-0] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[1.5-0] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_capacity_boundary_matrix[None-0] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[0] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[1] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[2] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[3] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[5] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[8] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[10] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[15] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[20] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[30] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[60] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[100] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[250] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[500] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads[999] - AssertionError: assert ['C', 'C'] == ['C']
FAILED tests/test_acceptance_matrix.py::test_current_time_validation[-1] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_current_time_validation[-10] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_current_time_validation[5_1] - TypeError: can only concatenate str (not "int") to str
FAILED tests/test_acceptance_matrix.py::test_current_time_validation[True] - assert True is False
FAILED tests/test_acceptance_matrix.py::test_current_time_validation[None] - TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
FAILED tests/test_acceptance_matrix.py::test_invalid_order_fields_do_not_assign_partner[order_id-] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_invalid_order_fields_do_not_assign_partner[order_id-None] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_invalid_order_fields_do_not_assign_partner[order_id-0] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_invalid_order_fields_do_not_assign_partner[prep_minutes--1] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_invalid_order_fields_do_not_assign_partner[prep_minutes-None] - TypeError: unsupported operand type(s) for +: 'int' and 'NoneType'
FAILED tests/test_acceptance_matrix.py::test_invalid_order_fields_do_not_assign_partner[prep_minutes-2] - TypeError: unsupported operand type(s) for +: 'int' and 'str'
FAILED tests/test_acceptance_matrix.py::test_invalid_order_fields_do_not_assign_partner[prep_minutes-True] - AssertionError: assert 'P' is None
FAILED tests/test_acceptance_matrix.py::test_invalid_order_fields_do_not_assign_partner[prep_minutes-nan] - AssertionError: assert 'P' is None
FAILED tests/test_contract.py::test_inactive_partner_not_assigned - AssertionError: assert 'P' is None
FAILED tests/test_contract.py::test_full_partner_not_assigned - AssertionError: assert 'P' is None
FAILED tests/test_contract.py::test_negative_prep_time_is_rejected - AssertionError: assert 'P' is None
FAILED tests/test_contract.py::test_duplicate_cancellation_is_idempotent - AssertionError: assert (0 == 0 and ['C1', 'C1'] == ['C1']
65 failed, 164 passed in 1.61s
- Demo/output observed:
    Test cases failed because estimate_eta returned invalid data for missing travel entries, assign_order did not filter inactive or over‑capacity partners, and process_cancellation mutated state even when the order was absent.

## 2. Codebase understanding
- Important files/functions inspected:
    models.py
    service.py
    test_contract.py
    test_acceptance_matrix.py
- Candidate filtering, ETA calculation, and capacity flow traced:
    assign_order iterates over partners, calls estimate_eta, then applies eligibility checks (active flag, capacity, order_id validity). estimate_eta computes pickup_minutes and eta_minutes based on travel times, partner workload, and order preparation.
- How you confirmed your understanding:
    By comparing test results with the expected behaviour.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1:
    estimate_eta accepted negative or non‑numeric travel times, causing TypeError or nonsensical ETAs.
    Hypothesis: Missing input validation.
    Evidence: Tests that supplied None or negative travel values raised exceptions.
    Fix: Add strict type‑and‑range guards for leg1, leg2, prep_minutes, capacity, and now. Return an ineligible result when validation fails.

- Issue 2:
    assign_order never checked partner activity or capacity, resulting in assignments to inactive or overloaded partners.
    Hypothesis: Eligibility conditions were incomplete (comment in the file hints at this).  
    Evidence: Tests expecting reason='no eligible partner' failed.  
    Fix: Extend the eligibility block to require partner['active'] truthy and not 'no', and ensure len(active_order_ids) < capacity.

- Issue 3 (if applicable):
    process_cancellation removed workload minutes even when the order_id was not present, and recorded the event_id unconditionally.
    Hypothesis: Guard clause missing.
    Evidence: Tests that cancelled a non‑existent order altered the partner state.
    Fix: Add if order_id in out['active_order_ids']: guard before mutating state and recording the event.

## 4. Implementation decisions
- Main changes and why:
    Added comprehensive validation in estimate_eta to guarantee safe numeric operations.
    Refined partner eligibility logic in assign_order to reflect real‑world constraints (active flag, capacity, valid order_id).
    Protected process_cancellation with a guard clause to make the operation idempotent.
- Alternatives considered and why rejected:
    Returning generic errors instead of a structured ineligible payload would have broken the contract expected by callers.
    Silently ignoring invalid partners in assign_order was considered but would hide programming mistakes; explicit eligibility checks provide clearer diagnostics.
- Assumptions:
    travel map always contains integer minutes for valid zone pairs.
    partner['capacity'] is a positive integer.
    order['prep_minutes'] is a non‑negative finite number.
    
## 5. Verification
- Tests added or changed:
- Commands run and actual results:
- Edge cases verified:
- Remaining failures or known limitations:

Record actual engineering decisions and evidence. Do not claim tests or experiments you did not run.
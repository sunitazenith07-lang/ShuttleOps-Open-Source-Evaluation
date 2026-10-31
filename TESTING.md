# TESTING.md — Test strategy and evidence

## 1. Testing objective

Verify the acceptance contract across normal, boundary, invalid-input, interacting-condition and state-change cases. A passing example alone is not sufficient: for each behavior, compare the input, expected result and actual result, then retain regression coverage for defects found.

Testing terms used here:

- A **test case** checks one scenario.
- A **test matrix** organizes related cases across values or condition combinations.
- The **test suite** is the complete set of cases run for the project.

## 2. Environment and commands

- Python: 3.14.7
- pytest: 9.2.0
- Baseline command: `python3 -m pytest -q --tb=no`
- Baseline result: **65 failed, 164 passed** (229 cases).
- Final command: `python3 -m pytest -q`
- Final result: **235 passed**.
- Demo command: `python3 -m main`
- Demo output: `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

The project's prescribed command uses `python`, but that executable is not available in this terminal. Validation used `python3`. The CI workflow selects Python 3.11; that runtime was not available/tested locally here. Dependencies were already importable, so no installation was necessary.

## 3. Test categories and result

| Category | Requirement being checked | Relevant evidence |
|---|---|---|
| Normal / formula | Pickup and ETA include the correct travel, workload and preparation components | `test_eta_formula`, `test_eta_calculation_matrix`, `test_eta_formula_for_expanded_scenario_matrix` |
| Boundary | Zero times are valid; exact capacity is full; just-below capacity is available | `test_eta_calculation_matrix`, `test_capacity_boundary_matrix` |
| Invalid input | Missing IDs/routes, negative or malformed times, Boolean, NaN and infinity are rejected | `test_invalid_or_missing_travel_time_rejected`, `test_preparation_time_validation`, `test_current_time_validation`, `test_invalid_order_fields_do_not_assign_partner` |
| Partner eligibility | Inactive, malformed, invalid-capacity and full partners are not assigned | `test_inactive_partner_not_assigned`, `test_inactive_partners_never_selected`, `test_full_partner_not_assigned`, `test_capacity_boundary_matrix` |
| Deterministic selection | Lowest ETA wins; ties resolve by partner ID, independently of input order | `test_lowest_eta_selected`, `test_tie_break_by_partner_id`, `test_dispatch_selects_lowest_eta_and_stable_tie`, `test_ties_break_by_partner_id_independent_of_input_order` |
| Cancellation / state | Duplicate events do not repeat release; unrelated orders do not release workload; workload is clamped at zero | `test_duplicate_cancellation_is_idempotent`, `test_duplicate_cancellation_is_idempotent_across_workloads`, `test_cancellation_only_releases_present_order`, `test_cancellation_workload_never_goes_below_zero` |
| Integration / regression | The full dispatch path remains usable and malformed candidates do not block valid candidates | Full `python3 -m pytest -q`; `tests/test_regressions.py`; `python3 -m main` |

## 4. Edge-case register

| # | Scenario / input | Expected result | Actual observed result | Test/evidence |
|---|---|---|---|---|
| 1 | Travel route missing, negative, string, Boolean, NaN or infinity | Candidate is ineligible; no missing route becomes zero | Rejected by the suite | `test_missing_travel_is_not_zero`, `test_invalid_or_missing_travel_time_rejected` |
| 2 | `prep_minutes` is zero | Valid input; calculation proceeds | Accepted and formula checked | `test_eta_calculation_matrix[0-0-0-0-0-0]`, `test_preparation_time_validation[0]` |
| 3 | Preparation/workload/current-time is negative, missing or wrong type | Candidate is ineligible rather than raising during ETA calculation | Invalid cases rejected | `test_preparation_time_validation`, `test_current_time_validation` |
| 4 | Capacity equals active-order count | Partner is not eligible | Full-capacity cases rejected | `test_full_partner_not_assigned`, `test_capacity_boundary_matrix` |
| 5 | Capacity is Boolean, zero, negative, fractional or missing | Invalid capacity; partner is not eligible | Invalid capacities rejected | `test_capacity_boundary_matrix` |
| 6 | Partner is inactive despite complete route data | Partner is not selected | Inactive partners rejected | `test_inactive_partner_not_assigned`, `test_inactive_partners_never_selected` |
| 7 | Two candidates tie on ETA and input order is reversed | Smaller partner ID wins consistently | Tie-break verified | `test_tie_break_by_partner_id`, `test_ties_break_by_partner_id_independent_of_input_order` |
| 8 | Same cancellation event is replayed | Release workload once and store the event ID once | Duplicate replay verified | `test_duplicate_cancellation_is_idempotent`, `test_duplicate_cancellation_is_idempotent_across_workloads` |
| 9 | Cancellation minutes exceed workload | Resulting workload is zero, not negative | Clamping verified | `test_cancellation_workload_never_goes_below_zero` |
| 10 | Invalid partner among valid candidates; malformed order; finite values whose sum overflows | Bad candidate/order is safely rejected; valid candidate can still be considered; overflow cannot produce an infinite ETA | Regression cases passed | `tests/test_regressions.py` |

The acceptance matrix combines input categories and condition combinations rather than relying only on a happy path. For example, partner assignment requires both active status and remaining capacity; failing either condition is sufficient to reject the candidate.

## 5. Regression tests added

`tests/test_regressions.py` adds six cases:

1. A malformed partner is skipped while a valid partner can still be selected.
2–4. Three malformed order shapes remain unassigned with a reason.
5. Finite input values that overflow ETA arithmetic do not produce an eligible candidate.
6. Cancellation updates returned state without mutating the original partner object.

The existing tests were preserved. The count increased from 229 baseline cases to 235 final cases.

## 6. Reading the baseline failures

The baseline's **65 failed tests do not represent 65 distinct root causes**. Multiple parameterized inputs exercised the same missing validation rule; several cases also exposed missing active/capacity checks or cancellation-event deduplication. Grouping by behavior revealed the producer of the wrong result and avoided adding one special case per failing assertion.

The baseline run also showed why test assertions matter: a test can fail because an expected ineligible result was marked eligible, because invalid arithmetic raised an exception, or because state such as the processed-event list changed twice. Those are different observations and point to different conditions to verify.

## 7. Limitations

The final visible suite passed, but that is evidence for the tested contract, not proof for every possible input. Persistence across process restarts and live travel-time data are outside this repository's scope. Local validation used Python 3.14.7 rather than the workflow's Python 3.11. Cancellation record corruption has explicit error behavior but no storage integration or recovery workflow to test.

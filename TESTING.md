# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version: Python 3.9.6 (Darwin / macOS)
- Command run: `python3 -m pytest -q`
- Actual test summary: 236 passed in 0.15s (Starter baseline was 65 failed, 164 passed in 0.60s)

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Negative preparation time (`prep_minutes = -5`) | Order rejected / not assigned; candidate marked ineligible | `partner_id` is None, `reason` indicates invalid order or time data | `test_contract.py::test_negative_prep_time_is_rejected`, `test_acceptance_matrix.py::test_preparation_time_validation[-5]` |
| 2 | Boolean passed as travel time or workload (`leg1 = True` or `workload_minutes = True`) | Rejected as non-numeric/ineligible without coercing `True` to integer `1` | `eligible` is False, `eta_minutes` is None | `test_acceptance_matrix.py::test_invalid_or_missing_travel_time_rejected[True-1]`, `test_regression.py::test_edge_case_boolean_workload_rejected` |
| 3 | Capacity saturation boundary (`capacity = 2`, `active_order_ids = ['O1', 'O2']`) | Partner rejected as capacity is full (`len(active_orders) >= capacity`) | `partner_id` is None, order remains unassigned | `test_acceptance_matrix.py::test_capacity_boundary_matrix[2-2]`, `test_regression.py::test_edge_case_capacity_saturation_boundary` |
| 4 | Duplicate cancellation replay (`event_id = 'C1'` sent twice for order `'O1'`) | Idempotent handling: workload decremented once, order removed once, event recorded once | `workload_minutes == 0`, `active_order_ids == []`, `processed_cancellation_ids == ['C1']` | `test_contract.py::test_duplicate_cancellation_is_idempotent`, `test_acceptance_matrix.py::test_duplicate_cancellation_is_idempotent_across_workloads` |
| 5 | Missing or incomplete travel route (`('Z-1', 'R-1')` missing from travel map) | Missing route never treated as 0; partner marked ineligible | `eligible` is False, `eta_minutes` is None, order unassigned with reason | `test_contract.py::test_missing_travel_is_not_zero`, `test_edge_cases.py::test_eta_is_ineligible_when_either_required_route_is_missing` |
| 6 | Whitespace or empty string identifiers (`order_id = '   '`) | Treated as invalid identifier; order unassigned | `partner_id` is None, `reason == 'invalid order or time data'` | `test_regression.py::test_edge_case_whitespace_or_empty_ids_rejected`, `test_acceptance_matrix.py::test_invalid_order_fields_do_not_assign_partner[order_id-]` |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning.
- **Defect 1**: Lack of strict numeric type and non-negative checking in `estimate_eta`. Fixed by adding `_is_valid_non_negative_number` checking `isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val) and val >= 0`. Tests: `test_regression.py::test_edge_case_boolean_workload_rejected`, `test_regression.py::test_edge_case_negative_workload_rejected`.
- **Defect 2**: Inactive partners and full-capacity partners being assigned in `assign_order`. Fixed by checking `partner.get('active') is True`, validating capacity is integer >= 1, and enforcing `len(active_order_ids) < capacity`. Test: `test_regression.py::test_edge_case_capacity_saturation_boundary`.
- **Defect 3**: Duplicate cancellation events deducting partner workload multiple times. Fixed by deduplicating using `processed_cancellation_ids` before executing cancellation logic. Test: `test_regression.py::test_edge_case_cancellation_unknown_order_and_idempotency`.
- **Defect 4**: Unhandled exceptions on malformed or empty inputs (`None` partners or travel dict). Fixed by safe dictionary gets, defensive None checks, and empty list defaults. Test: `test_regression.py::test_edge_case_none_partners_or_travel_handled_safely`.
- **Optional Stretch Feature**: Implemented `explain_candidates` in `service.py` to return an audit trail explaining why each candidate partner was eligible or why they were rejected. Test: `test_regression.py::test_stretch_explain_candidates_reasons`.

## Remaining failures or limitations
List any known failing tests or unresolved behaviours honestly.
- Zero remaining failures: 236 out of 236 tests pass cleanly in 0.15s.
- Known limitations: In-memory simulation does not persist partner states to an external database; concurrent execution would require distributed locks or transactional isolation in production environments.

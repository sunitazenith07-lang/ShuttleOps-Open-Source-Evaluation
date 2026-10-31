# Testing — SmartDispatch

## Test command and environment

- **Python version:** Python 3.14.8
- **Baseline command:** `python -m pytest -q`
- **Baseline result before implementation changes:** 65 failed, 164 passed.
- **Final command:** `python -m pytest -q`
- **Final result:** **229 passed in 0.41 seconds**.
- **Demo command:** `python -m main`
- **Demo result:** Completed successfully. It assigned order `O-7` to partner
  `P-2`, with pickup time 13 minutes and ETA 35 minutes.

The test files were not edited. The edge cases below were exercised as
parameterized cases in the full final pytest run; they were not run as separate
commands.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Missing first or second route entry | Estimate is ineligible; ETA is `None`, not zero or a partial calculation. | Passed in the final suite. | `test_missing_travel_is_not_zero`; `test_eta_is_ineligible_when_either_required_route_is_missing` |
| 2 | Negative, string, boolean, NaN, or infinite travel-time value | Estimate is ineligible and does not use invalid route data. | All parameter cases passed in the final suite. | `test_invalid_or_missing_travel_time_rejected` |
| 3 | Invalid preparation values such as `-1`, `None`, `"10"`, `True`, NaN, and infinity | ETA estimate is ineligible; assignment does not select a partner for the invalid order. | All parameter cases passed in the final suite. | `test_preparation_time_validation`; `test_invalid_order_fields_do_not_assign_partner` |
| 4 | Inactive partner, including false-like values such as `False`, `0`, or `None` | Partner is not assigned. Only `active is True` is accepted. | All parameter cases passed in the final suite. | `test_inactive_partners_never_selected`; `test_inactive_partner_not_assigned` |
| 5 | Capacity is invalid, zero, or already reached | Partner is not assigned; capacity must be a positive integer and active order count must be below it. | All parameter cases passed in the final suite. | `test_capacity_boundary_matrix`; `test_full_partner_not_assigned` |
| 6 | Equal candidate ETAs, with partners supplied in different orders | Partner with lexicographically smallest ID is selected deterministically. | All parameter cases passed in the final suite. | `test_tie_break_by_partner_id`; `test_ties_break_by_partner_id_independent_of_input_order` |
| 7 | Same cancellation event applied twice | Order workload and capacity are released once; event ID appears once in processed history. | All parameter cases passed in the final suite. | `test_duplicate_cancellation_is_idempotent`; `test_duplicate_cancellation_is_idempotent_across_workloads` |
| 8 | Cancellation refers to an order not in the active-order list | Other orders and workload are left unchanged. | All parameter cases passed in the final suite. | `test_cancellation_only_releases_present_order` |
| 9 | Cancellation workload exceeds current workload | Workload is clamped at zero, never negative. | All parameter cases passed in the final suite. | `test_cancellation_workload_never_goes_below_zero` |

## Regression tests added

No tests were added or changed. The supplied contract, acceptance-matrix, and
edge-case tests were retained and used as the regression suite. The service
changes address the failures in input/time validation, partner activity and
capacity checks, and duplicate cancellation handling. The final full suite
passed all 229 cases.

## Remaining failures or limitations

No failures remained in the final run. The demo and static checks were also
verified during implementation. This report covers the visible repository
tests; it does not claim that external or hidden tests were run.

# TESTING.md — Test evidence

## Test command and environment

- Python version: **3.13.15**
- Command run: `python -m pytest -q`
- Untouched baseline: **65 failed, 164 passed in 0.61s**
- After the fix and regression tests: **241 passed in 0.21s**
- Demo command: `python -m main`
- Demo result: `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`

No existing test was deleted, skipped, weakened or edited. The new coverage is in `tests/test_regressions.py` (12 tests).

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Only the partner-to-restaurant leg exists; restaurant-to-destination leg is missing | Candidate is ineligible; missing travel is not zero | `eligible is False`, `eta_minutes is None` | `test_eta_is_ineligible_when_either_required_route_is_missing`; `test_travel_mapping_none_is_safe_and_not_zero` |
| 2 | Travel value is `-1`, `"2"`, `True`, `False`, `nan` or `inf` | Reject the candidate instead of doing arithmetic or raising | `eligible is False`, `eta_minutes is None` | `test_invalid_or_missing_travel_time_rejected`; `test_negative_travel` observation in `DISPATCH_NOTES.md` |
| 3 | Partner is inactive, at capacity, or has capacity `0`, `-1`, `True`, `1.5` or `None` | No assignment | `partner_id is None` | `test_inactive_partner_not_assigned`; `test_full_partner_not_assigned`; `test_capacity_boundary_matrix` |
| 4 | `prep_minutes` is `-5`, `None`, `"10"`, `True`, `nan` or `inf`; `now` is negative, a string, a boolean or `None` | No assignment/ineligible result; no `TypeError` | `eligible is False` or `partner_id is None` | `test_negative_prep_time_is_rejected`; `test_preparation_time_validation`; `test_current_time_validation` |
| 5 | Order ID is `""`, `None`, `0` or whitespace; restaurant/zone is missing or invalid | Order is rejected with a reason, never assigned | `partner_id is None`, reason starts with `invalid order` | `test_invalid_order_fields_do_not_assign_partner`; `test_invalid_order_identifiers_and_malformed_order_are_safe` |
| 6 | Two candidates have equal ETA and IDs `P-10` and `P-2` | Choose `P-10` because the tie-break is lexicographic, not numeric | `partner_id == "P-10"` | `test_tie_break_by_partner_id`; `test_tie_break_is_lexicographic_not_numeric` |
| 7 | Same cancellation event `C1` is processed twice | Workload is released once and the event is recorded once | `active_order_ids == []`, `workload_minutes == 0`, `processed_cancellation_ids == ["C1"]` | `test_duplicate_cancellation_is_idempotent`; `test_duplicate_cancellation_is_idempotent_across_workloads` |
| 8 | Same order is cancelled with `C1` and then a different event ID `C2` | The order is released once; both distinct events are recorded, workload does not go negative | `active_order_ids == []`, `workload_minutes == 0`, events `["C1", "C2"]` | `test_same_order_with_different_event_ids_is_not_released_twice` |
| 9 | Duplicate event ID `C1` is sent for a second, still-active order | The event is processed only once; the second order is untouched | `active_order_ids == ["O2"]`, `workload_minutes == 6`, events `["C1"]` | `test_duplicate_event_id_for_another_order_is_ignored` |
| 10 | Partner has a negative `workload_minutes` | Candidate cannot produce a reliable ETA; skip it | Valid candidate is selected instead | `test_partner_with_negative_workload_is_not_assigned` |
| 11 | Expanded `data/records.json` is converted to tuple-key travel data and all 180 orders are assigned | No crash, non-negative ETA, deterministic result regardless of partner order | All orders returned a valid shape; forward/reverse partner order produced the same result | `test_expanded_dataset_is_deterministic_and_safe` |

## Regression tests added

`tests/test_regressions.py` protects these fixed defects:

1. Invalid/malformed orders return an unassigned result with a reason.
2. Negative partner workload makes a candidate ineligible instead of reducing the ETA.
3. A missing route for one partner does not prevent another valid partner from being assigned.
4. ETA ties use lexicographic partner IDs (`P10` before `P2`).
5. `None`, strings and incomplete records in the partner list are skipped safely.
6. `travel=None` is treated as missing data, not zero.
7. `assign_order` does not mutate the order, partners or travel mapping.
8. Two different cancellation events for the same order do not release workload twice.
9. A duplicate event ID for another order is ignored.
10. A malformed `minutes_by_order` value does not create a negative workload or an invented subtraction.
11. Tuple/set cancellation state is converted to deterministic lists without mutating the input.
12. The expanded JSON dataset is deterministic and safe when partner order is reversed.

## Remaining failures or limitations

There are no remaining visible test failures: `241 passed in 0.21s`.

Known limitations:

- A missing `workload_minutes` defaults to zero for compatibility with the provided model; an explicitly malformed value makes the candidate ineligible.
- If `minutes_by_order` for the cancelled order is malformed, the order is removed from `active_order_ids` but the workload is left unchanged because there is no trustworthy number to subtract. This is asserted by `test_cancellation_with_malformed_minutes_does_not_guess_workload`.
- Cancellation deduplication is per partner record, matching the function signature; cross-partner event deduplication would require a shared event store.
- Remote GitHub Actions: PR #3's upstream "Validation tests" run reported `action_required` because the workflow is awaiting maintainer approval. There is no remote green check to report at submission time; the local suite result is the evidence above.
- No performance benchmark was run. The reported suite time is a test result, not a before/after optimisation claim.

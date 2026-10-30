# TESTING.md

## Test command and environment
- **Python version:** 3.14.7 (local `.venv`); CI uses 3.11.
- **Commands run:** `python -m pytest -q`, `python -m main`
- **Baseline (untouched starter):** `65 failed, 164 passed in 0.19s` (229 total)
- **Final:** `443 passed in 0.11s` — Total 443, Passed 443, Failed 0, Errors 0, Skipped 0
  - Original tests (`test_contract.py`, `test_acceptance_matrix.py`, `test_edge_cases.py`): 229 passed, unmodified
  - New `tests/test_regression.py`: 214 passed (57 of these fail against the original starter)

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | **Negative preparation time** — `new_order('O','R','D',-5)`, one valid partner, valid routes | Order rejected, `partner_id` is `None` | `partner_id: None`, `reason: 'invalid order: invalid or missing prep_minutes'` (starter assigned `P`) | `test_negative_prep_time_is_rejected`; `test_preparation_time_validation[-1/-5/-100]` — **pass** |
| 2 | **Missing travel-time information** — `travel={}` or only one leg present | Not eligible, `eta_minutes` is `None` (never treated as 0) | `eligible: False`, `eta_minutes: None`, `reason: 'missing travel-time data'` | `test_missing_travel_is_not_zero`; `test_eta_is_ineligible_when_either_required_route_is_missing` (3 cases) — **pass** |
| 3 | **Inactive delivery partner** — `partner['active'] = False` (also `0`, `None`, `"no"`, `"yes"`) | Never selected | `partner_id: None`, rejected with `'partner is not active'` (starter selected the partner for `False`, `0`, `None` — 6 failing tests) | `test_inactive_partner_not_assigned`; `test_inactive_partners_never_selected` (11 cases); `test_truthy_non_bool_active_flag_is_not_treated_as_active` — **pass** |
| 4 | **Partner already at full capacity** — `capacity=1`, `active_order_ids=['A']` | Not selected | `partner_id: None`, `'partner at capacity'` | `test_full_partner_not_assigned`; `test_capacity_boundary_matrix` (15 cases) — **pass** |
| 5 | **Duplicate cancellation event** — cancel `O1` with `C1`, then repeat `C1` | Workload released once; `processed_cancellation_ids == ['C1']` | `workload_minutes: 0`, ids `['C1']` (starter: `['C1','C1']`) | `test_duplicate_cancellation_is_idempotent`; `..._across_workloads` (15 cases) — **pass** |
| 6 | **Same event ID, different order** — `C1` cancels `O1` (10 min), then `C1` for `O2` (15 min) | Second event ignored | `active_order_ids: ['O2']`, workload `15` | `test_reused_event_id_with_different_payload_is_ignored` — **pass** |
| 7 | **Cancellation with no event ID** (7 such events in dataset) | Not applied | order still active, workload unchanged, nothing recorded | `test_cancellation_without_event_id_is_not_applied` (2 cases) — **pass** |
| 8 | **NaN / infinity / bool / string times** — e.g. `leg2=inf`, `leg1=True`, `prep=nan`, `now="5"` | Rejected, no `TypeError` | `eligible: False` (starter raised `TypeError` for `"10"`, `None`; accepted `True`, NaN) | `test_invalid_or_missing_travel_time_rejected`, `test_current_time_validation`, `test_non_finite_or_non_numeric_now_rejected` — **pass** |
| 9 | **Invalid capacity** — `0`, `-1`, `True`, `1.5`, `None` | Never selected | `'invalid capacity'` | `test_capacity_boundary_matrix[0-0 … None-0]` — **pass** |
| 10 | **Empty / malformed partner lists** — `[]`, `None`, `"P"`, `[None, 42, partner_without_id, ...]` | No crash; unassigned with reason, or valid partner chosen | `reason: 'no delivery partners supplied'`; malformed entries listed in `rejected` | `test_empty_or_non_list_partners_leave_order_unassigned`, `test_malformed_partner_records_are_skipped_not_fatal` — **pass** |
| 11 | **ETA tie** — `P10`, `P9`, `P2` identical ETA | Lexicographic smallest ID: `P10` | `P10` | `test_tie_break_is_lexicographic_not_numeric` — **pass** |
| 12 | **Whole dataset** — all 180 orders × 60 partners | Each result equals an independent brute-force reference; unchanged when partners shuffled | 170 assigned, 10 unassigned; all match | `test_dataset_assignment_respects_all_rules` (180 cases), `test_dataset_assignment_is_independent_of_partner_order` — **pass** |

## Regression tests added (`tests/test_regression.py`)

| Defect fixed | Tests |
|---|---|
| No validation of `now`, workload, travel container, missing fields | `test_non_finite_or_non_numeric_now_rejected`, `test_invalid_partner_workload_is_not_treated_as_zero`, `test_missing_order_field_is_rejected_with_reason`, `test_non_mapping_travel_data_is_safe`, `test_float_travel_and_prep_are_accepted` |
| Active/capacity not enforced; malformed records | `test_empty_or_non_list_partners_leave_order_unassigned`, `test_malformed_partner_records_are_skipped_not_fatal`, `test_truthy_non_bool_active_flag_is_not_treated_as_active`, `test_ineligible_faster_partner_does_not_win`, `test_unassigned_result_explains_each_rejection` |
| Determinism | `test_tie_break_is_lexicographic_not_numeric`, `test_assign_order_does_not_mutate_inputs`, `test_dataset_assignment_is_independent_of_partner_order` |
| Cancellation not idempotent | `test_reused_event_id_with_different_payload_is_ignored`, `test_cancellation_without_event_id_is_not_applied`, `test_cancellation_frees_capacity_and_drops_order_minutes`, `test_cancellation_returns_copy_and_rejects_non_mapping`, `test_dataset_cancellation_stream_never_double_releases` |
| End-to-end rule check | `test_dataset_assignment_respects_all_rules` (one case per dataset order) |

## Remaining failures or limitations
- No failing tests.
- Not covered by the contract and therefore not enforced: order `status` (e.g. `CANCELLED` orders are still assignable), and updating partner capacity after an assignment. See `challenges.md` §6.

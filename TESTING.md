# TESTING.md — Required submission

## Test command and environment
- Python version: 3.13.15
- Command run: `py -m pytest -q`
- Actual test summary: **229 passed, 0 failed, 0 errors, 0 skipped** in 0.17s.
- Demo command: `py -m main` -> `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}`.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `estimate_eta(order, partner, {})` with no travel routes | Ineligible, `eta_minutes is None`; missing data is not zero | `{'eligible': False, 'eta_minutes': None}` | `test_missing_travel_is_not_zero`, `test_eta_is_ineligible_when_either_required_route_is_missing` |
| 2 | Partner with `active=False` | Not selected; assignment returns `partner_id=None` | `partner_id=None` | `test_inactive_partner_not_assigned`, `test_inactive_partners_never_selected` |
| 3 | Partner capacity 1 with 1 active order | Full capacity; not selected | `partner_id=None` | `test_full_partner_not_assigned`, `test_capacity_boundary_matrix` |
| 4 | Two partners with equal ETA (`X` and `Y` both travel 3, prep 0) | Tie broken by partner ID ascending (`A` before `Z`) | `partner_id='A'` | `test_tie_break_by_partner_id`, `test_dispatch_selects_lowest_eta_and_stable_tie` |
| 5 | Order with `prep_minutes=-5` | Invalid order; no assignment | `partner_id=None` | `test_negative_prep_time_is_rejected`, `test_invalid_order_fields_do_not_assign_partner` |
| 6 | Duplicate cancellation with event id `C1` | Workload released once; `processed_cancellation_ids=['C1']` | `workload_minutes=0`, `processed_cancellation_ids=['C1']` | `test_duplicate_cancellation_is_idempotent` |
| 7 | `now=-1`, `"5"`, `True`, `None` | Invalid current time; ETA ineligible | `eligible=False` | `test_current_time_validation` |
| 8 | Cancel an order not in `active_order_ids` | No workload change; event still recorded | `workload_minutes` unchanged | `test_cancellation_only_releases_present_order` |
| 9 | Workload 3, recorded minutes 10 | Workload clamped to 0, never negative | `workload_minutes=0` | `test_cancellation_workload_never_goes_below_zero` |

## Regression tests added
No test files were modified in this change. The repository's existing 229 tests in `test_contract.py`, `test_edge_cases.py`, and `test_acceptance_matrix.py` provide regression coverage for the corrected validation, active/capacity filtering, missing-travel handling, deterministic tie-breaking, and cancellation idempotency.

## Remaining failures or limitations
- No automated test failures remain.
- `data/records.json` is not exercised by the automated suite; it is investigation material only.
- The service is in-memory and not concurrency-safe.

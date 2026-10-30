# Testing

## Environment and results

These checks were run by Codex during the assisted work documented in approach.md. The user also reported the original 65-failure baseline.

- Environment: Windows, Python 3.15.1.
- Untouched baseline: **65 failed, 164 passed** with `python -m pytest -q`.
- Latest rerun in the original local repository (`Documents/evaluation/SmartDispatch-Open-Source-Evaluation`): **352 passed in 0.83s**.
- No skipped or failing tests were reported in that run.

Command used for the latest full-suite rerun:

```text
python -m pytest -q -p no:cacheprovider
```

The cache option disables pytest's cache plugin; it does not skip tests. The Python version was checked earlier. The demo was rerun immediately after applying the latest code fix and returned partner `P-2`, pickup time `13`, ETA `35`, and reason `assigned`.

## Edge-case evidence

All test references below are under `tests/` and passed in the latest full run.

| Case / input | Expected behaviour | Actual result | Evidence |
|---|---|---|---|
| Required travel route absent | No reliable ETA; candidate rejected | Ineligible, ETA `None` | `test_contract.py::test_missing_travel_is_not_zero` |
| Active status is `False` | Partner cannot receive the order | No partner selected | `test_contract.py::test_inactive_partner_not_assigned` |
| Capacity 1 with one active order | Partner is full | No partner selected | `test_contract.py::test_full_partner_not_assigned` |
| Preparation time -5 | Reject invalid timing input | No partner selected | `test_contract.py::test_negative_prep_time_is_rejected` |
| Equal ETA for IDs A and Z, Z supplied first | Choose A lexicographically | A selected | `test_contract.py::test_tie_break_by_partner_id` |
| Same cancellation submitted twice | Release work once and record event once | Workload 0, history `['C1']` | `test_contract.py::test_duplicate_cancellation_is_idempotent` |
| Event E used for A, then reused for B | Replay must not cancel B | B remains; state unchanged on replay | `test_regressions.py::test_cancellation_replay_cannot_cancel_a_different_order` |
| Zero travel and zero preparation | Zero is valid, unlike missing data | ETA 0 | `test_regressions.py::test_missing_route_explained_and_zero_route_allowed` |
| Workload `10**400`, released time 0.5, and reverse | Handle overflow without applying part of event | Unchanged copy, no exception | `test_stress.py::test_cancellation_numeric_overflow_is_atomic` |
| Duplicate partner ID, pickup 1 or 2, preparation `1e20` | Reordering must not change result | Identical result after reversal | `test_stress.py::test_duplicate_partner_ids_have_deterministic_result` |
| Missing total workload, accounting map, active-order list, or minutes for the active order | Do not apply cancellation or consume event | State and event history unchanged | `test_accounting.py::test_missing_accounting_does_not_apply_or_consume_event` |
| Fixture OLD-1 lacks minutes; fill in 5 and retry E | Reject first attempt; allow retry after repair | Order removed, workload 0, history `['E']` after repair | `test_accounting.py::test_fixture_incomplete_accounting_can_be_repaired_and_retried` |
| Active order has explicitly recorded 0 minutes | Apply cancellation normally | Order removed, workload 0, event recorded once | `test_accounting.py::test_explicit_zero_accounting_is_valid` |
| O already belongs to an active or inactive supplied partner | Do not assign O again | No partner selected; reason `order is already active` | `test_accounting.py::test_already_active_order_is_not_assigned_to_another_partner` |

## Added coverage

The original 229 cases remain unchanged. `test_regressions.py` adds 40 cases, `test_stress.py` adds 75, and `test_accounting.py` adds 8, for a total of 352 pytest cases. Before the latest fix, the accounting file produced 7 failures and 1 pass; all eight now pass.

Some cases contain multiple checks:

- 3,000 seeded dispatch scenarios checked against an independent expected selection, including shuffled inputs.
- 4,000 cancellation steps checked against a separate state model, with replay and input-preservation checks.
- 1,024 combinations of small integer ETA inputs.
- All 180 dataset orders checked for deterministic, eligible selection.
- All 177 dataset cancellation records processed and checked against expected remaining state.

The cancellation dataset has no event IDs. That test synthesizes stable IDs from partner/order pairs. This tests the API with a stated assumption; it is not evidence that the dataset supplied real event IDs.

## Limits

No failures are known in the executed suite. It is not exhaustive over every possible value. Local verification used Python 3.15.1; this report does not claim a separate Python 3.10/3.11 run or a successful GitHub Actions run. Performance under production load, concurrent dispatch and persistent storage were not tested.

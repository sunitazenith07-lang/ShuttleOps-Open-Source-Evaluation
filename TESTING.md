# Testing evidence

- Runtime: Python 3.13.5 (compatible with required Python 3.10+).
- Baseline untouched archive: `python -m pytest -q` → **65 failed, 164 passed in 0.45s**.
- Updated repository: `python -m pytest -q` → **237 passed in 0.15s**.
- Demo: `python -m main` → O-7 assigned to P-2, pickup 13, ETA 35.

| Case | Expected | Observed | Regression test |
|---|---|---|---|
| Missing travel leg | Unassigned, never zero-imputed | Passed | `test_missing_route_does_not_default_to_zero` |
| Invalid order | Unassigned | Passed | `test_invalid_order_does_not_assign` |
| Malformed partner list entries | Ignore bad entries safely | Passed | `test_malformed_partner_entries_do_not_crash` |
| Partner at capacity | Unassigned | Passed | `test_partner_at_capacity_is_rejected` |
| Equal ETA in reversed input order | Choose lexicographic A | Passed | `test_tie_independent_of_input_order` |
| Duplicate cancellation event | No second workload release | Passed | `test_duplicate_event_does_not_release_reused_order_id` |
| Cancellation state aliasing | Original remains unchanged | Passed | `test_cancellation_does_not_mutate_original` |
| Negative, NaN, infinite, bool or string travel | Reject ETA | Passed | `test_invalid_time_values_are_rejected` |

Eight new regression tests were added in `tests/test_regressions_added.py`; original tests were preserved. No failures remain in the executed suite. Tests do not prove correctness under concurrent state mutation or all possible malformed nested records.

## V3 explainability regression tests

Executed `python -m pytest -q` on 2026-10-30: **243 passed**.
Six new tests in `tests/test_explainer.py` cover deterministic candidate order and lexicographic ties, distinct capacity/inactive reasons, missing travel (never zero), no input mutation, empty/malformed candidates, and invalid preparation time. Original tests remain intact.

Use `python -m main` to verify the starter-compatible result and `python -m streamlit run dashboard.py` for a manual UI smoke test. The latter was syntax-checked, but browser interactions have not been verified in this environment. Do not confuse the candidate explanation with a separate optimization policy; eligibility and ETA come directly from `service.py`.

## Presentation snapshot regression tests
- Snapshot generation does not mutate the partner list or travel table.
- A recorded decision retains its original selected partner if workload changes later.
- Identical inputs produce identical recorded decision snapshots.

Verification: 246 tests passed locally. This does not substitute for a Streamlit browser interaction test.

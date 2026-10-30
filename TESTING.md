# Testing notes

## Environment and untouched baseline

Date: 30 October 2026. Windows, PowerShell, system Python **3.14.6**, pytest **9.2.0**.
Starting commit: `fcfe44d935c55509dbfeb0e78c93a8d44345c380`; clean working tree.

Before code changes:

| Command | Actual result |
|---|---|
| `python --version` | Python 3.14.6 |
| `python -m pip install -r requirements-dev.txt` | Success; pytest 9.2.0 and dependencies already satisfied |
| `python -m pytest -q` | **65 failed, 164 passed in 1.27s**; 229 cases, no collection errors or skips |
| `python -m main` | O-7 assigned to P-2; pickup 13, ETA 35 |

Representative baseline failures:

- `test_inactive_partner_not_assigned` / `test_full_partner_not_assigned`:
  `AssertionError: assert 'P' is None`.
- `test_invalid_or_missing_travel_time_rejected[2-1]`:
  `TypeError: unsupported operand type(s) for +: 'int' and 'str'`.
- `test_duplicate_cancellation_is_idempotent`: history was `['C1', 'C1']`,
  expected `['C1']`.
- Direct malformed-order probe: `AttributeError: 'NoneType' object has no attribute 'get'`.
- Direct workload -5 probe: pickup -4, ETA 7, incorrectly eligible.

The complete untouched pytest output was captured in the OS temporary file
`smartdispatch-baseline.txt`. The new dispatch/cancellation regressions were also
run against the starter: **50 failed, 8 passed** (captured as
`smartdispatch-regressions-before.txt`). Later the explicit no-candidate example
and dataset tests were added. Existing legitimate tests were not edited.

## Commands and final validation

| Command/run | Actual outcome |
|---|---|
| Dispatch-focused original/new tests, excluding cancellations | 216 passed, 47 deselected |
| Cancellation-focused original/new tests | 71 passed, 151 deselected |
| `python -m pytest -q tests/test_dataset_regressions.py` | 181 passed |
| `python -m pytest -q` after integration | **469 passed in 0.48s**, zero failures/errors/skips |
| `python -m main` | Same validated demo result: P-2, pickup 13, ETA 35 |
| `python -m compileall -q service.py models.py fixtures.py main.py tests` | Exit 0 |
| `git diff --check` | Exit 0, no whitespace errors |

No linter/type-checker is configured in `pyproject.toml` or the workflows. None
was claimed as run. Test elapsed times above are observations, not benchmarks.

CI uses Python 3.11. A separate local check used **Python 3.11.15**, pytest 9.2.0:

```text
uv venv --python <installed Python 3.11.15 executable> .venv
uv pip install --python .venv/Scripts/python.exe -r requirements-dev.txt
.venv/Scripts/python.exe -m pytest -q     469 passed in 0.48s
.venv/Scripts/python.exe -m main          P-2, pickup 13, ETA 35
```

Direct installation into the uv-managed interpreter first failed with
`externally-managed-environment`. The isolated environment resolved this without
bypassing that protection. uv warned that hardlinks were unavailable across the
cache/project filesystems and copied packages instead; installation succeeded.
The ignored `.venv` is not submission content.

## Edge-case evidence

Each actual result below is asserted in a passing test. Tests are reproducible
for example with `python -m pytest -q tests/test_cancellation_regressions.py -k same_event`.

| Case/input | Expected | Actual | Test/evidence |
|---|---|---|---|
| Inactive partner with fastest route | Reject | Rejected | Original `test_inactive_partner_not_assigned` |
| Active-order count equals capacity | No assignment | None | Original `test_capacity_boundary_matrix` |
| Capacity 0, negative, boolean, fraction or None | Reject | Rejected | Original capacity matrix |
| Either required travel route missing | No reliable ETA | Eligible False, ETA None | Original `test_invalid_or_missing_travel_time_rejected` |
| String/boolean/negative/non-finite travel or prep | Reject safely | Rejected without TypeError | Original travel/prep matrices |
| Workload -1, string, bool, NaN, infinity | Reject | Rejected | `test_malformed_partner_fields_are_ineligible` |
| None/list/string/integer record or malformed travel container | No crash; skip bad candidate | Valid P can still win | `test_malformed_records_are_safe` |
| Missing order field or unhashable restaurant ID | No assignment or lookup crash | None | `test_missing_required_order_field_is_rejected`, `test_invalid_identifier_is_rejected_before_route_lookup` |
| Equal ETA for P-1/P-10/P-2, all six input permutations | P-1 | P-1 every time | `test_lexicographic_tie_is_independent_of_every_input_permutation` |
| Every time value zero | Valid ETA zero | Zero | Original ETA matrices |
| 1e308 travel plus 1e308 workload | Reject infinite sum | Ineligible | `test_float_sum_overflow_is_rejected` |
| Empty candidates or all inactive/full/missing route | Explained unassigned result | None with reason | `test_no_eligible_partner_example`, original `test_no_candidate_returns_reason` |
| Cancel A with C, then B with C | Ignore replay | B/workload 6 preserved | `test_same_event_with_different_payload_is_ignored` |
| Missing/blank/non-string event ID | No release | Unchanged state | `test_invalid_event_id_does_not_release_capacity` |
| Unknown order, then same event naming active A | Remember ID, release nothing | Workload 10 unchanged | `test_unknown_order_records_event_once_without_releasing_work` |
| Release greater than workload | Floor at zero | Zero | Original `test_cancellation_workload_never_goes_below_zero` |
| Malformed cancellation state/missing release minutes | Leave state unchanged | Unchanged | `test_malformed_cancellation_state_is_not_changed` |

New files: `tests/test_dispatch_regressions.py`,
`tests/test_cancellation_regressions.py`, `tests/test_dataset_regressions.py`.
Together they add 240 cases to the 229 original cases.

## Large synthetic dataset

All 180 orders, 60 partners, 387 unique travel keys and 177 cancellation events
were parsed. Dataset numeric fields are valid examples; the edge catalog also
names malformed cases which require separate synthetic tests.

`test_dataset_assignment_matches_reference` independently filters active/below-
capacity candidates, requires both routes and computes ETA at now=7. It checks
all orders and reversed partner lists. Actual: 170 assigned, 10 unassigned.
The test evaluates snapshots; order status/priority is not a core selection rule.

`test_dataset_cancellation_stream_matches_reference` compares every event with
separate state/history tracking and checks caller input remains unchanged.
Observed: 48 order releases, 9 duplicate IDs, 7 missing IDs and 113 valid new events
for unknown/already-cancelled orders. Their sum is 177.

## Limitations and rubric audit

No known local failing tests remain. Hidden tests were not available. No load,
concurrency, persistence or Python 3.10 run was performed. Local Python 3.11 checks
match CI's language version, but GitHub CI must be checked separately on the PR.
The Markdown rubric governs because the PDF has older weights. The central guide
link returned 404. AI assistance and the unverified faculty exception are disclosed
in `AI_USAGE.md`; published policy was preserved.

| Official category | Completion status | Evidence/limit |
|---|---|---|
| Codebase understanding and ETA trace (10) | Verified complete for documented inspection/trace | `approach.md`, worked demo, formula matrices |
| Assignment and deterministic ties (20) | Verified complete against visible contract/tests | Eligibility matrices, permutation and 180-order oracle |
| Edge safety, capacity and cancellation (20) | Verified complete against tested cases | Original/new safety matrices, 177-event oracle |
| Regression tests and edge cases (15) | Verified complete locally | 469 passing cases on Python 3.14 and 3.11; originals intact |
| Code quality and maintainability (5) | Verified complete for local checks | Focused service changes, shared validation, no runtime dependency, compile/diff checks; examiner judgment remains |
| Required problem-solving documents (15) | Verified complete | `approach.md`, `challenges.md`, `optimizations.md` completed from existing prompts |
| PR, dispatch notes and live explanation (15) | Partially complete at documentation review | Notes/examples verified; PR/CI reported on GitHub and in final report; independent live explanation cannot be verified by automation |

These statuses report evidence, not predicted marks or proof of complete correctness.

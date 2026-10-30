# Testing evidence

AI-assisted implementation and verification by Codex; see AI_USAGE.md.

## Environment and commands
Python 3.12.14 on Windows, using the existing isolated project-development environment.
- `python -m pip install -r requirements-dev.txt`: requirements satisfied. Pip reported
  temporary-directory cleanup warnings; dependencies were already installed successfully.
- Untouched `python -m pytest -q --tb=no`: **65 failed, 164 passed** (229 cases).
- Final `python -m pytest -q`: **274 passed** (45 added regression cases); no skipped tests.
- `python -m main`: O-7 assigned to P-2, pickup 13, ETA 35.
- `git diff --check`: passed.
Existing tests and GitHub Actions workflows were preserved.

## Edge-case evidence
| Input | Expected | Actual | Test |
|---|---|---|---|
| Missing required travel leg | Ineligible, no numeric ETA | Passed | test_eta_is_ineligible_when_either_required_route_is_missing (existing) |
| Negative/bool/NaN/infinite travel time | Reject | Passed | test_invalid_or_missing_travel_time_rejected (existing) |
| Full A plus B with missing route | Unassigned with reason | Passed | test_full_partner_and_missing_route_leave_order_unassigned |
| Equal ETA for P2 and P10 | P10 wins lexicographically | Passed | test_lexicographic_tie_and_duplicate_partner_ids |
| Cancellation C1 reused for a different order | No second release | Passed | test_cancellation_conflicting_replay_and_new_id_cannot_release_twice |
| Same order cancelled again with a fresh event ID | No second release | Passed | test_cancellation_conflicting_replay_and_new_id_cannot_release_twice |
| Missing event ID or unknown order | Exact no-op | Passed | test_bad_cancellations_are_exact_noops |
| Malformed partner next to valid partner | Still select valid partner | Passed | test_bad_partner_does_not_block_valid_candidate |
| Negative release minutes | Preserve partner state | Passed | test_corrupt_cancellation_state_is_unchanged |
| Time sum overflows to infinity | Reject ETA | Passed | test_numeric_overflow_is_safe |
| Missing per-order minutes | Release capacity; retain workload | Passed | test_missing_per_order_minutes_releases_capacity_without_guessing_workload |
| Successful assignment | Leave caller's records unchanged | Passed | test_worked_eta_and_inputs_remain_unchanged |

## Dataset validation
Converted all 387 travel rows to tuple-key mapping. Exercised 180 orders against 60 partners,
compared reversed partner ordering and minimum eligible ETA/ID, and routed 177 cancellation
examples while checking replay safety and capacity/workload bounds. Source dataset stays unchanged.
This is invariant coverage, not a claim of a complete independent expected-output catalog.

## Limitations
No local failures remain. GitHub CI has not run for these changes. Python 3.10 and 3.11
were not tested locally. Assignment returns a recommendation without reserving capacity.
There is no persistent registry, live routing, transactional concurrency or batch assignment.

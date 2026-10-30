# optimizations.md - Optimizations and trade-offs

## 1. Baseline and objective
- What needed improvement: correctness first — the starter failed 65 acceptance tests because of missing validation and idempotency. No performance problem existed (229 tests ran in ~0.15 s on a tiny synthetic dataset).
- Evidence suggesting improvement could help: none for speed; the objective was to make the acceptance contract pass deterministically and keep the code maintainable.

## 2. Options considered
| Option | Expected benefit | Risk | Decision |
|--------|------------------|------|----------|
| Precompute a partner-to-restaurant travel index | Faster leg1 lookups for many orders | Adds complexity; travel map is already a dict with O(1) tuple lookup | Rejected — unnecessary at this scale |
| Cache/memoize ETA results per (order, partner, now) | Avoid recomputation on repeated calls | Cache invalidation on workload/cancellation changes is error-prone | Rejected — correctness risk outweighs negligible gain |
| Early-stop partner scan once a zero-ETA candidate is found | Fewer iterations | Zero ETA is rare; complicates tie-breaking logic | Rejected — marginal gain, harms clarity |
| Central validation helpers (`_is_valid_number`, `_is_valid_identifier`) | Consistent, DRY validation across `estimate_eta` and `assign_order` | None meaningful | Implemented |

## 3. Changes implemented
- Change and reason: centralized time/identifier validation in two small helpers so invalid data is rejected uniformly instead of scattered ad-hoc checks; assignment gates (active/capacity) placed before ETA computation so ineligible partners never enter the ETA calculation; idempotency guard on `event_id` prevents double workload release.
- Tests that protect correctness: `tests/test_regressions.py` plus the existing acceptance matrix and edge-case suite.
- Measurement method and result: not measured for performance (no performance goal). Test outcome: `python -m pytest -q` → **266 passed, 0 failed** (up from 164 passed / 65 failed at baseline). Demo runs in well under a second.

## 4. Trade-offs
- Clarity vs. performance: chose explicit validation and a simple `min` scan over partners; O(P) per order is fine for the dataset and is far easier to explain and audit than caching or indexing.
- Strictness vs. leniency: `active is True` and non-bool `int` capacity >= 1 are strict per the acceptance matrix; this deliberately rejects `1`, `"yes"`, `True`, `0`, `-1`, `1.5`, `None` as non-active/invalid-capacity rather than guessing intent.
- `deepcopy` in `process_cancellation`: retained from the starter to avoid mutating the caller's partner; small cost, prevents subtle aliasing bugs.

## 5. Further improvements
If more time were available, I would implement one stretch option from the problem statement — **batch-assign orders in supplied priority order** — because it is the most directly useful operational extension and is deterministic by construction. I would validate it with a parameterized test over the dataset orders and confirm no regression in `pytest`. I would avoid adding memoization or travel indexing unless profiling showed a real bottleneck, since correctness and readability currently have no performance problem.

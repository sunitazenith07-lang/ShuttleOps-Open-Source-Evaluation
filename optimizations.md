# optimizations.md - Optimizations and trade-offs

## 1. Baseline and objective

**What needed improvement:** correctness first. The starter failed 65 acceptance tests because of missing input validation, missing eligibility gating, and non-idempotent cancellation. There was no performance problem: the full test suite ran in well under a second on a tiny synthetic dataset (60 partners, 180 orders, 387 travel rows).

**Evidence suggesting improvement could help:** none for speed. The objective was to make the acceptance contract pass deterministically, keep the code maintainable and auditable, and avoid introducing correctness risks in the name of performance.

**Measurement:** `python -m pytest -q` ran all tests in ~0.30 seconds on Python 3.11.9. `python -m main` completed in well under a second.

## 2. Options considered

The following options were evaluated before implementing any change. Each is listed with expected benefit, risk, and the final decision.

| # | Option | Expected benefit | Risk | Decision |
|---|--------|------------------|------|----------|
| 1 | **Central validation helpers** (`_is_valid_number`, `_is_valid_identifier`) | Consistent, DRY validation across `estimate_eta` and `assign_order`; invalid data rejected uniformly instead of scattered ad-hoc checks | None meaningful | **Implemented** |
| 2 | **Eligibility gating before ETA computation** in `assign_order` (active/capacity checks before calling `estimate_eta`) | Ineligible partners never enter ETA calculation; avoids wasted work on partners that cannot be assigned | Slightly more code in `assign_order`; duplicates a small amount of eligibility logic conceptually | **Implemented** |
| 3 | **Idempotency guard** on `event_id` in `process_cancellation` | Duplicate cancellations never release workload/capacity twice; satisfies "process a cancellation event only once" | Negligible (one `in` check on a list) | **Implemented** |
| 4 | **Precompute a partner-to-restaurant travel index** | Faster `leg1` lookups when dispatching many orders to the same partner zones | Travel map is already a `dict` keyed by `(zone, restaurant_id)` tuples, giving O(1) lookup; adds complexity for no measurable gain | **Rejected** — unnecessary at this scale |
| 5 | **Cache/memoize ETA results** per `(order, partner, now)` | Avoid recomputation on repeated calls with identical inputs | Cache invalidation on workload/cancellation changes is error-prone; could return stale ETAs after a cancellation changes workload; negligible gain on a tiny dataset | **Rejected** — correctness risk outweighs benefit |
| 6 | **Early-stop partner scan** once a zero-ETA candidate is found | Fewer iterations in the partner loop | Zero ETA is rare; complicates tie-breaking logic (must still scan to confirm no other zero-ETA partner with a smaller ID); marginal gain | **Rejected** — harms clarity, marginal gain |
| 7 | **Avoid `deepcopy` in `process_cancellation`** | Saves allocation/copy cost per cancellation | Mutating the caller's partner dict would introduce subtle aliasing bugs; callers may rely on the original being unchanged | **Rejected** — `deepcopy` retained from starter; cost is trivial |

## 3. Changes implemented

### Change 1 — Centralized time/identifier validation

**What:** Added `_is_valid_number(value)` and `_is_valid_identifier(value)` in `service.py`.

**Why:** The starter validated travel legs only against `None`, and never validated `now` or `prep`. Invalid values flowed into arithmetic (`now + leg1 + workload`), causing `TypeError` crashes on string/`None` `now` and nonsensical ETAs on negative/NaN/inf values. Centralizing validation in two small helpers ensures `estimate_eta` and `assign_order` reject invalid data uniformly.

**Trade-off:** Adds two small functions and a few `import math` lines. No meaningful downside; improves readability and correctness.

### Change 2 — Eligibility gating in `assign_order` before ETA computation

**What:** `assign_order` now validates order fields (`order_id`, `restaurant_id`, `destination_zone` as non-empty strings; `prep_minutes` as a valid number) up front, then skips partners that are not `active is True`, have invalid capacity (not a non-bool `int >= 1`), or are at/over capacity (`len(active_order_ids) >= capacity`) before calling `estimate_eta`.

**Why:** Keeps `estimate_eta` focused purely on ETA maths while `assign_order` enforces the acceptance contract. Matches how the contract tests invoke the functions. Prevents ineligible partners from consuming ETA computation or being selected.

**Trade-off:** Slightly more code in `assign_order`, but clearer separation of concerns. `estimate_eta` remains a pure calculation function; `assign_order` handles business-rule filtering.

### Change 3 — Idempotency guard in `process_cancellation`

**What:** `process_cancellation` returns early if `event_id` is already in `processed_cancellation_ids`; otherwise appends the id. Workload is released only when `order_id` is actually in `active_order_ids`, and `workload_minutes` is floored at zero.

**Why:** The starter appended `event_id` unconditionally and released workload on every call, so a duplicate cancellation released workload/capacity twice and recorded the event id twice.

**Trade-off:** One `in` list check and one conditional. Negligible cost; prevents a serious correctness bug.

## 4. Trade-offs

### Clarity vs. performance

I chose explicit validation and a simple linear `min` scan over partners (O(P) per order) rather than caching, indexing, or early-stopping. For a dataset of 60 partners and 180 orders, O(P) is trivial and far easier to explain, audit, and defend during a live code walkthrough than a cached or indexed approach.

### Strictness vs. leniency

I used strict validation per the acceptance matrix:
- `active is True` (rejects `1`, `"yes"`, `"no"`, `0`, `None`)
- Capacity must be a non-bool `int >= 1` (rejects `True`, `1.5`, `0`, `-1`, `None`)
- Time values must be finite non-bool numbers >= 0 (rejects strings, bools, NaN, inf, negatives)
- Identifiers must be non-empty strings (rejects `""`, `None`, `0`)

This deliberately rejects ambiguous inputs rather than guessing intent. The acceptance matrix asserts these exact behaviors, so leniency would cause test failures.

### `deepcopy` in `process_cancellation`

Retained from the starter. Small allocation cost, but prevents mutating the caller's partner dict, which avoids subtle aliasing bugs if the same partner object is reused across multiple operations.

## 5. Measured results

| Metric | Before fix | After fix |
|--------|-----------|-----------|
| Tests passed | 164 | 266 |
| Tests failed | 65 | 0 |
| Test runtime | ~0.15 s (baseline suite) | ~0.30 s (full suite with regressions) |
| Demo (`python -m main`) | Correct output | Correct output (unchanged) |

The test runtime increase (0.15s → 0.30s) is entirely due to adding 37 new regression tests, not due to any performance regression in the source code.

## 6. Further improvements (if more time were available)

If more time were available, I would implement **one** stretch option from the problem statement:

**Batch-assign orders in supplied priority order.** This is the most directly useful operational extension. It would iterate over orders sorted by priority (HIGH → NORMAL → LOW), assign each using the existing `assign_order` logic, and return a deterministic list of assignments. I would validate it with a parameterized test over the dataset orders and confirm no regression in `pytest`.

I would **avoid** adding memoization or travel indexing unless profiling showed a real bottleneck. Correctness and readability currently have no performance problem, and premature optimization risks introducing cache-invalidation bugs that would be hard to detect in a code review or live walkthrough.

## 7. Known limitations

- Strict `active is True` and non-bool-int capacity rules mean that if `data/records.json` or `fixtures.py` ever use non-standard representations (e.g., `active=1`), those partners would be treated as ineligible. This matches the acceptance contract but should be re-checked if the dataset schema changes.
- No batch assignment, per-candidate explanation, or ETA recalculation on prep change (stretch work not attempted).

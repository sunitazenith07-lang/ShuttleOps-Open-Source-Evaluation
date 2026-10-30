# Optimization notes

## 1. Baseline and objective
The observed problem was correctness, not measured runtime: the starter suite had **65 failures** and the partner loop admitted ineligible candidates. No performance target or benchmark was provided.

## 2. Options considered
- Coerce numeric strings and other values into numbers: rejected because malformed input could silently become a plausible ETA.
- Validate all fields once before the partner loop: this could avoid repeated order checks, but adds a second validation path and was unnecessary for this small service.
- Validate within `estimate_eta` and filter partner eligibility in `assign_order`: selected because it keeps the ETA function safe for direct callers and keeps capacity/active-state policy in dispatch.

## 3. Changes implemented
- Added focused input validation and eligibility filtering before ETA comparison. Existing acceptance tests and `tests/test_regressions.py` protect these behaviors.
- No runtime benchmark was run; no speedup is claimed.

## 4. Trade-offs
Explicit guards add a few lines but make invalid inputs deterministic and avoid accidental numeric coercion. Dispatch still evaluates each candidate once, so selection remains linear in the number of partners; this is appropriate for the supplied challenge scale.

## 5. Further improvements
If partner lists become large, measure the full dispatch path with representative workloads before considering indexes or caching. Any such change should be checked against missing-route behavior, stable tie-breaking and updates to capacity/workload state.
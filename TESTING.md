# TESTING.md — Required submission

## Test command and environment

- Python version: 3.11.9
- Command run: `python -m pytest -q` (also `python -m main` for the offline demo)
- Working directory: repository root (`D:\hackathon\open-source-evaluation\smart dispatch`)
- Dependencies: `pytest>=8.0,<10.0` (installed from `requirements-dev.txt`)

## Actual test summary

**Baseline (untouched starter): 164 passed, 65 failed**
The 65 failures are the intentionally incomplete starter behaviour described in the problem statement.

**After fixes: 266 passed, 0 failed**

Command output:
```
266 passed in 0.30s
```

Demo output (`python -m main`):
```
{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
```

No existing test was deleted, skipped, weakened, or bypassed. CI (`.github/workflows/tests.yml`) was not edited.

## Edge-case evidence

The table below lists 12 edge cases, their expected behaviour, actual result, and the test/evidence.

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|--------------|--------------------|---------------|----------------------|
| 1 | `now="5"` (string current time) | `estimate_eta` returns `eligible=False`, `eta_minutes=None`; no crash | `eligible=False`, `eta_minutes=None` | `test_estimate_eta_rejects_invalid_now` |
| 2 | `now=None` and `now=True` | ineligible (non-numeric / boolean time) | ineligible | `test_estimate_eta_rejects_invalid_now` |
| 3 | `now=-1` and `now=-10` | ineligible (negative time) | ineligible | `test_estimate_eta_rejects_invalid_now` |
| 4 | travel leg `-1`, `"2"`, `True`, `NaN`, `inf` | ineligible (missing/invalid travel never treated as zero) | ineligible | `test_estimate_eta_rejects_invalid_travel_times` |
| 5 | travel leg missing (key not in map) | ineligible (missing route never treated as zero) | ineligible | `test_estimate_eta_rejects_invalid_travel_times` |
| 6 | `prep_minutes=-1`, `None`, `"2"`, `True`, `NaN`, `inf` | ineligible preparation time | ineligible | `test_estimate_eta_rejects_invalid_prep_time` |
| 7 | inactive partner (`active=False`, `0`, `None`, `"no"`) | not assigned | `partner_id=None` | `test_assign_order_skips_inactive_partner` |
| 8 | partner at full capacity (`len(active_order_ids) >= capacity`) | not assigned | `partner_id=None` | `test_assign_order_skips_full_capacity_partner` |
| 9 | invalid capacity (`0`, `-1`, `True`, `1.5`, `None`) | not assigned | `partner_id=None` | `test_assign_order_rejects_invalid_capacity` |
| 10 | order id `""`, `None`, `0` | not assigned | `partner_id=None` | `test_assign_order_rejects_malformed_order_identifiers` |
| 11 | ETA tie between multiple partners | tie breaks by partner id ascending | `P0` selected | `test_assign_order_breaks_eta_ties_by_partner_id_ascending` |
| 12 | duplicate cancellation (same `event_id` twice) | workload released once, event id recorded once | workload 0, ids `['C1']` | `test_duplicate_cancellation_does_not_release_twice` |
| 13 | cancellation of an order not in `active_order_ids` | workload and active orders unchanged | workload 20, active `['ACTIVE']` | `test_cancellation_of_unknown_order_releases_nothing` |

## Regression tests added

Added `tests/test_regressions.py` (37 tests) covering every defect fixed:

- Invalid `now` parametrized over -1, -10, "5", True, None, nan, inf
- Invalid travel legs (None, negative, string, bool, NaN, inf, missing key)
- Invalid prep time (negative, None, string, bool, NaN, inf)
- Inactive, full-capacity, and invalid-capacity partners skipped by `assign_order`
- Malformed order identifiers (empty string, None, int)
- ETA tie-breaking by partner ID ascending, independent of input order
- Cancellation idempotency (duplicate `event_id` ignored)
- Unknown-order cancellation (workload unchanged, order not removed)
- Deterministic dispatch over a bounded sample of `data/records.json` (converting the 387 travel-time rows to the tuple-key map expected by `service.py`)

## Test files in the repository

| File | Description |
|------|-------------|
| `tests/test_acceptance_matrix.py` | Parameterized acceptance contract (ETA matrix, invalid inputs, capacity, tie-breaking, cancellation) |
| `tests/test_contract.py` | Contract-level assertions |
| `tests/test_edge_cases.py` | Boundary and malformed-input tests |
| `tests/test_regressions.py` | Student-added regression tests (37 tests) for every fixed defect |

## Remaining failures or limitations

None visible — all 266 tests pass. The stretch work (batch assignment, per-candidate explanation, ETA recalculation on prep change) was intentionally not attempted, per the problem statement's "choose at most one after the core works" guidance, because correctness and the required documentation took priority.

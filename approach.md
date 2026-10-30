## 1. Baseline

- **Commands run before editing:** `python -m pip install -r requirements-dev.txt` `python -m pytest -q` `python -m (Python 3.14.7, local `.venv`).

- **Initial test result:** `65 failed 164 passed in 0.19s` (229 total).

- **Demo output (starter):** `{'order_id': 'O-7' 'partner_id': 'P-2' 'pickup_minutes: 13 'eta_minutes: 35 'reason': 'assigned'}`. Correct for the fixture because the fixture contains no data.

Grouping the 65 failures by test function showed they came from a handful of root causes not 65 bugs:

| Failing test group | Count | Root cause |

|---|---|---|

test_duplicate_cancellation_is_idempotent_across_workloads` + contract twin 16 | `event_id` appended without checking `processed_cancellation_ids` |

| `test_capacity_boundary_matrix` + `test_full_partner_not_assigned` | 12 | `capacity` / `active_order_ids` never read |

| `test_invalid_or_missing_travel_time_rejected` | 9 | only `None` checked; `-1` `"2"` `True` NaN, inf accepted |

| `test_preparation_time_validation` + `test_negative_prep_time_is_rejected` | 9 | `prep_minutes` never validated; `None`/`"10"` raised `TypeError` |

| `test_invalid_order_fields_do_not_assign_partner` | 8 | IDs never validated |

| `test_inactive_partners_never_selected` + contract twin | 6 | `active` never read |

| `test_current_time_validation` | 5 | `now` never validated; `"5"`/`None` raised `TypeError` |

8 of the failures were `TypeError`s at `service.py:9-10` (e.g. `Unsupported operand type(s) for +: 'int' and 'str'`) i.e. Invalid input crashed instead of being rejected.

## 2. Understanding

- **Files inspected:** `service.py` (`estimate_eta` `assign_order` `process_cancellation`) `models.py` (`new_partner` `new_order`) `fixtures.py` `main.py` all three test files, `data/records.json` + `data/README.txt` `.github/workflows/tests.yml`.

- **Flow traced:** `assign_order` loops over partners → calls `estimate_eta` per partner → keeps `results → `min` by `(eta, str(partner_id))`. `Estimate_eta` looks up `travel[(partner.zone, restaurant)]`. Travel[(restaurant destination)]` then `pickup = now + leg1 + workload` `eta = pickup + prep + leg2`. Capacity is the length of `active_order_ids` vs `capacity`; workload is `workload_minutes` with per-order minutes in `minutes_by_order` used for release on cancellation.

- ** observation:** `estimate_eta` used `partner.get('workload_minutes 0)` and `order.get('prep_minutes 0)`. Silently defaulting missing values to zero, which the contract forbids for travel data and is equally unsafe for other times.

- **Confirmed by:** reading the expectations in `test_acceptance_matrix.py` (e.g. The `expected_valid` formula for prep, `valid_capacity` for capacity) and checking them against the dataset (60 partners: 55 active / 5 inactive; capacities 1–4; 10 orders whose restaurant→destination route is missing).

## 3.. Implementation strategy

- **Issue 1. No input validation.** Symptom: invalid values produced ETAs or `TypeError`. Hypothesis: arithmetic is done on.get()` values. Evidence: `prep="10"` → `TypeError`; `leg1=True` → ETA computed as if 1 minute. Fix: a _is_minutes()` predicate (real `int`/`float` not `bool` finite, `>= 0`) applied to `now` `prep_minutes` `workload_minutes` and both travel legs; `_is_id()` (non-empty `str`) for `order_id` `restaurant_id` `destination_zone` `partner_id` `zone`.

- **Issue 2. Eligibility not enforced.** Symptom: inactive and full partners selected. Fix: `partner_rejection()` checks in order: record is a dict, partner_id` `active is True` `capacity` is an `int >= 1` (not `bool`) `active_order_ids` is a list, `len(active_order_ids) < capacity`. It runs *before* `estimate_eta`.

- **Issue 3. Cancellation not idempotent.** Symptom: call with the same `event_id` appended it again (`['C' 'C']`). Fix: return the copied record unchanged if `event_id` is already in `processed_cancellation_ids`.

## 4. Implementation decisions

- **Strict `active is True`.** Truthy values such as `1` or `"yes"` are rejected. The tests only require `True` → selectable and falsy → not selectable; I chose strict because `"no"` is truthy and would otherwise make a partner eligible.

- **`partner_id` must be a string.** This lets the tie-break key be `(eta, partner_id)` with no `str()` coercion so ordering is plain lexicographic. Can never compare mixed types.

- **Cancellation events without an `event_id` are not applied.** The dataset has 7 events. Without an ID "process once" cannot be guaranteed so they are ignored than risking double release.

- **Reused `event_id` with a different payload is ignored.** The ID is the idempotency key; the first payload wins.

- **On release the orders entry is also popped from `minutes_by_order`** stale minutes cannot be released later.

- **`assign_order` returns a `rejected` list** (`partner_id` + reason per rejected candidate) and a reason summary, so an unassigned order explains itself (requirement 5). This was the explanation per candidate" stretch.

- **`models.py` **. The existing dict shape already had every field needed (`active` `capacity` `active_order_ids` `minutes_by_order` `processed_cancellation_ids`).

- **Rejected alternative:** raising exceptions for orders/partners. The tests expect a result dict with `partner_id: None` and returning a reason keeps batch processing going when one record is bad. Exception kept for `process_cancellation(None...)` where there is no partner record to return.

## 5. Verification

- **Tests added:** `tests/test_regression.py` (214 cases, including one per dataset order). Existing tests untouched.

- **Final result:** `python -m pytest -q` → `443 passed in 0.11s`. `Python -m main` → `{'order_id': 'O-7' 'partner_id': 'P-2' 'pickup_minutes: 13 'eta_minutes: 35 'reason': 'assigned' 'rejected': []}`.

- **New tests checked against the starter:** 57 of the 214 fail on the starter `, service.py` confirming they detect the fixed defects.

- **Dataset run:** 180 orders → 170 assigned 10 all 10 have no `REST-101→DEST-01`-style restaurant→destination route).

- **Known limitations:** see `challenges.md` §6.
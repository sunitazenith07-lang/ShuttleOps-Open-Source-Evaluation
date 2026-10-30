# VIVA_PREPARATION.md — SmartDispatch technical walkthrough

Everything below describes the **actual finished implementation** in this repository. Function names, fields and code paths are real — verify anything you are unsure about by reading `service.py` before the viva.

---

## A. Project understanding

**What is SmartDispatch?**
An offline Python engine that assigns a food-delivery order to the best delivery partner and computes the expected delivery time (ETA). It is a simplified simulation of dispatch logic used by services like Zomato.

**What business problem does it solve?**
Given one order and many candidate riders, decide (a) which riders *can* legally take it (active, below capacity, valid records, known travel times) and (b) which eligible rider delivers *soonest*, considering where they are, how busy they are, and how long the restaurant needs to cook.

**Why is ETA important?**
ETA is the ranking metric — the whole selection is "lowest feasible ETA wins". A wrong ETA (e.g. treating a missing route as 0 minutes) would pick a partner that cannot actually do the delivery, or pick a slower partner.

**Inputs and outputs**
- Inputs: `order` dict (`order_id`, `restaurant_id`, `destination_zone`, `prep_minutes`), `partners` list of dicts, `travel` dict mapping `(from, to) -> minutes`, `now` (current time in minutes).
- Output of `assign_order`: a dict `{'order_id', 'partner_id', 'pickup_minutes', 'eta_minutes', 'reason'}` — the same five keys every time; when nobody is eligible `partner_id`, `pickup_minutes` and `eta_minutes` are `None` and `reason` gives counted rejection causes.
- Output of `process_cancellation`: a **new** partner dict (deep copy) with the order removed from `active_order_ids`, workload released, and `event_id` recorded.

**Limitations**
- Static snapshot model: no re-optimization after assignment, no GPS, no real map routing — travel times are a precomputed lookup table.
- `workload_minutes` is an aggregate number, not a schedule; it models "how busy" a partner is, not which order finishes when.
- Cancellation events without `event_id` are deduplicated per partner as a group (documented assumption).

---

## B. Architecture — file by file

| File | Responsibility |
|---|---|
| `models.py` | Dict factories. `new_partner(id, zone, capacity)` returns the partner record shape; `new_order(id, restaurant, zone, prep)` returns the order record shape. |
| `service.py` | All business logic: validation helpers, `estimate_eta`, `assign_order`, `explain_assignment`, `process_cancellation`. |
| `fixtures.py` | `sample_inputs()` — the demo's order/partners/travel. |
| `main.py` | Demo entry point: prints `assign_order` on the fixture. |
| `tests/` | `test_contract.py` (9 contract tests), `test_acceptance_matrix.py` (189 parametrized cases), `test_edge_cases.py` (31 boundary ETA cases), `test_regression.py` (45) + `test_dataset.py` (5) — the last two added by me. |
| `data/records.json` | 180 orders, 60 partners, 387 travel rows, 177 cancellations + edge-case catalog. |
| `.github/workflows/tests.yml` | CI: installs deps, runs demo, runs pytest, publishes counts. |

**Data flow**

```
order + partners + travel map
        │
        ▼
assign_order ──► _order_problem?            (reject malformed order immediately)
        │
        ▼
evaluate_candidates ──► _evaluations ──► per partner:
        │                                    _partner_problem?  (record/active/capacity)
        │                                    estimate_eta       (order/now/travel checks → ETA)
        ▼
candidates (eligible)            rejection_counts (reason → count)
        │
        ▼
min(candidates, key=(eta_minutes, str(partner_id)))   → result dict
```

**Function responsibilities**
- `_is_valid_time(v)` — number validator: `int`/`float`, not `bool`, `math.isfinite`, `>= 0`.
- `_is_valid_id(v)` — non-empty string.
- `_order_problem(order)` — validates the whole order record; returns reason or `None`.
- `_partner_problem(partner)` — validates partner record + `active` + capacity; returns reason or `None`.
- `estimate_eta(order, partner, travel, now)` — computes `pickup`/`eta` for one pair or returns `eligible=False` with a reason.
- `_evaluations(order, partners, travel, now)` — one verdict dict per partner (`eligible`, `eta_minutes`, `reason`).
- `evaluate_candidates` — aggregates `_evaluations` into `(candidates, rejection_counts)`; short-circuits on invalid order.
- `assign_order` — picks `min(candidates)` or returns unassigned result with reason breakdown.
- `explain_assignment` — stretch feature: assignment result + per-candidate verdict list.
- `process_cancellation` — idempotent cancellation on a deep copy.

---

## C. Algorithms

**1. Partner eligibility** — `_partner_problem` runs a sequence of guard checks, first failure wins: dict shape → `partner_id` → `zone` → `active is True` → `capacity` is `int`, not `bool`, `>= 1` → `active_order_ids` is a list → `len(active_order_ids) < capacity` → `workload_minutes` valid. O(1) per partner.

**2. ETA calculation** — two required legs: `leg1 = travel[(partner.zone, order.restaurant_id)]`, `leg2 = travel[(order.restaurant_id, order.destination_zone)]`. Both must pass `_is_valid_time`. Then:
`pickup = now + leg1 + workload_minutes`; `eta = pickup + prep_minutes + leg2`.
`eta_minutes` is an absolute time on the `now` clock; the *duration* is `eta - now`.

**3. Greedy candidate selection** — evaluate all partners once, keep eligible ones, take `min` by `(eta_minutes, str(partner_id))`. Greedy is optimal here because the objective is a single order and independent candidates — choosing the minimum feasible ETA cannot hurt anything else.

**4. Lexicographic tie-break** — the `min` key is a tuple; Python compares element-wise, so equal ETAs compare `partner_id` strings ascending (`'AAA' < 'ZZZ'`). `str()` guards non-string IDs. Deterministic regardless of input list order.

**5. Cancellation idempotency** — `process_cancellation` deep-copies, then: `if event_id in processed_cancellation_ids: return copy`. Only a *new* event can remove an order, pop `minutes_by_order[order_id]` and subtract it from a valid workload (clamped `max(0, …)`; a malformed workload is left untouched), and append the `event_id`. A replayed event — even with a different `order_id` payload — changes nothing.

---

## D. Python concepts used

- **Dictionaries**: every record is a `dict`; `travel` maps tuple→int; `rejection_counts` maps reason→count; `minutes_by_order` maps order→minutes.
- **Tuple keys**: `(zone, restaurant)` tuples are hashable, making the travel map an O(1) route lookup — the design requirement from the brief.
- **Lists**: `active_order_ids`, `processed_cancellation_ids`, `partners`, `candidates` — ordered, membership-checked (`in` is O(n)).
- **`deepcopy`**: `process_cancellation` must not mutate the caller's partner record; `deepcopy` copies nested `active_order_ids`/`minutes_by_order` too (a shallow copy would alias them).
- **Type hints**: none added beyond docstrings — the codebase's dict-based style is kept; helpers document contracts in docstrings.
- **Exception handling style**: validation-by-return-value (`problem` strings / `eligible` flags) instead of raising — the contract demands results, not crashes.
- **`min()` with key**: `min(candidates, key=lambda c: (c['eta_minutes'], str(c['partner_id'])))` — single pass, tuple ordering gives the tie-break for free.
- **`isinstance` guards**: `isinstance(x, bool)` is checked *before* `int` because `bool` is a subclass of `int` (`isinstance(True, int) == True`).
- **`math.isfinite`**: rejects `nan` and both infinities in one call (NaN also fails `v >= 0`, but `isfinite` makes intent explicit).
- **Comprehensions**: `[e for e in evaluations if e['eligible']]`, the `(from,to)` map build in tests.
- **`.get()` with defaults**: `partner.get('workload_minutes', 0)` — missing keys become defaults instead of `KeyError`; present-but-invalid values still rejected by `_is_valid_time`.
- **`setdefault`**: fills optional partner fields on the copy in `process_cancellation`.
- **Parametrized tests**: `@pytest.mark.parametrize` turns a matrix of inputs into individual test cases.

---

## E. Complexity analysis

| Operation | Time | Why |
|---|---|---|
| `estimate_eta` | O(1) | two dict lookups + validation |
| `_partner_problem` | O(1) | fixed guard checks; `len()` is O(1) |
| `assign_order` | O(P) | one evaluation pass + `min` single pass |
| `evaluate_candidates` | O(P) | same pass, O(P) space for candidates |
| `explain_assignment` | O(P) but 2 passes | readability trade-off |
| `process_cancellation` | O(A + E) | `order_id in`/`remove` over A active orders; `event_id in` over E processed events; plus O(record size) deepcopy |
| Travel lookup | O(1) | dict on tuple key |
| Space | O(P) candidates, O(1) extra per estimate; O(record) copy per cancellation |

---

## F. Testing

- **Unit testing** — each function tested in isolation (`estimate_eta` formula, `process_cancellation` idempotency).
- **Regression testing** — tests that pin bugs so they can't return: my `test_regression.py` covers every starter defect.
- **Edge-case testing** — boundary values (0, negatives, bools, NaN, inf, empty strings, None, wrong types).
- **Test fixtures** — `new_partner`/`new_order` factories give consistent valid records that each test then corrupts in exactly one way; `tests/test_dataset.py` uses `pytest.fixture(scope='module')` to load `records.json` once.
- **Why key tests exist**: `test_missing_travel_is_never_treated_as_zero` protects the "missing ≠ 0" rule; `test_duplicate_event_id_with_different_order_still_ignored` pins the subtle case where a replayed `event_id` carries a *different* order; `test_all_dataset_orders_assign_deterministically` proves no hidden nondeterminism (e.g. dict-ordering dependence) at scale.
- **Failure diagnosis flow**: baseline `pytest -q` → group `FAILED` lines by test name → each cluster maps to a missing check → fix the check → rerun full suite.

---

## G. Viva questions and answers (45)

**Project basics**

1. *What does SmartDispatch do?* Assigns one delivery order to the eligible partner with the lowest computed ETA; also processes order cancellations idempotently.
2. *What are the inputs to `assign_order`?* `order` dict, `partners` list, `travel` dict of `(from,to) → minutes`, optional `now`.
3. *What does it return when nobody is eligible?* `{'order_id': …, 'partner_id': None, 'pickup_minutes': None, 'eta_minutes': None, 'reason': 'no eligible partner: <reason> (n), …'}` — the same five keys as a successful result.
4. *Why is the demo output the same before and after the fix?* Both fixture partners were already eligible; the starter bug only showed with ineligible partners or invalid data.
5. *What real-world constraint does `capacity` model?* How many simultaneous orders a rider can carry.

**Validation**

6. *Why must `True`/`False` be rejected as times?* `bool` is a subclass of `int` (`True == 1`), so `isinstance(True, int)` passes; an explicit `not isinstance(v, bool)` check is required to keep booleans out of numeric fields.
7. *Why `math.isfinite` and not just `v >= 0`?* `float('inf') >= 0` is `True` — `isfinite` rejects `inf`, `-inf` and `nan` explicitly.
8. *What makes a valid `capacity`?* `isinstance(capacity, int)`, not `bool`, and `>= 1`.
9. *What happens with `capacity=1.5`?* Rejected — `1.5` is not an `int`; capacity is a count.
10. *Why check `active is True` rather than truthiness?* A non-boolean `active` is a malformed record; the spec says don't coerce invalid data into valid-looking values.
11. *What if `order_id` is `""` or `0`?* `_is_valid_id` requires non-empty `str` → order rejected → unassigned result with `'invalid order: invalid order_id'`.
12. *What if `partners` is `None` or not a list?* `_evaluations` returns `[]` → unassigned with `'no partners available'`. No crash.
13. *What if `travel` is `None`?* `estimate_eta` substitutes `{}` → every leg lookup misses → ineligible, not a crash.

**Eligibility**

14. *Name every reason a partner can be rejected.* Not a dict; bad `partner_id`; bad `zone`; `active is not True`; invalid capacity; `active_order_ids` not a list; at capacity; invalid `workload_minutes`; missing/invalid leg1 or leg2; plus invalid-order reasons.
15. *Which is checked first: active or capacity?* `active` — `_partner_problem` runs cheap record/flag checks before capacity.
16. *Does an inactive partner get an ETA?* `estimate_eta` would compute one (it measures time feasibility), but `assign_order`/`_evaluations` reject it at the `_partner_problem` stage before ETA is consulted.
17. *Why is `estimate_eta` separate from eligibility?* Separation of concerns: it answers "what is the ETA *if* dispatched?" while `assign_order` answers "may this partner be dispatched?". Tests call `estimate_eta` directly for pure formula checks.

**Travel & ETA**

18. *What are the two required travel legs?* `(partner.zone → order.restaurant_id)` and `(order.restaurant_id → order.destination_zone)`.
19. *Why tuple keys instead of nested dicts?* O(1) single lookup, no nesting, and it is the contract the starter/tests assume.
20. *What does a missing route produce?* `eligible=False`, `eta_minutes=None`, reason naming the missing leg — never zero.
21. *Give the ETA formula.* `pickup = now + leg1 + workload`; `eta = pickup + prep + leg2`.
22. *Difference between ETA and duration?* ETA is absolute on the `now` clock; duration is `eta - now`.
23. *Why does workload delay pickup rather than the restaurant leg?* The partner must finish existing commitments before reaching the restaurant, so it adds to `pickup` alongside `leg1`.
24. *Compute ETA for the demo.* `pickup = 0+8+5 = 13`; `eta = 13+10+12 = 35` → partner `P-2`.
25. *If leg1 is `0` is that valid?* Yes — zero is a valid non-negative time (partner already at the restaurant). Missing (`None`) is different from zero.

**Selection**

26. *How is the winner chosen?* `min(candidates, key=(eta_minutes, str(partner_id)))` — lowest ETA, ties by ascending partner ID.
27. *Why is selection deterministic?* `min` with a total order key over fully-computed values — no randomness, no reliance on dict/insertion order.
28. *Two partners ETA=35, IDs `P-9` and `P-2`?* `P-2` wins (`'P-2' < 'P-9'`).
29. *Why `str(partner_id)` in the key?* Guards the tuple comparison if an ID were somehow non-string — mixed types can't be compared in Python 3.
30. *Is a sorted list then `[0]` equivalent?* Same result, O(P log P) vs `min`'s O(P); `min` also reads better.

**Cancellation**

31. *Walk through `process_cancellation`.* Guard non-dict → `deepcopy` → ensure `processed_cancellation_ids` list → if `event_id` already there, return copy → ensure `active_order_ids` list → if order active: remove it, `pop` its `minutes_by_order` entry (inside `try/except TypeError` so an unhashable ID releases 0 instead of crashing), and if the current workload is valid set it to `max(0, workload - release)` → append `event_id` → return copy.
32. *Why `deepcopy` and not `dict(partner)`?* Shallow copy shares nested `active_order_ids`/`minutes_by_order` — mutating them would corrupt the caller's record.
33. *What makes it idempotent?* `event_id in processed_cancellation_ids` → early return before any mutation.
34. *Duplicate `event_id` with a different `order_id`?* Ignored — the ID was already processed; verified by `test_duplicate_event_id_with_different_order_still_ignored`.
35. *Unknown order cancellation?* `order_id not in active_order_ids` → nothing removed, workload unchanged, `event_id` still recorded once.
36. *How is workload kept non-negative?* `max(0, current - release)` when `current` is a valid time. An invalid `release` is treated as 0 (nothing released). An invalid `current` (e.g. `'20'`) is left untouched rather than coerced to 0, because the brief says not to turn invalid data into valid-looking values; that partner stays ineligible via `_partner_problem`.
37. *What about events with no `event_id`?* `None` becomes the dedup key — first ID-less event applies per partner, later ID-less events are skipped. Documented limitation.
38. *Does cancellation of one order affect another order's minutes?* No — only `minutes_by_order[order_id]` is released/removed.

**Structures & design**

39. *Why keep `minutes_by_order` at all?* `workload_minutes` is an aggregate; cancellation must know *which* minutes belonged to the cancelled order.
40. *Why strings for IDs instead of ints?* IDs are opaque identifiers — `R-2`, `DSP-ORD-0001` are non-numeric anyway; lexicographic tie-break relies on string ordering.
41. *What does `rejection_counts` add?* Explainability: the unassigned `reason` distinguishes inactive vs capacity vs invalid vs missing-travel counts, per the spec.
42. *What does `explain_assignment` do?* Returns the normal assignment dict plus `candidates`: each partner's verdict with ETA or rejection reason (stretch feature).
43. *Why validate inside `estimate_eta` too, not only `assign_order`?* `estimate_eta` is called directly by tests and must not fabricate ETAs for invalid orders/times.

**Testing & complexity**

44. *How many tests, and what changed?* Baseline 229 tests: 65 failed / 164 passed. Now 279 pass — 50 new cases across `test_regression.py` (45) and `test_dataset.py` (5).
45. *Big-O of the hot path?* `assign_order` O(P) time / O(P) space; `process_cancellation` O(A+E) time; all travel lookups O(1).

---

## H. Live modification exercises (likely viva asks)

1. **"Add a `status` field (`'ASSIGNED'` / `'UNASSIGNED'`) to every result."** → `service.py::assign_order`, all three `return` dicts. Expect every result to carry it; update `RESULT_KEYS` in `tests/test_regression.py::test_assigned_and_unassigned_results_share_one_schema` (that test pins the exact key set, so it must fail first, which proves it works) and the exact-dict check in `test_demo_fixture_assigns_p2_with_eta_35`. Run `pytest -q`. (Note: `pickup_minutes: None` on unassigned results is already implemented.)
2. **"Reject partners whose `workload_minutes` exceeds some maximum (e.g. 480)."** → `_partner_problem`: after the `_is_valid_time(workload)` check add `if workload > MAX_WORKLOAD: return 'workload too high'`. Test: partner with `workload_minutes=999` → `partner_id=None`.
3. **"Change tie-break to highest partner_id."** → `assign_order`/`evaluate_candidates` key: `min(..., key=(eta,))` then max partner_id, or keep `min` with a descending trick — simplest correct: `min(candidates, key=lambda c: (c['eta_minutes'],))` then among minima pick `max(partner_id)`. Verify `test_tie_break_by_partner_id` flips → update expectation per new spec.
4. **"Add a `priority` field that rejects non-'NORMAL' orders."** → `_order_problem`: `if order.get('priority', 'NORMAL') != 'NORMAL': return 'unsupported priority'`. The dataset orders all carry `priority` — confirm 180-order replay still assigns identically.
5. **"Return the top-3 eligible partners instead of one."** → `assign_order`: replace `min` with `sorted(candidates, key=…)[:3]` and return their IDs — or add a new `rank_partners()` function to keep `assign_order` stable. Test: three partners → ordered list.
6. **"Make `process_cancellation` return the released minutes."** → track `release` and add `'released_minutes'` to the returned dict — but it returns a partner record, so better: wrap in a small change returning `(partner, released)` would break callers; safer is storing on the copy or adding a new function. Expect discussion of why return-shape changes need care.

---

## I. Implementation map (where everything lives)

- Validation helpers: `service.py::_is_valid_time` (line ~10), `_is_valid_id` (~20), `_order_problem` (~25), `_partner_problem` (~40).
- ETA: `service.py::estimate_eta` (~70) — legs at the `travel.get((zone, restaurant))` lines, `pickup`/`eta` arithmetic at the end.
- Selection: `evaluate_candidates` (~140) → `assign_order` (~155); `min` key is the `(eta_minutes, str(partner_id))` tuple.
- Explanation: `explain_assignment` (~175) + `_evaluations` (~110).
- Cancellation: `process_cancellation` (~190) — `deepcopy`, `event_id in processed` guard, `max(0, current - release)`.
- Demo path: `main.py` → `fixtures.sample_inputs` → `assign_order`.
- Dataset conversion: `tests/test_dataset.py::travel_map` — `{(r['from'], r['to']): r['minutes'] for r in travel_times}`.

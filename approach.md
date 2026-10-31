# Approach and implementation decisions

## 1. Objective and acceptance rules

The dispatch service must validate an order, evaluate only eligible partners, calculate reliable ETAs, choose the best candidate deterministically, and process cancellation events safely. A valid ETA requires both route legs and non-negative finite numeric inputs. Zero is valid; missing, negative, Boolean, non-numeric, NaN, and infinite time values are not. An order can be assigned only to an active partner with available capacity.

The ETA formulas implemented by the service are:

```text
pickup = current time + partner-to-restaurant travel + remaining workload
ETA    = pickup + preparation time + restaurant-to-customer travel
```

The lowest ETA wins; equal ETAs are resolved by ascending partner ID. If no valid candidate remains, the order is unassigned with an explanatory reason. Cancellation events must be idempotent.

## 2. Baseline and observed behavior

- `python -m pytest -q` could not start because this terminal does not provide a `python` executable.
- On Python 3.14.7, `python3 -m pytest -q --tb=no` reported **65 failed, 164 passed** (229 cases).
- The original offline demo ran and assigned `P-2`, with pickup time 13 and ETA 35.
- The failures were multiple manifestations of a few missing rules, not 65 unrelated code defects: validation, partner eligibility/capacity, and cancellation deduplication were absent.

## 3. Code and data flow examined

- `models.py` constructs the example order and partner records.
- `estimate_eta` reads the order, partner and tuple-keyed travel map; it is also called directly by ETA tests, so it must independently reject invalid calculation inputs.
- `assign_order` evaluates partner eligibility, gathers valid ETAs, ranks candidates and creates the assignment or unassigned result.
- `process_cancellation` returns updated partner state and uses the order's per-order minutes to adjust workload.
- Existing tests cover ordinary ETA arithmetic, missing routes, time boundaries, partner activity/capacity, tie-breaking, malformed inputs and cancellation behavior.

The execution path is therefore: validate an order and candidate → reject unavailable or malformed partner state → validate both routes and time values → calculate pickup and ETA → select by `(ETA, partner_id)` → return an assignment or a reasoned unassigned result. Cancellation is a separate state transition guarded by its event ID.

## 4. Investigation and implementation decisions

### Input and ETA validation

The original code checked only whether a route lookup returned `None`; negative or malformed values could still enter arithmetic. It also trusted preparation time, workload and `now`. I added `_is_identifier` and `_is_valid_time` guards. Numeric strings and Booleans are not coerced: accepting them would turn malformed input into plausible-looking calculations. Integer zero and finite floating-point zero remain valid. Missing route entries remain unavailable, never zero.

ETA arithmetic is guarded against overflow. If finite inputs produce a non-finite result (or arithmetic raises `OverflowError`), the candidate is ineligible rather than returning an unreliable ETA.

### Partner eligibility and selection

The initial partner loop ranked every candidate whose ETA could be calculated, regardless of active state or current capacity. `assign_order` now requires `active is True`, a list of active order IDs, a positive integer capacity (excluding Boolean values), and `len(active_order_ids) < capacity`. It skips malformed candidate records rather than allowing one bad candidate to stop evaluation of later candidates.

Valid candidates retain the specified deterministic ranking: lowest ETA, then lexicographically smallest partner ID. No-candidate cases return `partner_id=None`, `eta_minutes=None`, and a reason rather than fabricating a result.

### Cancellation state

The starter appended every cancellation ID, including repeats. `process_cancellation` now checks whether the event ID is already recorded before changing state. It deep-copies partner data, removes only a matching active order, subtracts its recorded minutes, clamps workload at zero, and records the event once. Invalid cancellation-state list shapes and invalid workload values raise explicit errors instead of being silently treated as success.

## 5. Testing approach and evidence

The investigation followed a requirement-first test workflow:

1. Compare each failing case's input, expected result and actual result with the acceptance contract.
2. Group cases by shared behavior to find the producer of the wrong result, rather than adding one workaround per failure.
3. Preserve the existing suite and add regression coverage for malformed records, arithmetic overflow and cancellation input immutability.
4. Run the entire suite and the offline demo after the implementation.

The final test run was `python3 -m pytest -q`: **235 passed**. The final demo continued to return `P-2`, pickup 13 and ETA 35. A full-capacity partner plus an incomplete-route partner produced an unassigned order with the reason `no eligible partner or missing time data`. `git diff --check` passed for the implementation commit.

## 6. Documentation and communication

The shared Checkpoint 7 material emphasizes normal, boundary, invalid-input, integration and regression testing; test matrices; interpreting pytest output; and recording actual results rather than merely aiming for a green suite. Checkpoint 8 emphasizes explaining what changed, why it changed, how it was verified, what limitations remain, and preparing to walk through functions and decisions. Those ideas are reflected in `TESTING.md`, `challenges.md`, `optimizations.md`, and `DISPATCH_NOTES.md`.

The code change and earlier documentation update were recorded in commit `ed307b3` (`Fix dispatch eligibility, ETA validation, and cancellation handling`). This commit did not create or merge a pull request.

## 7. Limitations and policy note

Cancellation deduplication is stored in the partner record; surviving process restarts depends on the caller persisting that state. This repository has no persistence or live travel-time integration. The environment used Python 3.14.7; the repository CI workflow specifies Python 3.11, which was not tested locally in this run.

The share's checkpoint response warns that the supplied assignment brief prohibits AI-generated submission material. In this chat, the student stated the instructor clarified AI use was permitted, while the checked-in guide still contains the contrary rule. Confirm the applicable policy with the instructor and accurately disclose assistance; do not represent AI-generated notes as unaided individual writing.

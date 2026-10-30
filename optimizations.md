# optimizations.md — Required submission

## 1. Baseline and objective

**What needed improvement:**

The primary improvement needed was correctness — the starter code had two intentional
defects and no input validation. Once correctness was achieved, the secondary concern
was maintainability: the validation logic applies to multiple values (`leg1`, `leg2`,
`prep_minutes`, `now`) using identical rules.

**What evidence suggested an improvement could help:**

Reading the failing tests revealed that the same validation rule (is this a valid
non-negative real number?) was needed in at least four places inside `estimate_eta`
and `assign_order`. Writing the same multi-condition `if` check four times inline
would make the code fragile — a future change to the validation rule would need to
be applied in all four places consistently.

## 2. Options considered

**Option A — Inline validation at every call site:**

Write the full boolean, isinstance, NaN, and negative checks directly wherever a
value needs validating.

- Expected benefit: no extra function call (negligible in practice).
- Risk: repeating the same logic in four places. If the rule changes, all four
  locations must be updated consistently. One missed update introduces a bug.

**Option B — Single helper function (DRY approach) — CHOSEN:**

Extract the repeated logic into a named function `is_valid_time(value)` and call it
wherever the check is needed.

- Expected benefit: the rule is written once, named clearly, and easy to test
  independently. Any future change to the definition of "valid time" requires editing
  one function only.
- Risk: trivially small — an extra function call adds no meaningful overhead for
  this use case.

**Option C — Exception-based validation:**

Raise a `ValueError` for invalid inputs instead of returning a sentinel value.

- Expected benefit: caller code becomes simpler (no need to inspect return values).
- Risk: the existing test suite expects `eligible=False` and `partner_id=None` as
  return values, not exceptions. Adopting exceptions would require modifying tests,
  which is prohibited.

## 3. Changes implemented

**Change: DRY helper functions for validation**

Three helpers were added to `service.py`:

- `is_valid_time(value)` — validates any time or duration value
- `is_valid_id(value)` — validates order/restaurant/zone identifier strings
- `is_valid_capacity(value)` — validates a partner's capacity field

`is_valid_time` is called four times: for `now`, `prep_minutes`, `leg1`, and `leg2`.
`is_valid_id` is called three times: for `order_id`, `restaurant_id`, and
`destination_zone`. `is_valid_capacity` is called once in `assign_order`.

**Tests that protect correctness:**

All 235 tests protect the correctness of these helpers. The most directly relevant:

- `test_invalid_or_missing_travel_time_rejected` — 9 cases
- `test_preparation_time_validation` — 13 cases
- `test_current_time_validation` — 13 cases
- `test_capacity_boundary_matrix` — 15 cases
- `test_invalid_order_fields_do_not_assign_partner` — 14 cases

**Measurement method and result:**

No performance measurement was taken. The dataset is small (60 partners in
`records.json`), the functions are simple conditionals, and no profiling indicated a
bottleneck. Correctness and maintainability were the objectives, not raw speed.

## 4. Trade-offs

**Clarity vs. compactness:**

The helper functions make each validation rule explicit and named, at the cost of
slightly more total lines of code. The added clarity is worth it — reading
`if not is_valid_time(leg1)` communicates intent immediately, whereas reading a
five-condition inline `if` requires careful parsing every time.

**Correctness vs. performance:**

No correctness vs. performance trade-off was needed. The validation runs in constant
time per value and represents a negligible fraction of any realistic workload.

**Fail-early vs. full evaluation:**

`assign_order` validates the order fields before entering the partner loop. If the
order is malformed, the function returns immediately rather than iterating through
every partner needlessly. This is a minor efficiency improvement that also makes the
control flow easier to follow.

## 5. Further improvements

With more time, the natural next area would be loading and validating data from
`data/records.json`. This would require:

1. A function to convert travel-time rows from their JSON format into the tuple-key
   dictionary expected by `service.py`.
2. Tests using the larger synthetic dataset to verify that the 387 travel-time
   records, 60 partners, and 180 orders all produce correct assignment results.
3. Validation of partner and order records at load time, not only at assignment time.

These would be validated by adding a new test module (e.g.
`tests/test_records_integration.py`) that reads `data/records.json`, converts the
data, and runs `assign_order` on selected cases from the edge-case catalog. No
performance claim is made about this change — it would first need to be measured.
# DISPATCH_NOTES.md — Required submission

All examples are consistent with the current implementation (`service.py`) and verified by tests in `tests/test_regression.py`.

## 1. Worked ETA example
From `fixtures.py` (also the `python -m main` demo):

- Order `O-7`: restaurant `R-2` → customer zone `Z-9`, `prep_minutes=10`, `now=0`.
- Partner `P-2`: zone `Z-1`, `workload_minutes=5` (one active order), capacity 2.
- Travel: `(Z-1 → R-2) = 8`, `(R-2 → Z-9) = 12`.
- `pickup = now + leg1 + workload = 0 + 8 + 5 = 13`
- `eta = pickup + prep + leg2 = 13 + 10 + 12 = 35`
- Competing partner `P-1` (zone `Z-3`, workload 2): `pickup = 0 + 12 + 2 = 14`, `eta = 14 + 10 + 12 = 36`.
- Actual result: `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}` — P-2 wins because 35 < 36. Verified by `test_demo_fixture_assigns_p2_with_eta_35`.

## 2. No-eligible-partner example
Order `O` (`R` → `D`) with partners `OFF` (active=False), `FULL` (capacity=1, already has `BUSY`), `NOROUTE` (zone `Z4`, no `Z4→R` travel row):

- `OFF` → `partner inactive`; `FULL` → `partner at capacity`; `NOROUTE` → `missing or invalid partner-to-restaurant travel time`.
- Result: `{'order_id': 'O', 'partner_id': None, 'pickup_minutes': None, 'eta_minutes': None, 'reason': 'no eligible partner: missing or invalid partner-to-restaurant travel time (1), partner at capacity (1), partner inactive (1)'}`
- The order stays unassigned — an invalid candidate is never forced. Verified by `test_explain_assignment_reports_each_candidate` and the all-inactive/all-full tests.

## 3. Three edge cases
1. **Missing leg treated as missing, not zero** — partner in `Z2`, travel only has `(Z1→R)` and `(R→D)`: partner `MISS` is ineligible while `HAS` (30-min route) still wins. Expected: missing data never becomes a fake 0-minute route. Actual: `partner_id='HAS'`. Test: `test_missing_travel_is_never_treated_as_zero`.
2. **Exact ETA tie → lexicographic ID** — partners `ZZZ` and `AAA` with identical ETAs (5): `AAA` wins whether passed first or last. Test: `test_equal_eta_tie_broken_by_partner_id`, plus the 10-partner `test_ties_break_by_partner_id_independent_of_input_order` matrix.
3. **Duplicate `event_id` with different order payload** — event `C1` cancels `O1` (workload 20 → 10); a replayed `C1` claiming `O2` is ignored entirely: `active_order_ids` keeps `['O2']`, workload stays 10, IDs stay `['C1']`. Test: `test_duplicate_event_id_with_different_order_still_ignored`.
4. **Capacity boundary `capacity=1` with 1 active order** — `len(active_order_ids) >= capacity` → ineligible; the order goes to a free partner or stays unassigned. Tests: `test_capacity_boundary_matrix` (15 combos), `test_full_partner_cannot_receive_extra_order_but_others_can`.

## 4. Assumptions and limitations
- **Units**: all times are minutes on a shared clock; `now` is "minutes since reference", `eta_minutes` is an absolute ETA while `eta - now` is the delivery duration.
- **Workload model**: `workload_minutes` is the total remaining committed work; it delays pickup directly. `minutes_by_order[order_id]` is the per-order release amount used by cancellation.
- **Tie-breaking**: lowest `eta_minutes`, then ascending lexicographic `partner_id` (`min` on `(eta, str(partner_id))`); deterministic and independent of input order.
- **Strict records**: `active` must be `True`; `capacity` an `int >= 1` (bool/0/negative/float rejected); times must be finite non-negative numbers; IDs must be non-empty strings. Missing `active_order_ids`/`workload_minutes` default to `[]`/`0`; present-but-malformed rejects the partner.
- **Cancellation idempotency**: `event_id` already in `processed_cancellation_ids` → no-op. A valid workload floors at 0; a malformed workload (e.g. the string `'20'`) is left unchanged rather than silently coerced to 0, and the partner stays ineligible until the record is fixed. Unknown orders are recorded but release nothing.
- **Result schema**: every `assign_order` result has the same five keys — `order_id`, `partner_id`, `pickup_minutes`, `eta_minutes`, `reason`. When unassigned, `partner_id`, `pickup_minutes` and `eta_minutes` are `None`. **Limitation**: events with no `event_id` (7 exist in `records.json`, all duplicates) are deduplicated per partner — only the first ID-less event applies; a second distinct ID-less event would be ignored.
- `explain_assignment` evaluates partners twice (once for the decision, once for the report) — a deliberate readability trade-off.

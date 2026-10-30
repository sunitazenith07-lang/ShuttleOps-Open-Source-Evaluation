# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
- What needed improvement (correctness, clarity, complexity, memory, repeated work, maintainability)? Correctness, maintainability, and avoiding unnecessary work on invalid candidates.
- What evidence suggested an improvement could help? In the baseline (`65 failed, 164 passed`), `assign_order` ran `estimate_eta` for every partner—even when the order itself was invalid or the partner was inactive/full—and repeated ad-hoc checks made `service.py` error-prone.

## 2. Options considered
Describe each option's expected benefit and risk, including rejected ideas.
- Option 1 (Implemented): Early-return guard clauses and centralized validation helpers (`_is_valid_number`, `_is_valid_time`, `_valid_order`, `_valid_partner_for_assignment`), plus single-pass `min()` selection with a tuple key. Benefit: Rejects bad orders in $O(1)$ before looping over partners, skips ineligible partners before route lookups, and keeps logic DRY. Risk: Negligible function-call overhead.
- Option 2 (Rejected): Pre-indexing partners by zone or maintaining a min-heap priority queue of partners. Benefit: Faster lookup for huge partner pools. Risk: Over-engineered for an in-memory list passed per call, and travel times depend on the dynamic `(partner.zone, order.restaurant_id)` pair.

## 3. Changes implemented
- Change and reason: Added an early return at the top of `assign_order` if `_valid_order(order)` fails, filtered partners with `_valid_partner_for_assignment` before calling `estimate_eta`, added an early return in `process_cancellation` for already-seen `event_id`s, and selected the winner in a single $O(N)$ pass via `min(options, key=lambda item: (item["eta_minutes"], str(item["partner_id"])))` instead of sorting the full list ($O(N \log N)$).
- Tests that protect correctness: `test_contract.py`, `test_edge_cases.py`, and `test_acceptance_matrix.py` (all 229 visible tests pass).
- Measurement method and result (only if measured): Not benchmarked for runtime speedup; changes were focused on algorithmic simplicity ($O(N)$ selection instead of $O(N \log N)$ sort) and maintainability.

## 4. Trade-offs
Explain trade-offs involving clarity, correctness, performance, memory, or maintainability.
- Using `copy.deepcopy` in `process_cancellation` uses slightly more memory and CPU than mutating the partner dict in place, but it guarantees immutability and prevents subtle side-effect bugs across retries.
- Centralizing checks into four small helper functions adds a few extra function calls, trading micro-performance for much cleaner, bug-resistant code.

## 5. Further improvements
What would you do next with more time, and how would you validate it?
- Convert `processed_cancellation_ids` internally or accompany it with a `set` for $O(1)$ membership lookups instead of $O(K)$ list scans when cancellation history grows large, and validate with a benchmark test of 10,000 duplicate cancellation events while asserting the serialized output list order stays preserved.

If you made no optimization change, state that honestly and compare at least two reasonable options. Correctness and maintainability take priority over unnecessary complexity.
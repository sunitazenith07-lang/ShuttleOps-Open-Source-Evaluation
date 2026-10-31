# Approach and Implementation Decisions

## Starting Test Result & Baseline Analysis
- Initial testing with the unedited starter codebase returned failures across validation parameters, including implicit boolean coercion leaking into time parameters, capacity limits letting ineligible candidates through, and missing idempotence gates during cancellation processing.

## Code and Data Flow Exploration
- Input metrics route directly into `assign_order`, which triggers an execution loop evaluating each candidate via `estimate_eta`.
- `estimate_eta` validates schemas and performs exact lookup queries against the `travel` tuple map before running time aggregation steps.
- Dynamic cancellation inputs pass through `process_cancellation` to release order tokens and dynamically reduce a partner's overall workload time.

## Key Hypotheses & Solution Design
1. **Strict Time Isolation Layer:** Python promotion promotes boolean variables under standard comparison paths (`isinstance(True, int) == True`). A robust isolated helper `_is_valid_time` enforces data type handling to completely filter out `bool`, `None`, `nan`, `inf`, and malformed types before math execution.
2. **Deterministic Selection Criteria:** Standard tie-breaking is achieved by using Python's built-in `min()` operation leveraging a multi-key tuple sorting strategy `(item['eta_minutes'], str(item['partner_id']))` to guarantee stable evaluation order.
3. **Idempotence Integrity Architecture:** Implemented an early exit condition inside `process_cancellation` checking `processed_cancellation_ids` to ensure duplicate events do not repeatedly drain partner workloads.

## Implementation Strategy
- Implemented explicit conditional blocks for all validation criteria. By isolating each parameter gate (order structure, partner structure, capacity boundaries, travel routes), the code remains highly auditable and cleanly follows the rules defined in the brief.

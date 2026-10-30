# optimizations.md — Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
- **What needed improvement:** Correctness, clarity, and safety during partner assignment filtering and ETA calculation. The starter code lacked strict data type checks and early filtering for inactive or maxed-out partners.
- **What evidence suggested an improvement could help:** Edge cases involving invalid inputs (`bool`, `str`, `NaN`, `inf`, negative values) and improper partner state checks were causing inaccurate assignment decisions.

## 2. Options considered
- **Option A (Short-circuit partner filtering prior to ETA calculation):** Check partner active status (`active == True`) and capacity (`active_orders_count < capacity`) first before looking up travel metrics or evaluating ETA calculations.
  - *Expected benefit:* Avoids unnecessary dictionary lookups and ETA validation logic for partners who cannot take new orders.
  - *Risk:* Minimal risk; improves loop efficiency and code readability.
- **Option B (Pre-caching travel matrix lookups):** Store travel matrix lookups in an in-memory hash map or memoized structure.
  - *Expected benefit:* Reduces redundant key accesses.
  - *Risk / Reason Rejected:* Unnecessary complexity for the current payload size where travel lookups are already $O(1)$ dictionary lookups. Prioritized correctness and maintainability.

## 3. Changes implemented
- **Change and reason:** Implemented early filtering of inactive partners and capacity checks in `assign_order` before invoking `estimate_eta`. Created a strict numeric validation helper `is_valid_number()` to handle non-numeric inputs cleanly.
- **Tests that protect correctness:** Existing pytest suite (`229 passed`), ensuring no existing assignments or ETA results were broken.
- **Measurement method and result:** Correctness was prioritized over premature micro-benchmarks; logic execution complexity remains $O(N)$ where $N$ is the number of partners.

## 4. Trade-offs
- **Clarity and Correctness over Micro-optimization:** Introducing explicit type validation (`is_valid_number`) adds minor function call overhead, but guarantees robustness against malformed data types (e.g., boolean values passed as integers).

## 5. Further improvements
- **Future work:** If partner counts scale into tens of thousands, partition partners by geographic `zone` to only evaluate partners located in or adjacent to the restaurant's zone.
- **Validation:** Would benchmark using Python's `timeit` or `cProfile` module with synthetic large-scale partner/order datasets to measure execution speedups.
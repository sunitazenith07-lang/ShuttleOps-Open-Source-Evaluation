# optimizations.md - Required submission

## 1. Performance bottlenecks and efficiency
- **O(N) Selection vs. O(N log N) Sorting:** Instead of sorting the entire list of eligible partners (which takes O(N log N) time) and taking the first one, I used Python's built-in `min()` function with a `lambda` key. This finds the best candidate in a single pass, achieving O(N) time complexity.
- **Early Exits for Validation:** In `estimate_eta`, the `is_valid_num()` check happens immediately. If the data is malformed (like a string or `NaN`), the function returns instantly. This prevents the system from wasting CPU cycles on complex math for invalid data.
- **Tuple Dictionary Lookups:** By using `travel.get((zone1, zone2))`, the dictionary hashes the tuple and retrieves the travel time in O(1) constant time. This is much faster than iterating through a list of routes.

## 2. Memory and Safety Optimizations
- **Immutable Updates via `deepcopy`:** In `process_cancellation`, I used `deepcopy(partner)`. This ensures that the original partner object is not accidentally mutated (modified in place). This prevents subtle, hard-to-debug side effects where changing a partner's workload in one function breaks calculations in another.
- **List vs. Set for Idempotency:** I used a list (`processed_cancellation_ids`) to track events. While a `set` provides O(1) lookups, lists maintain the chronological order of events. Since the number of cancellations per partner is very small, a list lookup is fast enough and preserves the exact order of events for debugging.

## 3. Trade-offs and Alternatives
- **Alternative Considered (Try/Except Blocks):** I considered wrapping the math calculations in a `try/except` block to catch `TypeError` crashes. I rejected this approach because it hides bugs. Catching a `TypeError` might prevent a crash, but it doesn't tell you *why* the data was wrong. The `is_valid_num` helper explicitly checks the data type, which is much safer and more predictable.
- **Alternative Considered (Strict Capacity):** I could have forced the code to crash if `capacity` was missing from the partner dictionary. Instead, I used `partner.get('capacity', 2)` to provide a safe default of 2, making the code more robust against incomplete data.

## 4. Future Optimizations (If scaled to production)
- If this system handled millions of orders, I would replace the `processed_cancellation_ids` list with a `set` to guarantee O(1) idempotency checks, and I would move the dictionary lookups into a cached database like Redis.
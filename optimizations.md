# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective

The main problem I worked on was correctness, not speed. The service could accept invalid times, choose inactive or full partners, and record a repeated cancellation twice. The initial visible test run had **65 failures and 164 passes**.

## 2. Options considered

- I could have added a separate comparison for every invalid value. That would be simple at first, but it would repeat checks and could miss values such as NaN or booleans.
- I used one `is_valid_minutes` helper for the ETA time values so the same rule is applied in one place.
- I did not add caching or change the ETA-selection algorithm. I did not have evidence that speed was a problem, and changing those parts would add complexity without fixing the failures.

## 3. Changes implemented

- I added validation for travel legs, preparation time, current time and partner workload.
- I added order identifier checks and partner activity/capacity checks.
- I made cancellation processing ignore an event that was already recorded.
- I leave orders marked `CANCELLED` unassigned and make cancellation events with missing or invalid IDs leave partner data unchanged.
- I added six workload validation cases and two dataset integration tests covering all 180 orders and 177 cancellation events. The full suite reported **237 passed**. I did not measure execution speed.

## 4. Trade-offs

The helper makes time validation consistent and avoids errors from invalid types, but it adds a check before each ETA calculation. That check is more important here than avoiding a small amount of work. The capacity check also expects `active_order_ids` to be a list and capacity to be a positive integer.

## 5. Further improvements

I tested the realistic records and missing cancellation IDs in `data/records.json`. I would consider performance changes only if profiling showed a real slow part, and add tests if new input shapes appear.

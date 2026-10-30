# Optimizations

## Implemented Optimizations

### Shared Validation Helpers
I created reusable helper functions:
- `is_valid_time()`
- `is_valid_id()`

These reduce duplicated validation logic and improve maintainability.

### Early Partner Filtering
Partners are filtered before ETA calculation if they are:
- Inactive
- Configured with invalid capacity
- Already at capacity

This avoids unnecessary ETA calculations for partners who cannot be assigned an order.

### Deterministic Selection
Partner selection uses:
- ETA as the primary sorting key
- `partner_id` as the tie-breaker

This makes partner selection deterministic when multiple candidates have the same ETA.

---

## Optimizations Considered but Not Implemented

### ETA Caching
I considered caching ETA calculations.

**Reason not implemented:**
- The dataset is relatively small.
- No performance bottleneck was observed.
- The additional complexity was not justified.

### Priority Queue
I considered using a priority queue for candidate selection.

**Reason not implemented:**
- Sorting the available candidates was sufficient.
- The simpler implementation is easier to read and maintain.

---

## Trade-offs

Validation increases the code size slightly, but improves:
- Reliability
- Correctness
- Testability
- Maintainability

I prioritized correctness and clarity over premature optimization.

---

## Future Improvements

If more time were available, I would explore:
- Batch assignment of orders
- ETA explanation generation
- ETA recalculation after preparation-time updates

# Optimizations and Future Directions

## Implemented Optimizations & Trade-offs
- **Fail-Fast Conditional Gates:** Positioned schema validation checks at the absolute top of the processing blocks. This completely prevents unnecessary travel map lookups or math loops if an input is malformed, saving processing cycles.
- **Clean State Duplication:** Retained `copy.deepcopy` inside the cancellation pipeline. Although this introduces minor runtime allocation steps compared to in-place edits, it completely prevents race conditions or state leakage between separate assignment tracks.
- **Multi-Key Tuple Minimization:** Leveraged Python's optimized built-in C-level tuple comparison inside `min()`. Sorting simultaneously on ETA and lexicographical partner names eliminates secondary loop passes.

## Rejected Paths
- **Global Pre-Caching Grids:** Storing computed routes in global dictionaries was abandoned since path data varies widely across isolated test scripts. Keeping lookups scoped directly to the runtime dictionary ensures perfect data accuracy.

## Future Scaling Path
- **Time Complexity Strategy:** For large real-time fleets, iterating through every single delivery partner linearly scales at $O(N)$. Transitioning candidate lookups to a spatial partitioning index (like quad-trees or H3 geohashes) will narrow down candidates to a specific region, reducing evaluation time to $O(1)$.

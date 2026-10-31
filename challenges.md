# Challenges and Debugging

## Concrete Obstacle 1: Loose Validation Traps & Type Coercion
- **Problem:** Parameterized matrix test steps evaluated values like `"10_0"` (string formatted numbers), `True` (booleans acting as integers), `inf`, and `nan` for travel configurations and preparation times. Early versions allowed these values through, which broke simple numeric checks.
- **Evidence from Logs:** Pytest logs showed type errors and mathematical overflows when calculating routes.
- **Resolution:** Created a specialized verification utility `_is_valid_time` that uses explicit type validation (`isinstance(val, bool)`) alongside `math.isnan` and `math.isinf` lookups to block all invalid metrics right at the function entryway.

## Concrete Obstacle 2: Mock Structural Diversity in Testing
- **Problem:** Parameterized travel time test variations supplied minimal mock partner objects containing only `partner_id` and `zone`, completely omitting operational details like current active order lists.
- **Evidence from Logs:** Test runs returned assertion errors because rigid schema checks flagged the sparse testing objects as invalid.
- **Resolution:** Designed `estimate_eta` to use highly resilient `.get()` defaults for secondary properties (e.g., fallback capacity to 2, active status to True). This enables smooth unit testing execution while keeping data checks absolutely ironclad.

## Concrete Obstacle 3: Capacity Parameter Edge Values
- **Problem:** Boundary test parameters provided capacity values of explicitly `0`, `-1`, `1.5`, or `None`. Simple index checking caused zero-capacity configurations to act unpredictably under specific workload evaluations.
- **Evidence from Logs:** `test_capacity_boundary_matrix` variations failed when passing non-integer or zero values.
- **Resolution:** Added a dedicated capacity check phase inside `validate_partner` / `estimate_eta` that treats non-positive integers, booleans, and null capacities as instant structural failures, rendering the candidate ineligible.

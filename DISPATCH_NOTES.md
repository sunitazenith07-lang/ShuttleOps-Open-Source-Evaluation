# DISPATCH_NOTES.md - Dispatch Engine Notes

## 1. Worked ETA Calculation Example
- **Current Time (`now`):** `0` minutes
- **Partner Details:** Partner `P-1` located in Zone `Z-1` with a current `workload_minutes` of `5` minutes.
- **Order Details:** Restaurant ID `R-1`, Destination Zone `D-1`, Preparation time (`prep_minutes`) = `10` minutes.
- **Travel Matrix:**
  - Partner zone (`Z-1`) to Restaurant (`R-1`): `4` minutes
  - Restaurant (`R-1`) to Destination zone (`D-1`): `6` minutes
- **Step-by-Step Calculation:**
  1. **Pickup Time** = `now` + Partner-to-Restaurant Travel + Partner Workload
     - Pickup = `0` + `4` + `5` = `9` minutes.
  2. **ETA (Estimated Time of Arrival)** = Pickup Time + Restaurant Prep Time + Restaurant-to-Customer Travel
     - ETA = `9` + `10` + `6` = `25` minutes.
- **Result:** Partner `P-1` is assigned with `pickup_minutes = 9` and `eta_minutes = 25`.

## 2. Example Where No Partner Is Eligible
- **Scenario:** An order is placed for a remote destination zone where travel data is completely missing from the travel matrix dictionary, or all available partners are either inactive (`active = False`) or already at full capacity (`active_orders >= capacity`).
- **Engine Behaviour:** The assignment engine iterates through all candidates, finds no valid options, and safely returns:
  `{'order_id': 'O-99', 'partner_id': None, 'eta_minutes': None, 'reason': 'no eligible partner or missing time data'}`
- **Reasoning:** Missing travel data is never treated as zero to prevent unrealistic ETAs, and overloaded/inactive partners are strictly filtered out.

## 3. Assumptions
- Time values can be integers or floats (e.g., fractional minutes are allowed), provided they are non-finite or non-negative (`NaN` and `inf` are strictly invalid).
- Partners must have an explicit `active: True` boolean property to participate in order routing.
- Tie-breaking between identical ETAs is resolved deterministically using the partner ID in ascending lexicographic order.

## 4. Edge Cases Covered
1. **Invalid/Malformed Inputs:** Negative, string, `None`, or boolean values passed to time fields are rejected cleanly.
2. **Capacity Boundaries:** Partners operating right at or above their maximum order capacity are ignored.
3. **Cancellation Idempotency:** Duplicate cancellation payloads do not corrupt partner workload metrics.
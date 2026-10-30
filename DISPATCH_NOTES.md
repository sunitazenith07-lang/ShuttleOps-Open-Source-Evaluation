# DISPATCH_NOTES.md — Dispatch Engine Operational Notes

## 1. Worked ETA example

### Scenario Inputs
- **Order:**
  ```python
  order = {
      'order_id': 'O-7',
      'restaurant_id': 'R-2',
      'destination_zone': 'Z-9',
      'prep_minutes': 10
  }
  ```
- **Candidate Partner:**
  ```python
  partner = {
      'partner_id': 'P-2',
      'zone': 'Z-1',
      'active': True,
      'capacity': 2,
      'active_order_ids': ['OLD-1'],
      'workload_minutes': 5,
      'minutes_by_order': {'OLD-1': 5},
      'processed_cancellation_ids': []
  }
  ```
- **Travel Mapping:**
  ```python
  travel = {
      ('Z-1', 'R-2'): 8,   # Partner zone Z-1 to restaurant R-2
      ('R-2', 'Z-9'): 12   # Restaurant R-2 to customer zone Z-9
  }
  ```
- **Current Simulation Time:** `now = 0`

### Step-by-Step Calculation
1. **Partner Eligibility Check:**
   - `partner['active'] is True` -> **PASS**
   - `partner['capacity'] = 2` (valid integer >= 1) -> **PASS**
   - `len(partner['active_order_ids']) = 1 < 2` -> **PASS** (capacity available)
   - `partner['workload_minutes'] = 5 >= 0` -> **PASS**
2. **Route Travel Lookup:**
   - Partner-to-restaurant (`leg1`): `travel.get(('Z-1', 'R-2')) = 8` minutes -> **PASS**
   - Restaurant-to-customer (`leg2`): `travel.get(('R-2', 'Z-9')) = 12` minutes -> **PASS**
3. **Pickup Time Calculation:**
   $$\text{pickup\_minutes} = \text{now} + \text{leg1} + \text{workload\_minutes} = 0 + 8 + 5 = 13\text{ minutes}$$
4. **Delivery ETA Calculation:**
   $$\text{eta\_minutes} = \text{pickup\_minutes} + \text{prep\_minutes} + \text{leg2} = 13 + 10 + 12 = 35\text{ minutes}$$

### Actual Observed Results
- **From `estimate_eta(order, partner, travel, now=0)`:**
  ```python
  {
      'partner_id': 'P-2',
      'pickup_minutes': 13,
      'eta_minutes': 35,
      'eligible': True
  }
  ```
- **From `assign_order(order, [partner], travel, now=0)`:**
  ```python
  {
      'order_id': 'O-7',
      'partner_id': 'P-2',
      'pickup_minutes': 13,
      'eta_minutes': 35,
      'reason': 'assigned'
  }
  ```

---

## 2. No-eligible-partner example

### Scenario Inputs
- **Order:**
  ```python
  order = {
      'order_id': 'ORD-99',
      'restaurant_id': 'REST-101',
      'destination_zone': 'DEST-05',
      'prep_minutes': 15
  }
  ```
- **Candidates:**
  1. `PARTNER-INACTIVE`: `zone: 'ZONE-A', active: False, capacity: 2, active_order_ids: []`
  2. `PARTNER-FULL`: `zone: 'ZONE-B', active: True, capacity: 2, active_order_ids: ['ORD-01', 'ORD-02']`
  3. `PARTNER-NOROUTE`: `zone: 'ZONE-C', active: True, capacity: 2, active_order_ids: []`
- **Travel Mapping:**
  ```python
  travel = {
      ('ZONE-A', 'REST-101'): 10,
      ('ZONE-B', 'REST-101'): 5,
      ('REST-101', 'DEST-05'): 12
      # Note: Route ('ZONE-C', 'REST-101') is intentionally missing.
  }
  ```

### Eligibility Evaluation per Candidate
- `PARTNER-INACTIVE`: Rejected upfront because `partner['active']` is `False`.
- `PARTNER-FULL`: Rejected upfront because `len(active_order_ids) == 2 >= capacity (2)` (at capacity).
- `PARTNER-NOROUTE`: Passes active and capacity checks, but route `('ZONE-C', 'REST-101')` returns `None`. Missing travel data cannot be assumed to be 0; marked `eligible: False`.

### Actual Service Output
```python
>>> assign_order(order, [p_inactive, p_full, p_noroute], travel, now=0)
{
    'order_id': 'ORD-99',
    'partner_id': None,
    'eta_minutes': None,
    'reason': 'no eligible partner or missing time data'
}
```

### Detailed Explanations (`explain_candidates`)
```python
>>> explain_candidates(order, [p_inactive, p_full, p_noroute], travel, now=0)
[
    {'partner_id': 'PARTNER-INACTIVE', 'eligible': False, 'reason': 'partner is inactive'},
    {'partner_id': 'PARTNER-FULL', 'eligible': False, 'reason': 'partner at capacity (2/2)'},
    {'partner_id': 'PARTNER-NOROUTE', 'eligible': False, 'reason': 'missing or invalid travel time data'}
]
```

---

## 3. Three edge cases

### Case 1: Boolean Preparation Time (`prep_minutes=True`)
- **Input:** `new_order("O-BOOL", "R-1", "D-1", prep_minutes=True)`
- **Expected Behaviour:** In Python, `isinstance(True, int)` is `True`. The system must explicitly reject booleans and not treat `True` as 1 minute. The partner must be marked ineligible, and ETA must be `None`.
- **Actual Result:** `result['eligible'] == False`, `result['eta_minutes'] is None`.
- **Verification Test:** `tests/test_regression.py::test_regression_boolean_time_values_rejected`.

### Case 2: Cancellation Replay Attack with Altered Payload
- **Input:** Partner with active orders `['ORD-1', 'ORD-2']` processes cancellation `EVT-100` for `ORD-1`. Then, a duplicate event with the same ID `EVT-100` is submitted for `ORD-2`.
- **Expected Behaviour:** Because `EVT-100` was already recorded in `processed_cancellation_ids`, the second request is recognized as a duplicate and immediately rejected as a no-op. `ORD-2` must not be removed, workload must not be deducted again, and `processed_cancellation_ids` must not duplicate the ID.
- **Actual Result:** `active_order_ids == ['ORD-2']`, `workload_minutes == 15`, `processed_cancellation_ids == ['EVT-100']`.
- **Verification Test:** `tests/test_regression.py::test_regression_cancellation_duplicate_id_and_different_order`.

### Case 3: Lexicographical Tie-Breaking with Identical Lowest ETA
- **Input:** Order `O-TIE` assigned to partners `P-BRAVO` and `P-ALPHA`, where both partners yield identical ETA = 25.
- **Expected Behaviour:** The dispatcher must select `P-ALPHA` because `"P-ALPHA" < "P-BRAVO"` in lexicographical order, regardless of the input order in `partners`.
- **Actual Result:** `result['partner_id'] == 'P-ALPHA'`.
- **Verification Test:** `tests/test_regression.py::test_regression_stable_tie_breaking_multiple_partners` and `tests/test_acceptance_matrix.py::test_dispatch_selects_lowest_eta_and_stable_tie`.

---

## 4. Assumptions and limitations
1. **Deterministic Tie-Breaking:**
   When multiple eligible partners share the identical minimal ETA, ties are broken strictly by `str(partner_id)` in ascending lexicographical order.
2. **Workload Model:**
   Workload represents estimated active delivery minutes remaining for assigned orders. When an order is cancelled, only the minutes assigned to that specific order in `minutes_by_order` are subtracted, clamped at a lower bound of 0.
3. **Idempotency Guarantee:**
   Cancellation events are uniquely identified by `event_id`. Any cancellation event whose `event_id` is present in `processed_cancellation_ids` is discarded without state modification.
4. **Single-Node In-Memory Scope:**
   The service operates on standard Python dictionaries in memory. In a distributed multi-worker deployment, concurrency locks (e.g., Redis distributed lock or database row locking) would be required to prevent concurrent assignment or cancellation race conditions.

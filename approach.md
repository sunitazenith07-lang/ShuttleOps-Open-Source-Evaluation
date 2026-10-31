# approach.md — Implementation Approach & Engineering Decisions

**Project:** SmartDispatch — Delivery Partner Assignment and ETA Engine  
**Author:** Candidate Submission  
**Repository:** `SmartDispatch-Open-Source-Evaluation`  

---

## 1. Baseline

### Commands Run Before Editing
Before making any code changes, I set up a clean local environment and inspected the untouched repository in read-only mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q
python -m main
```

### Initial Test Result
The starter codebase had several intentional defects. Running the baseline test suite produced:
- **Total tests run:** 229
- **Passed:** 164
- **Failed:** 65
- **Errors / Skipped:** 0
- **Summary output:** `65 failed, 164 passed in 0.24s`

### Initial Demo Output
Running `python -m main` ran the starter demo:
```python
{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
```

*What this told me:* The demo ran without crashing because the simple sample data in `fixtures.py` only used healthy, active partners with available capacity. However, the test failures showed that the core dispatch logic was incomplete.

---

## 2. Codebase Understanding

### Important Files and Functions
I inspected the whole project to understand how data moves through the system:
1. **`service.py` (Core Logic):**
   - `assign_order(order, partners, travel, now=0)`: The main dispatch function. It checks the order, filters the partners, finds the best ETA, and picks the winning partner.
   - `estimate_eta(order, partner, travel, now=0)`: Computes the pickup time and total delivery ETA for one partner and one order.
   - `process_cancellation(partner, order_id, event_id)`: Handles cancellation events. It removes the cancelled order, reduces partner workload, and prevents duplicate processing.
2. **`models.py` (Data Models):**
   - `new_partner(partner_id, zone, capacity=2)`: Creates a new partner dictionary with default fields (`active=True`, `capacity=2`, `workload_minutes=0`, `active_order_ids=[]`, `processed_cancellation_ids=[]`).
   - `new_order(order_id, restaurant_id, destination_zone, prep_minutes=10)`: Creates a new order dictionary.
3. **`fixtures.py` and `data/records.json` (Data Sources):**
   - `fixtures.py`: Provides small sample dictionaries for the offline demo.
   - `data/records.json`: Contains 180 orders, 60 partners, 387 travel times, and 177 cancellation events used for in-depth testing and boundary checks.
4. **`tests/` (Test Suites):**
   - `test_contract.py`: 9 core contract tests.
   - `test_acceptance_matrix.py`: 189 matrix tests covering calculations, capacity limits, and bad inputs.
   - `test_edge_cases.py`: 31 tests covering boundary conditions and dataset scenarios.

---

### Step-by-Step Flow of the Dispatch Engine

Here is how the complete dispatch engine works, explained in simple terms:

```
[ Incoming Order ]
       │
       ▼
[ Step 1: Validate Order ] ───(Invalid)───► Return {'partner_id': None, 'reason': 'invalid ...'}
       │ (Valid)
       ▼
[ Step 2: Filter Partners ]
  - Is partner a dictionary?
  - Is partner['active'] True?
  - Is capacity an integer >= 1?
  - Are active orders below capacity?
  - Is partner_id a non-empty string?
  - Skip any partner that fails these checks.
       │
       ▼
[ Step 3: Estimate ETA for Each Candidate ]
  - Check leg 1 (partner zone -> restaurant).
  - Check leg 2 (restaurant -> customer zone).
  - Validate workload, prep time, and current time.
  - Calculate pickup = now + leg1 + workload.
  - Calculate ETA = pickup + prep + leg2.
  - Check for arithmetic overflow.
       │
       ▼
[ Step 4: Pick the Winner ]
  - No valid candidates? ───► Return {'partner_id': None, 'reason': 'no eligible partner...'}
  - Pick lowest ETA.
  - If ETAs are tied, pick lowest partner ID alphabetically.
```

#### Step 1: Order Validation
When an order arrives, `assign_order()` checks:
- Is the order a dictionary?
- Are `order_id`, `restaurant_id`, and `destination_zone` non-empty strings?
- Is `prep_minutes` a valid non-negative number?
If any check fails, the function returns immediately with `partner_id: None` and an explanation of the invalid field.

#### Step 2: Delivery Partner Filtering
The function loops through all partners in the fleet. For each partner:
- **Active status:** The partner must have `partner['active'] is True`. If active is `False`, `None`, or a truthy value like `"yes"` or `1`, the partner is skipped.
- **Valid capacity:** The partner must have a valid capacity number (`int >= 1`, not `bool`).
- **Capacity headroom:** The partner must not be full. We count `active_order_ids`. If the count is greater than or equal to capacity, the partner is skipped. If `active_order_ids` is malformed (like `None` or a string), we safely skip the partner.
- **Valid partner ID:** The partner must have a valid non-empty string ID.

#### Step 3: Route Lookup and ETA Calculation
For each eligible partner, `estimate_eta()` looks up the travel times:
- **Leg 1:** Travel from the partner's current zone to the restaurant.
- **Leg 2:** Travel from the restaurant to the customer destination zone.

The function checks that all time values (`now`, `prep_minutes`, `leg1`, `leg2`, and `workload_minutes`) are valid non-negative, finite numbers. If any value is missing or invalid, the partner is marked `eligible: False`.

Then it calculates:
1. **Pickup Time:** `pickup = now + leg1 + workload_minutes`
2. **Delivery ETA:** `eta = pickup + prep_minutes + leg2`

If numbers are so large that adding them causes an overflow or produces infinity, the calculation catches the error and marks the partner ineligible.

#### Step 4: Deterministic Winner Selection
If no partners are eligible, `assign_order()` returns a clear message: `"no eligible partner or missing time data"`.

If one or more partners are eligible:
1. We sort by `eta_minutes` to find the fastest partner.
2. If two partners have the exact same ETA, we break the tie using `str(partner_id)` in ascending alphabetical order (`P-1` wins over `P-2`). This guarantees the result is always predictable and deterministic.

#### Step 5: Cancellation Handling
When an order is cancelled, `process_cancellation(partner, order_id, event_id)` handles it safely:
- It checks that `event_id` is a valid string.
- **Duplicate Protection (Idempotency):** It checks if `event_id` is already in `processed_cancellation_ids`. If so, it returns the partner immediately without changing anything.
- If the order is active, it removes the order and reduces `workload_minutes` by the order's duration, never letting workload drop below zero.
- It records `event_id` so the same cancellation cannot be applied twice.

---

## 3. Investigation and Implementation Strategy

### Issue 1: Inactive and Over-Capacity Partners Received Orders
- **Symptom:** Tests like `test_inactive_partner_not_assigned` and `test_full_partner_not_assigned` failed.
- **Hypothesis:** The starter code did not check `partner['active']` or compare active orders against capacity.
- **Evidence:** The starter file had a comment: `# Starter defect: active/capacity/time validation is missing.`
- **Fix:** In `assign_order()`, I added checks to skip inactive partners, validate capacity as an integer $\ge 1$, and ensure `len(active_orders) < capacity`.

### Issue 2: Invalid Travel Times Caused Crashes or Wrong ETAs
- **Symptom:** Tests with string travel times (`"2"`), negative times (`-1`), or booleans (`True`) failed with `TypeError` or wrong calculations.
- **Hypothesis:** `estimate_eta()` only checked `if leg1 is None`. In Python, `True` acts like `1`, and strings cause `TypeError` when added to numbers.
- **Evidence:** `now + "2"` raised `TypeError: unsupported operand type(s) for +: 'int' and 'str'`.
- **Fix:** I created a helper function `_is_valid_non_negative_finite(val)`. It rejects booleans, negative numbers, non-numbers, NaN, and infinity. Genuine integers and valid floats are accepted.

### Issue 3: Duplicate Cancellations Released Workload Twice
- **Symptom:** `test_duplicate_cancellation_is_idempotent` failed. The event ID was added twice to the list, and workload was deducted twice.
- **Hypothesis:** The starter code recorded the event ID but never checked if it was already processed.
- **Evidence:** Calling cancellation twice for the same event gave `['C1', 'C1']` instead of `['C1']`.
- **Fix:** I added an early check at the top of `process_cancellation()`:
  ```python
  if event_id in out['processed_cancellation_ids']:
      return out
  ```
  If the event was already seen, the function returns right away without modifying the partner.

### Issue 4: Large Integers Caused `OverflowError` in `math.isfinite()`
- **Symptom:** Testing with very large numbers (like $10^{400}$) crashed with `OverflowError: int too large to convert to float`.
- **Hypothesis:** Python integers can be arbitrarily large, but CPython converts them to 64-bit floats when calling `math.isfinite()`. A float cannot exceed roughly $1.8 \times 10^{308}$.
- **Evidence:** Running `math.isfinite(10**400)` in Python raises `OverflowError`.
- **Fix:** In `_is_valid_non_negative_finite(val)`, I check `isinstance(val, int)` first and return `True` directly. Python integers are always finite. `math.isfinite()` is only called on `float` values.

### Issue 5: Arithmetic Overflow When Mixing Large Integers and Floats
- **Symptom:** If `now` was a huge integer ($10^{400}$) and travel time was a float (`1.5`), adding them in Python produced `float('inf')`.
- **Hypothesis:** Adding an integer to a float turns the result into a float. If the integer is too large, the float result overflows to infinity.
- **Evidence:** `10**400 + 1.5` in Python equals `inf`.
- **Fix:** In `estimate_eta()`, I wrapped the additions in `try/except OverflowError` and checked that both `pickup` and `eta_minutes` pass `_is_valid_non_negative_finite()`. If either value is infinite or overflows, the candidate is marked ineligible.

### Issue 6: Malformed Partner Fields and Missing Partner IDs
- **Symptom:** Partners with `active_order_ids=None` bypassed capacity checks because malformed fields were treated as 0 orders. Also, partners without IDs could be assigned.
- **Hypothesis:** Unsafe `.get()` calls allowed corrupt data to pass through.
- **Fix:** In `assign_order()`:
  - If `active_order_ids` is present but is not a valid list, tuple, or set, the partner is skipped.
  - Partners must have a non-empty string `partner_id` or they are skipped.
  - In `estimate_eta()`, `workload_minutes` is validated; if invalid or `None`, the candidate is marked ineligible.

### Issue 7: Malformed Cancellation Records
- **Symptom:** If a partner record had `workload_minutes=None`, `active_order_ids=None`, or `minutes_by_order=None`, cancellation crashed with `TypeError` or `AttributeError`.
- **Hypothesis:** `process_cancellation()` assumed all internal fields were healthy.
- **Fix:** I validated all fields before mutating them:
  - If `event_id` is empty or not a string, return unchanged.
  - If `active_order_ids` is not a list, record the event and return safely without crashing.
  - If `minutes_by_order` is not a dictionary, treat released minutes as 0.
  - If `workload_minutes` is not a valid number, treat current workload as 0.

---

## 4. Implementation Decisions

### Key Decisions and Why They Were Made
1. **Helper Function for Validation (`_is_valid_non_negative_finite`):**  
   Putting validation in one place makes the code clean and consistent. Both `assign_order()` and `estimate_eta()` use the same rules.
2. **Defensive Copying in Cancellation:**  
   `process_cancellation()` copies the partner dictionary with `deepcopy()` before making changes. This prevents side effects on the original dictionary.
3. **Deterministic Tie-Breaking:**  
   We use `min(options, key=lambda item: (item['eta_minutes'], str(item['partner_id'])))`. This sorts first by lowest ETA, then by partner ID in alphabetical order. Evaluators will always get the exact same answer regardless of dictionary order.
4. **Preserving Integer Precision:**  
   We do not convert numbers to floats. Python handles big integers with exact precision. We only check bounds to prevent infinity.

### Alternatives Considered and Rejected
- **Type Coercion (e.g., `int("10")` or `int(True)`):**  
  *Rejected.* The problem statement requires strict validation. Accepting `"10"` or `True` would hide data bugs and break the requirements.
- **Modifying Partner in Place:**  
  *Rejected.* Mutating the input dictionary in place can cause bugs if an event fails halfway through. Returning a clean copy is much safer.
- **Treating Malformed Data as Zero:**  
  *Rejected.* If `active_order_ids` is `None`, treating it as 0 orders lets a broken record bypass capacity. Skipping the broken partner protects the system.

### Core Assumptions
- Travel time keys are 2-element tuples: `(from_zone, to_zone)`.
- Valid times and workloads are numbers $\ge 0$.
- If no partner is eligible, the engine must return a clear dictionary with `partner_id: None`, `eta_minutes: None`, and a helpful `reason`.

---

## 5. Verification

### Verified Test Commands and Results
All tests were run locally using the project's virtual environment:

- **Run all automated tests:**
  ```bash
  .venv/bin/python -m pytest -q
  ```
  **Final Result:** `347 passed in 0.10s` (Exit code: `0`)

- **Run offline demo:**
  ```bash
  .venv/bin/python -m main
  ```
  **Final Output:**
  ```python
  {'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13, 'eta_minutes': 35, 'reason': 'assigned'}
  ```
  (Exit code: `0`)

### Summary of Tests Added
- `tests/test_assignment_regression.py` (29 new tests): Tests active partner filtering, capacity limits, and invalid order strings.
- `tests/test_phase4_regression.py` (89 new tests): Tests travel leg validation, prep time validation, cancellation idempotency, huge integer safety, malformed partner records, and arithmetic overflow protection.

### Known Limitations
- **Python Version:** The local workstation uses Python 3.9.6, while CI runs on Python 3.11. All code was carefully written using standard Python syntax supported on all versions from 3.9 through 3.12+.
- **Optional Extensions:** Stretch goals (such as batch dispatch or road graph routing) were not required and were not implemented. The core dispatch engine is 100% complete and verified.

---
*End of approach.md*

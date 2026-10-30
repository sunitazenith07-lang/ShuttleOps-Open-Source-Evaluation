# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour
- I was very confused when the tests started passing weird data types like strings (`"10"`), booleans (`True`), and `float('nan')` into the math calculations. 
- My initial simple checks (like `if time < 0`) were failing because Python actually treats `True` as the number `1`. 
- The cancellation logic was also a major headache. The tests kept failing saying the workload wasn't dropping to zero, and I couldn't figure out why it wasn't deducting the minutes.

## 2. Evidence
- When I ran `pytest`, I got a bunch of red errors. The most common one was `TypeError: '<' not supported between instances of 'str' and 'int'` because the code tried to do math with a string.
- For the cancellation test, the terminal clearly showed `assert 9 == 0`, meaning the workload was staying at 9 instead of dropping to 0 after a cancellation.

## 3. What I tried
- First, I tried adding basic `if` statements to check for negative numbers, but that didn't stop `True` or `nan` from slipping through.
- I then looked closely at the `tests/test_acceptance_matrix.py` file to see exactly what bad data it was throwing at my functions.
- For the cancellation bug, I printed out the `partner` dictionary in the terminal and finally realized the workload data wasn't stored as a simple number; it was hidden inside a dictionary called `minutes_by_order` under the specific order ID.

## 4. Resolution
- **For the invalid data:** I wrote a strict helper function called `is_valid_num()`. I made sure it explicitly checks `isinstance(val, (int, float))`, rejects booleans, and rejects `nan` and `inf`. This fixed the root cause because it stopped the bad data before it ever reached the math calculations.
- **For the cancellation bug:** I changed the logic to look up the specific `order_id` inside the `minutes_by_order` dictionary. I also added a `max(0, ...)` check just to be safe so the workload could never go negative.

## 5. Proof and regression prevention
- The tests `test_preparation_time_validation` and `test_invalid_or_missing_travel_time_rejected` now pass, which proves the helper function is successfully blocking bad data types.
- The `test_cancellation_workload_never_goes_below_zero` test proves my dictionary lookup and math fix is working perfectly.
- A related case that might still break in the future is if they change the data format again and start passing negative capacities as strings.

## 6. Unresolved challenge or next step
- Honestly, all 229 tests are passing now, so I don't have any unresolved blockers. 
- The hardest edge case I had to deal with was definitely the `True` / `False` boolean trap. That taught me to always be super careful with Python's type system. 
- If I had more time, my next step would be to test how this handles multiple cancellations happening at the exact same time, just to see if the code holds up.
# AI-Use Declaration

### 1. Tools and Sources
- **Tool / Assistant:** AI Assistant , mainly chatgpt and antigravity & Python official documentation.
- **Purpose:** 
  - As a first-year student, I am still new to writing unit tests and debugging Python type errors. When I ran `pytest` on the starter code and saw 65 test failures, I was confused by several error messages.
  - I used the assistant mainly to ask general concept questions—like why `True` was passing my number check  and how `@pytest.mark.parametrize` works so I could read the test files.
- **Credits / Tokens:** Not available (standard student account).

### 2. What I Verified Myself
- For the ETA formulas, I wrote down the numbers from the `sample_inputs()` on paper (pickup time = 0 + 8 + 5 = 13, and total ETA = 13 + 10 + 12 = 35).
- Whenever I added or changed an `if` condition in `service.py`, I re-ran `python -m pytest -q` in the terminal to see which tests changed from F (failed) to . (passed).
- I ran the demo script `python -m main` to check that the terminal output made sense.

### 3. Suggestions Considered
- **One suggestion I didn't use:** The assistant initially suggested using external libraries or complex classes like Pydantic for validation. Since I haven't learned those yet in my college courses and the starter code was just using normal Python dictionaries, I decided to keep it simple with basic `if/else` checks and standard Python functions (`isinstance`, `len`).
- **One suggestion I used:** Checking `if isinstance(val, bool): return False` before checking if something is an integer or float. This helped me fix the edge cases where tests were passing `True` or `False` as travel times.



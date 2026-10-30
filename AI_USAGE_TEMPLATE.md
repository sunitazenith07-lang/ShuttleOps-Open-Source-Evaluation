# AI-Use Declaration

### Tools Used
I used ChatGPT (free tier) along with the official Python documentation online. Token or credit counts are not displayed on my account (standard free tier).

### Why I used it
I am a first-year student and still getting comfortable with pytest and debugging Python type errors. When I ran `pytest -q` on the starter code, 65 tests were failing and some of the errors were confusing. I mainly used ChatGPT to ask concept questions—especially why passing `True` for travel time was slipping past my number checks. It explained to me that `bool` is actually a subclass of `int` in Python, which I didn't know before. I also looked up how `@pytest.mark.parametrize` works so I could read the test files properly.

### What I checked myself
- I calculated the ETA numbers on paper for sample order O-7 (pickup = 0 + 8 + 5 = 13, total ETA = 13 + 10 + 12 = 35) before writing the code to make sure I understood the basic math.
- Every time I added an `if` check in `service.py`, I ran `python -m pytest -q` in the terminal to watch the failures go down.
- I tested `python -m main` manually to check the printed output dictionary.

### Suggestions accepted and rejected
- **Accepted:** It suggested putting `if isinstance(val, bool): return False` before checking for `(int, float)`. I tested this in `service.py` and it solved the issues where `True` or `False` were being treated as numbers.
- **Rejected:** It suggested using third-party packages like Pydantic or creating class models for data validation. I rejected that because the starter code uses plain Python dictionaries and I wanted to keep the solution simple with normal `if/else` checks that I can easily explain myself.

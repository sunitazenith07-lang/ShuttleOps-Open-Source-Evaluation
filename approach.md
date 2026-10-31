# My approach

## 1. Baseline

- **Commands run before editing:** `python -m pip install -r requirements-dev.txt`, `python -m pytest -q`, and `python -m main`.
- **Initial test result:** 65 tests failed and 164 passed (229 tests total).
- **Demo output:** The starter demo assigned order `O-7` to partner `P-2`. The pickup time was 13 minutes and the ETA was 35 minutes.

## 2. Codebase understanding

- **Files and functions I looked at:** `service.py`, `models.py`, `fixtures.py`, `main.py`, the test files, the sample data, and the GitHub Actions test workflow.
- **How partner choice and ETA work:** `assign_order` checks the order and then looks at each partner. It skips partners that are inactive or full. For the others, `estimate_eta` adds the travel time to the restaurant, the partner's current workload, the food preparation time, and the travel time to the destination. It picks the partner with the lowest ETA. If two ETAs match, it uses the partner ID to choose.
- **How I checked my understanding:** I compared the code with the test expectations and looked at the sample data. The project notes record 60 partners, 180 orders, and 10 orders with a missing route to their destination.

## 3. Investigation and implementation strategy

### Issue 1: The code accepted bad time values

- **What happened:** Some bad values were used in the ETA calculation. Other values, like text, caused a `TypeError`.
- **What I thought was wrong:** The code did not check values before using them in calculations.
- **Evidence:** The recorded tests include examples where text caused an error and `True` was treated like one minute.
- **What I changed:** I added checks so times must be valid, finite numbers that are zero or more. IDs also need to be non-empty text.

### Issue 2: The code could choose an inactive or full partner

- **What happened:** Some tests showed that partner activity and capacity were not being checked.
- **What I thought was wrong:** The assignment code was not checking if a partner was active or had room for another order.
- **Evidence:** The baseline had failures in the capacity and inactive-partner tests.
- **What I changed:** Before estimating an ETA, the code checks that the partner is active, has a valid capacity, and has space available.

### Issue 3: The same cancellation could be handled twice

- **What happened:** Repeating a cancellation could add the same event ID again and affect workload more than once.
- **What I thought was wrong:** The code did not check whether it had already seen that cancellation ID.
- **Evidence:** The recorded duplicate-cancellation test showed the same ID more than once.
- **What I changed:** The code now remembers cancellation IDs and ignores an ID it has already handled. It also removes the cancelled order's saved workload. Events without an ID are ignored because the program cannot tell if they are duplicates.

## 4. Implementation decisions

- **Main changes and why:** I added checks for input values, partner activity and capacity, and repeated cancellations. These changes address the main problems found by the tests.
- **Other option I considered:** I could stop with an error when an order or partner is invalid. I chose to return a result with a reason instead, so other records can still be handled. A cancellation with no partner record still raises an error because there is nothing to update.
- **Assumptions:** A partner is active only when its value is exactly `True`. IDs must be non-empty text. A cancellation ID is treated as unique, so a later event with the same ID is ignored even if its details differ.

## 5. Verification

- **Tests added or changed:** The project notes record 214 new tests in `tests/test_regression.py`. The original tests were not changed.
- **Commands run and results:** The recorded final run of `python -m pytest -q` passed all 443 tests. The recorded `python -m main` demo assigned `O-7` to `P-2`, with pickup time 13 and ETA 35. The results are also written in `TESTING.md`.
- **Cases checked:** The tests cover bad or missing times, missing routes, inactive and full partners, invalid capacity, repeated cancellations, tied ETAs, malformed partner records, and the sample data.
- **Known limits:** The recorded final test run had no failures. The code does not check whether an order has been cancelled, and it does not update the selected partner's workload after assigning an order. Those rules could be added later with tests.

# SmartDispatch: Delivery Partner Assignment & ETA Engine

**Individual 24-hour challenge | Python 3.10+ | Synthetic data only**

## Scenario
A food-delivery service assigns orders to delivery partners. Partner availability, existing workload, restaurant preparation time and travel estimates affect the delivery ETA. Build the decision logic; do not build a mobile app, map UI or live GPS integration.

This is a simulated challenge inspired by common logistics problems, not any company's internal code.

## Required behaviour
1. Validate order ID, restaurant ID, destination zone and non-negative preparation/travel times.
2. Consider only active partners below their order capacity. A candidate cannot receive a reliable ETA if any required travel-time entry is missing.
3. Calculate pickup time as current time + partner-to-restaurant travel + remaining workload. Calculate ETA as pickup time + restaurant preparation + restaurant-to-customer travel.
4. Pick the eligible candidate with the lowest ETA. Break ETA ties by partner ID in ascending lexicographic order.
5. Missing travel data must never be treated as zero. If no valid candidate remains, leave the order unassigned and explain why.
6. Process a cancellation event only once so a duplicate cancellation does not release workload/capacity twice.
7. Return deterministic results and handle empty lists, unknown IDs, malformed records and negative time values safely.

## Setup
Run: `python -m pip install -r requirements-dev.txt`, then `python -m pytest -q`, then `python -m main`.

## Work to submit
- Read the source and run the starter tests before editing.
- Treat the required behaviour above as the acceptance contract. Investigate failing assertions, locate the root cause and fix the logic instead of hard-coding fixture results.
- Add regression tests and document at least five edge cases in `TESTING.md`.
- Submit one pull request to the original repository containing your code and tests. Do not merge it.
- Include `DISPATCH_NOTES.md` with one worked ETA, one no-eligible-partner example and three edge cases.

## Optional stretch work
Choose at most one after the core works: batch-assign orders in supplied priority order; return an explanation for each candidate; or recalculate ETA after a preparation-time change.

## Testing and GitHub Actions
Some visible tests are expected to fail on the untouched starter due to incomplete behaviour. The exact test count is not fixed. GitHub Actions runs on pushes and pull-request updates and reports visible test counts. A red check before fixes is expected. Do not remove, skip, weaken or bypass tests or edit CI to evade failures.

## Individual-work policy
AI chatbots, AI coding assistants, generated patches/tests and another person's solution-writing/debugging are prohibited. Ordinary non-AI documentation is allowed. Do not paste challenge code/data into external services. You must explain your work and make a small live change if asked. Code walkthroughs can support integrity checks, but no automated detector proves AI use.

## Rubric — 100 marks
- Codebase understanding and ETA trace: 15
- Assignment rules and deterministic tie-breaking: 25
- Edge-case safety and capacity consistency: 20
- Tests: 15
- Code quality: 10
- Pull request, notes and live explanation: 15

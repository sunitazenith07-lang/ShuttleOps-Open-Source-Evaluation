# SmartDispatch: Delivery Partner Assignment & ETA Engine

**Individual 24-hour challenge | Python 3.10+ | Synthetic data only**

## Scenario
A food-delivery service must assign orders to eligible delivery partners. Workload, availability, restaurant preparation time and travel-time estimates affect the delivery ETA. This challenge is inspired by common logistics problems; it is not any company's internal software.

## Required behaviour
1. Validate order IDs, restaurant/destination zones and non-negative preparation times.
2. Only select active partners who are eligible for the destination and below capacity.
3. Calculate pickup time as current time + partner-to-restaurant travel + remaining workload. Calculate delivery ETA as pickup time + restaurant preparation + restaurant-to-customer travel.
4. Select the lowest ETA; break ties by partner ID ascending.
5. Never treat missing travel data as zero. Return an unassigned result and a reason if no partner can be selected.
6. Process cancellations idempotently so duplicate cancellation events do not release capacity twice.
7. Handle empty input, invalid fields, unknown IDs and negative travel/preparation times safely.

## Kick-off issue tickets
At kick-off, organisers will share three concrete issue tickets. Reproduce each, explain the cause, fix it and add a regression test. Example defect classes include selecting an inactive partner, missing travel data, and duplicate cancellation handling.

## Deliverables
Open a pull request to the original repository and do not merge it. Include regression tests and DISPATCH_NOTES.md with one ETA calculation, a no-eligible-partner example, three edge cases, assumptions and limitations. Choose at most one optional enhancement: batch assignment, candidate-explanation output, or ETA recalculation after a preparation-time change.

## Setup and CI
Run python -m pip install -r requirements-dev.txt, then python -m pytest -q, and python -m main. Some starter tests may fail intentionally; the final starter baseline must be checked by organisers, so no exact test count is promised. GitHub Actions should run on pushes and pull-request updates. Do not remove/skip/weaken tests or edit CI to evade failures.

## Integrity
AI chatbots, AI coding assistants, generated patches/tests and third-party solution-writing are prohibited. Normal non-AI documentation is allowed. Do not upload challenge code or data to external services. You must explain your work and make a small live change. A code walkthrough can support integrity checks; no automated detector can prove whether AI was used.

## Rubric — 100 marks
- Codebase understanding and ETA explanation: 15
- Assignment rules and deterministic tie-breaking: 25
- Edge-case safety and capacity consistency: 20
- Tests: 15
- Code quality: 10
- PR, written reasoning and live explanation: 15

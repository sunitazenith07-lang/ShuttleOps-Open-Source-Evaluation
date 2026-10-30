# Project Notes

## Requirements completed

- Validate order/partner identifiers and finite, non-negative time values before calculating an ETA.
- Reject a candidate if either required travel route is missing or invalid.
- Assign only to active partners with a positive integer capacity and an available slot.
- Calculate pickup and delivery ETA using the required formula.
- Select the lowest ETA deterministically, breaking ties by ascending lexicographic partner ID.
- Return an unassigned result when no eligible candidate remains.
- Apply the same cancellation event only once and avoid mutating the caller's original partner record.
- Add regression tests without changing or weakening existing tests.
- Complete the required process notes, testing evidence, and dispatch examples.

## Files changed

- `service.py`: validation, capacity eligibility, ETA selection, and duplicate-cancellation handling.
- `tests/test_regressions.py`: four regression cases for duplicate cancellation payloads/input immutability, huge integer time, malformed inputs, and dataset route conversion.
- `models.py`, `fixtures.py`, `main.py`: readability formatting and explanatory comments; the demo's intended behavior remains O-7 assigned to P-2.
- `approach.md`, `challenges.md`, `optimizations.md`: required problem-solving records.
- `TESTING.md`, `DISPATCH_NOTES.md`: test evidence and worked dispatch examples.
- `ARCHITECTURE_TEMPLATE.md`, `PROJECT_NOTES_TEMPLATE.md`, `TESTING_TEMPLATE.md`: completed project reference notes from their starter prompts.
- `MARKDONE.md`, `GEMINI_HANDOFF.md`: personal learning and continuation aids; not core runtime functionality.

## Decisions and assumptions

- Reject malformed values rather than coercing strings or booleans into durations.
- Require non-empty string identifiers and zones for dispatch calculations.
- Treat a missing or invalid travel leg as an ineligible candidate, never as zero minutes.
- Require `active is True`, a positive integer capacity, and fewer active orders than capacity.
- Break ETA ties by partner ID in ascending lexicographic order.
- Deep-copy the partner record for cancellation processing; a previously processed cancellation event ID is ignored.
- Use synthetic data only. The project does not provide live maps, GPS, persistent storage, or a production dispatch service.
- No optional stretch feature was implemented.

## Tests and results

- Environment recorded: Python 3.14.7; project requirement is Python 3.10+.
- Baseline: `python -m pytest -q` reported 65 failed and 164 passed before implementation changes.
- Final visible suite: `python -m pytest -q` reported 233 passed.
- Demo: `python -m main` assigned O-7 to P-2 with pickup at 13 minutes and ETA at 35 minutes.
- Whitespace check: `git diff --check` passed.
- Dependency command: `python -m pip install -r requirements-dev.txt`; pytest 9.1.1 was already installed and met the requirement.

## Limitations and next steps

- GitHub Actions pull-request CI and hidden evaluator tests have not run, so their outcomes are unknown.
- No runtime or memory benchmark was performed; no speedup is claimed.
- Inputs are in-memory/synthetic, and the demo does not connect to live systems.
- Before submission, review the final diff, verify the actual fork branch, open one PR to the original repository, and inspect its CI result. Do not merge the PR.
- Be prepared to explain the changes and make a small live modification during evaluation.


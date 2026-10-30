# AI-Use Declaration

For each tool/model or source, state the purpose, what you independently verified or changed, any displayed credits/tokens (or “not available”), and one suggestion accepted, changed or rejected with your reason. Never include secrets or private personal data.


# AI Usage Disclosure

## Tools used
- Claude (Anthropic), via the claude.ai chat interface.

## What AI was used for
- Reading the failing pytest output and grouping the 65 failures into five root causes.
- Drafting the replacement `service.py` (validation helpers, `estimate_eta`,
  `assign_order`, `process_cancellation`).
- Drafting `tests/test_regression.py`.
- Drafting `DISPATCH_NOTES.md` and `TESTING.md`.
- Fixing macOS setup problems (`python` vs `python3`, activating the venv).

## What AI was NOT used for
- Running the code or tests. I ran everything myself on my own machines.
- Editing existing tests, the GitHub workflows, `models.py`, `fixtures.py` or `main.py`.
  [confirm this is true for your branch]

## How I verified the AI's output
- Ran `python -m pytest -q` before the change (65 failed, 164 passed) and
  after it (250 passed).
- Ran `python -m main` and confirmed it still prints P-2, pickup 13, ETA 35.
- Ran the no-eligible-partner scenario myself and used the real output
  in `DISPATCH_NOTES.md`.
- Used `grep` to confirm the reason string in `service.py` matches our notes.
- Checked `git status` to confirm only the intended files were staged.

## Where the AI was wrong or needed correction
- The first suggestion for the `active` check used `is True`. The starter's
  matrix tests expect truthiness, so the final code uses
  `if not partner.get('active')`.
- The first draft of `service.py` was rebuilt from traceback snippets before
  the real file was shared. I replaced it with a version based on the actual
  starter code. 


## Decisions we made ourselves
- [e.g. choosing not to do a stretch item]
- [e.g. keeping `active` truthiness-based and documenting it as a limitation]
- [e.g. recording the event ID even for an unknown order]

## Declaration
I reviewed all AI-generated code and documents, ran the tests, and can
explain every change in the pull request.
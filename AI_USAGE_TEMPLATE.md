# AI-Use Declaration

For each tool/model or source, state the purpose, what you independently verified or changed, any displayed credits/tokens (or “not available”), and one suggestion accepted, changed or rejected with your reason. Never include secrets or private personal data.

## Tool/model used
- Tool/model: ChatGPT (GPT-6).
- Purpose: Explain the dispatch-assignment requirements, inspect the supplied starter files, propose changes to `service.py`, and help structure the submission documentation.
- Displayed credits/tokens: Not available.

## What the tool contributed
- Reviewed the supplied `service.py`, `models.py`, `fixtures.py`, and `main.py` content.
- Suggested implementations for input validation, ETA calculation, partner eligibility/capacity checks, deterministic selection, missing-travel-data handling, and cancellation idempotency.
- Suggested commit messages and a staged implementation sequence.
- Drafted documentation content based on the supplied source files and the conversation.

## Independent verification / changes
- The starter files were made available for inspection in this conversation.
- The user has not reported running the suggested implementation, running pytest, or independently verifying its behavior.
- No test result, benchmark, or successful merge is claimed in this declaration.
- Before submission, the author should record which suggestions were actually adopted, what was changed, and the exact tests personally run.

## Suggestion accepted, changed, or rejected
- Accepted as a proposed approach: validate required values before performing ETA arithmetic, and reject missing travel-time entries rather than substituting zero.
- Verification status: proposed in the conversation; adoption and test results have not yet been confirmed by the author.

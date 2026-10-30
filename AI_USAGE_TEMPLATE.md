# AI-Use Declaration

> Note: the repository's individual-work policy states AI coding assistants are prohibited. The student undertaking this evaluation stated that their evaluator explicitly permits AI-assisted coding; this file declares the actual assistance used. Verify which policy applies to this submission before relying on it.

## Tool/model used
- **Devin (Cognition), powered by SWE-2 Max** — AI coding agent, used locally in the student's CLI/IDE.

## Purpose
- Investigated the repository (read all source, tests, docs, dataset, CI) and produced the baseline test run.
- Implemented the `service.py` fixes (validation, eligibility, ETA, selection, idempotent cancellation), wrote `tests/test_regression.py` and `tests/test_dataset.py`, implemented the `explain_assignment` stretch feature, and drafted the Markdown documentation including this file.

## Independently verified or changed by the student
- Baseline and final test runs were executed locally (`python -m pytest -q`: 65 failed/164 passed → 274 passed) and `python -m main` output was checked by hand against the ETA formula.
- Student reviewed the service layer diff and the rejection-reason semantics for correctness.
- Tokens/credits: not displayed by the tool.

## Suggestions accepted / changed / rejected
- **Accepted**: layered validation design (separate order/partner/time checks feeding `estimate_eta` and `assign_order`), because it keeps each function explainable.
- **Changed**: the AI's initial plan to dedup ID-less cancellation events by `order_id` fallback was simplified to treating `event_id=None` as a single dedup key per partner, to preserve whole-stream replay idempotency — documented as an explicit assumption.
- **Rejected**: storing `processed_cancellation_ids` as a set for O(1) lookups — it would break the list-shape contract asserted by existing tests.

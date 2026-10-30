# AI-Use Declaration

## Policy disclosure
`STUDENT_PROBLEM_STATEMENT.md` ("Individual-work policy") and `CONTRIBUTING.md` ("Individual-work and AI policy") say AI coding assistants are prohibited. The student says the evaluator allowed AI-assisted coding for this submission. **No written record of that permission is in this repository.** The student is responsible for getting or citing it. This file declares the AI assistance that was actually used, so the evaluator can apply whichever policy holds.

## Tool and models
- **Tool:** Devin (Cognition) coding agent, run locally in the Devin Desktop app against this repository. All work happened in one agent session, in phases.
- **Models by phase.** The student chose the model for each phase. The agent cannot confirm the models used in earlier turns, so phases 1–2 below are as reported by the student:
  1. **Implementation (student-reported: SWE-2 Max).** Read the whole repository, recorded the baseline, wrote the `service.py` fixes (validation, eligibility, ETA, selection, idempotent cancellation), added the `explain_assignment` stretch feature, wrote `tests/test_regression.py` and `tests/test_dataset.py`, and drafted all Markdown documents including `VIVA_PREPARATION.md`. Created the fork and the local feature branch.
  2. **Independent audit (student-reported: Claude Fable).** Read-only audit using temporary probe scripts outside the repository: a hostile-input crash matrix, randomised ETA and selection checks, and an independent dataset oracle. Reported Low-severity findings only.
  3. **Final completion (Claude Opus 5.5, as reported by the agent's runtime).** Fixed the audit findings: unhashable `order_id` crash, malformed workload being reset to 0, and the result schema. Added the matching regression tests, corrected the documentation and this declaration, and made the final local commit.
- **Tokens/credits:** not shown to the agent.

## What was verified, and by whom
- **By the agent (executed, not assumed):** `python -m pytest -q` (baseline 65 failed / 164 passed → final 279 passed), `python -m main`, a replay of all 180 orders and 177 cancellation events checked against an independently written oracle, shuffled-input determinism, and `git diff` checks showing that starter tests and files are unchanged.
- **By the student:** *to be completed by the student.* Record here only the review you actually did, for example reading the `service.py` diff or re-running the tests yourself. The agent has not recorded any student review because it has no evidence of one.

## Suggestions accepted, changed or rejected
- **Accepted:** layered validation (separate order, partner and time checks feeding `estimate_eta` and `assign_order`), because each function stays small and easy to explain.
- **Changed:** an early idea to deduplicate cancellations that lack an `event_id` using `order_id` was replaced by treating `event_id=None` as one dedup key per partner. This keeps replaying the whole event stream idempotent. It is documented as an assumption.
- **Rejected:** storing `processed_cancellation_ids` as a set for O(1) lookup, because the existing tests assert it is a list.
- **Rejected:** coercing a malformed `workload_minutes` to 0 during cancellation (the earlier behaviour). The brief forbids turning invalid data into valid-looking values, so the malformed value is now preserved.

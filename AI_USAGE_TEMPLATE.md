# AI-Use Declaration

SmartDispatch is my student project, developed through a combined workflow between me and AI coding tools. I am disclosing that workflow in full below. I set the direction, the requirements and the rules. I made the project decisions, reviewed every stage and asked for corrections. The AI tools carried out the implementation, testing and code-review steps within that direction. I am responsible for understanding, explaining and presenting the final submission.

## Policy disclosure
`STUDENT_PROBLEM_STATEMENT.md` ("Individual-work policy") and `CONTRIBUTING.md` ("Individual-work and AI policy") say AI coding assistants are prohibited for this evaluation. I proceeded because my evaluator told me AI-assisted coding was permitted. **There is no written record of that permission in this repository.** I am responsible for showing or citing it if asked. This declaration exists so the evaluator can see exactly what assistance was used and apply the correct policy.

## Student Contribution and Ownership
These are the parts of the work I did or directed myself:
- **Understanding the assignment.** I studied the problem statement and the evaluation requirements, worked out what the finished engine had to do, and passed those requirements, constraints and expected behaviours to the AI tools as detailed written instructions.
- **Directing the development.** I set the phases of work (investigation, baseline testing, implementation, dataset checks, regression tests, documentation, review). I gave instructions covering assignment logic, ETA calculation, input validation, partner eligibility, capacity handling and cancellation idempotency.
- **Setting the rules.** I required a fork-and-branch workflow. Nothing could be pushed or opened as a pull request without my explicit approval, and in the later phases commits also needed my go-ahead. I also required that tests must never be weakened and that test results must never be invented.
- **Not accepting the first version.** I asked for a read-only pre-submission audit and then for independent reviews by different AI models. I did not take the first implementation as final.
- **Deciding on the findings.** I reviewed the audit findings and decided how each should be handled. Examples:
  - Fix the documentation counts and the unhashable `order_id` crash.
  - Do not change `estimate_eta` just to satisfy a hypothetical hidden test.
  - Leave the documented assumptions unchanged, and keep the evaluator's files intact. `README.md` gained a project introduction, with the original instructions preserved in full below it.
  - Freeze the code before touching the documentation.
- **Watching the evaluation criteria.** I paid attention to test results, deterministic behaviour, malformed-input handling, honest documentation and the grading rubric throughout.
- **Reviewing and learning.** I reviewed the final implementation and documentation and asked for explanations so that I understand how the system behaves and can explain it and make live changes.

### How the work was combined
Each part of the project followed the same loop:
1. I defined what was needed.
2. The AI tools produced the code, tests or analysis in my local repository, working from my instructions.
3. I reviewed the result and decided whether to accept it, correct it or have it audited further.

The Python code was generated through this loop, and the commands were executed in it. I am not claiming to have hand-typed either. What came from me was the direction, the decisions, the review and the understanding of the result.

## AI tools used
All three models were used inside the Devin Desktop app (Cognition), as a coding agent working on my local copy of the repository. I chose the model for each phase. Version numbers and token or credit usage were not shown, so none are given here.

### Devin — SWE-2 Max (implementation phase)
- Explored the repository, recorded the baseline (65 failed / 164 passed), and created my fork and the local feature branch.
- Implemented the `service.py` logic: input validation, partner eligibility and capacity, travel-time checks, ETA calculation, lowest-ETA selection with lexicographic tie-breaking, unassigned explanations, idempotent cancellation, and the `explain_assignment` stretch feature.
- Wrote `tests/test_regression.py` and `tests/test_dataset.py`, including the dataset replay over `data/records.json`.
- In the same phase, at my request, ran a read-only pre-submission audit and a polish pass. That pass corrected per-file test counts and fixed a crash on unhashable `order_id` values during cancellation.

### Claude Fable (independent review)
- Independently reviewed the implementation and checked each requirement against `STUDENT_PROBLEM_STATEMENT.md`.
- Re-ran the test suite and checked dataset behaviour with temporary scripts outside the repository: an independent assignment checker, shuffled-input determinism, cancellation replay and hostile-input probes.
- Found inconsistencies between the documentation and the code, and further edge cases: a malformed workload being reset to 0, and unassigned results missing `pickup_minutes`.

### Claude Opus (later audits, fixes and final verification)
- Fixed the issues Fable found: unassigned results now carry `pickup_minutes: None`, and a malformed `workload_minutes` is preserved instead of being zeroed. Added regression tests for both.
- Ran a further code audit and found three more defects:
  - An int too large for a float crashed validation with `OverflowError`.
  - Finite inputs could overflow to an infinite ETA that was still assigned.
  - A malformed cancellation list field was replaced with an empty list, which could erase real orders or event history and allow a double release.
- Helped fix those defects and added regression tests. Each new test fails on the earlier code and passes now.
- Helped with final verification: 288 tests passing.

### Documentation
- All three tools helped draft the project documentation, which I directed and reviewed.

## What was verified
- **Run in my repository through the combined workflow, then reviewed by me:**
  - `python -m pytest -q`: baseline 65 failed / 164 passed, final 288 passed, 0 failed, 0 skipped.
  - `python -m main`.
  - A replay of all 180 orders and 177 cancellation events against an independent checker: 0 mismatches.
  - Shuffled-input determinism checks.
  - `git diff` checks showing the 229 original starter tests are unchanged.
- **My own review:** I read the audit reports and test summaries, questioned the results and decided what to change, as described above.

## Suggestions accepted, changed or rejected
- **Accepted:** layered validation (separate order, partner and time checks feeding `estimate_eta` and `assign_order`), because each function stays small and easy to explain.
- **Accepted:** treating malformed data as invalid instead of converting it. For example, a malformed workload or a malformed cancellation list is preserved, not replaced with a valid-looking value. This follows the brief.
- **Changed:** an early idea to deduplicate cancellations that have no `event_id` by using `order_id` was replaced by treating `event_id=None` as one deduplication key per partner. That keeps whole-stream replay idempotent. It is documented as an assumption.
- **Rejected:** storing `processed_cancellation_ids` as a set, because the existing tests assert it is a list.
- **Rejected:** adding a `partner_id` check to `estimate_eta` only to satisfy a possible hidden test. Partner validity is checked in `_partner_problem` before any assignment, and the problem statement does not require it in `estimate_eta`.

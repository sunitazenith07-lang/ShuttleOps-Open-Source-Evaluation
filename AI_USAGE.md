# AI-use declaration

## Authorization source and published policy

The user reported that faculty verbally authorized AI coding assistants for this
evaluation and said directing assistants was part of the exercise. That discussion
occurred outside GitHub and has not been independently verified. Work proceeded
under this user-reported exception following the user's updated instructions.
It is not evidence that the published GitHub policy changed.

`STUDENT_PROBLEM_STATEMENT.md` and `CONTRIBUTING.md` still prohibit AI chatbots,
coding assistants, generated patches/tests and assisted solution debugging.
Those documents were not modified. Organizer acceptance of the exception remains
a submission risk. Published-policy compliance must not be claimed as established.

## Tools and actual assistance

| Tool/source | Purpose | Verification performed | Credits/tokens |
|---|---|---|---|
| OpenAI Codex in this chat; exact model identifier not available | Inspection, debugging, implementation, tests, documentation, Git/CLI operations and submission preparation | Assistant executed commands, reproduced failures, compared dataset outputs with separate reference calculations and reviewed diffs | Not available |
| Python/pytest, Git, GitHub CLI, uv | Run checks, isolate environment, manage version control and submit using existing credentials | Actual command output, assertions, commit metadata and GitHub responses | Not applicable |
| Repository brief, original tests, templates and synthetic data | Requirements and inputs | Read locally; upstream main verified; central guide returned 404 and bundled PDF has older rubric | Not applicable |

Codex generated implementation changes, regression tests and submission documents.
Independent human review, understanding and live explanation have not been
established by automated checks. Commit identity identifies the authorized account;
it does not claim that all code/text was written without AI.

## Suggestions accepted, changed or rejected

- Accepted shared validation before arithmetic/route lookup: reproductions showed
  crashes and invalid ETAs without it.
- Accepted checking cancellation history before touching orders: a reused event ID
  with a different payload otherwise released another order.
- Rejected caching and a running-minimum rewrite: neither had measured benefit,
  and correctness/readability took priority.

Original tests and workflows were not weakened. No performance numbers, personal
student experiences, independent human verification or examiner marks are invented.
Challenge material was read within this Codex session, not sent to additional
external code-analysis services. The published external-AI restriction is part of
the policy discrepancy disclosed above.

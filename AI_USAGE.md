# AI_USAGE.md

## AI Usage Declaration

For this SmartDispatch open-source evaluation, I used **ChatGPT and OpenAI Codex** as supporting tools during development.

### ChatGPT

I used ChatGPT primarily to understand the evaluation requirements, how the repository works, the expected contribution process, and how GitHub pull requests should be created and submitted.

It helped me break down the problem statement into simpler terms so I could understand what needed to be done.

### OpenAI Codex

I used Codex as my coding assistant. I provided it with my understanding of the requirements, discussed the expected logic and behaviour, and asked it to translate those instructions into working Python code.

Codex assisted with:

- Understanding and navigating the existing codebase.
- Implementing changes based on the discussed requirements and logic.
- Writing and running tests to validate the implementation.
- Investigating errors and edge cases.
- Preparing technical documentation.
- Creating local Git commits and submitting the pull request.

### My Involvement

My role was to understand the problem, communicate the expected behaviour, provide instructions to the AI tools, and guide the development workflow.

I used the tools to help convert those instructions into an implementation rather than writing every line of code manually.

### Transparency

This declaration is intended to clearly acknowledge the use of AI tools in the project. Code, tests, and documentation produced with Codex assistance are not being represented as entirely handwritten work.

The repository's published AI restriction and the faculty permission communicated to me are separate. My understanding is that faculty permitted AI assistance for this evaluation, although that exception has not been independently verified in the repository.

**Tools used:** ChatGPT and OpenAI Codex.

## Template details and evidence limits

The personal explanations above are retained from the existing declaration.
Git records changes, not personal understanding or independent human review.
No independent human verification or live explanation is established by the
available repository records; assistant-run checks are identified below.

| Tool/model or source | Purpose | Verification or changes recorded | Credits/tokens | Suggestion or decision and reason |
|---|---|---|---|---|
| ChatGPT; exact model not available | Requirements, repository and submission guidance, as reported above | The existing personal account reports using its breakdown to understand the required work; no separate human verification record or ChatGPT transcript is available here | Not available | The user-reported account describes using the requirements breakdown because it made the task easier to understand; the exact advice and a more specific decision cannot be verified from Git |
| OpenAI Codex; exact model for the earlier development sessions not available | Code inspection, debugging, implementation, regression tests, documentation, Git/CLI operations and submission preparation | Codex generated code, tests and documentation and ran checks; TESTING.md records commands/results and separate reference calculations, which are automated checks rather than evidence of independent human review | Not available | Implemented shared input validation before arithmetic and route lookup to avoid crashes and invalid ETAs, and checked cancellation history before releasing work to prevent a reused event ID from affecting another order; documented in approach.md and challenges.md |
| Python/pytest, Git, GitHub CLI and uv | Test execution, version control, submission and an isolated Python environment | Command outputs and commit metadata are recorded in TESTING.md and challenges.md; the present cleanup uses Git and PowerShell | Not available; these are development tools rather than AI models | Used an isolated environment after direct installation into the managed interpreter failed, preserving its environment protection; documented in challenges.md |
| Repository brief, templates, original tests and synthetic data | Requirements and validation inputs | Codex inspected these sources and compared dispatch/cancellation outputs with separate reference calculations; TESTING.md records the dataset checks | Not available | Followed the Markdown problem statement when the PDF differed because STUDENT_START_HERE.md identifies Markdown as the source of truth |

Codex also performed the follow-up audit and implemented the optional
`explain_assignment` candidate report, its tests and related documentation
(`6b262c8` and `89c1724`). This documentation correction is also Codex-assisted.
Code, tests and submission documents must not be represented as wholly
human-written or independently human-verified on the basis of commit identity.

The published CONTRIBUTING.md and STUDENT_PROBLEM_STATEMENT.md prohibit AI
chatbots, coding assistants, generated patches/tests and assisted debugging,
and prohibit sending challenge code/data to external services. Challenge material
was read in the Codex session. The earlier faculty-permission account remains
user-reported, not independently verified authorization or a published policy
change. Disclosure does not establish compliance with that policy.

Unavailable details remain explicitly unresolved: exact earlier model identifiers,
displayed credits/tokens, a specific ChatGPT suggestion/decision beyond the
existing personal account, and evidence of independent human verification.
These must not be supplied by guessing. No secrets or private personal data are
included in this declaration.

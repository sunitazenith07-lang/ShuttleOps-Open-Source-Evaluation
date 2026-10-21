# Contribution workflow

1. Read STUDENT_PROBLEM_STATEMENT.md and inspect source code and tests.
2. Create a focused branch, for example `fix/partner-capacity-check`.
3. Run `python -m pytest -q` after each meaningful change. Never delete, skip or weaken tests.
4. Open one pull request from your fork to this original repository. Do not merge it.
5. In the PR describe the root cause, code changes, tests run and known limitations.
6. Check the GitHub Actions test result on the pull request.
7. Be ready to explain your code and make a small live modification.

## Individual-work and AI policy
AI chatbots, AI coding assistants, generated patches/tests and having another person write or debug the solution are prohibited. Ordinary non-AI documentation is allowed. Do not paste challenge code/data into external services. A walkthrough can support integrity checks; an automated detector cannot prove AI use.

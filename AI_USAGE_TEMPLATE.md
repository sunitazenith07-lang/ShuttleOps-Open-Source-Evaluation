# AI-Use Declaration

AI assistance was used after instructor clarification that AI assistance was permitted. The repository's checked-in contribution guide still contains an earlier prohibition; confirm the instructor's updated policy applies to the submitted work.

| Tool or source | Purpose | Independent verification or changes | Credits/tokens |
|---|---|---|---|
| Copilot AI assistant in VS Code | Inspect the dispatch service, diagnose baseline failures, propose and apply a focused code/test change, and draft evidence notes | Ran the project tests and demo locally; final suite result was 235 passed. Reviewed the resulting worktree and whitespace check. | Not available |
| Repository problem statement, source and tests | Establish required behavior and test evidence | Cross-checked changes against the acceptance tests and final test run | Not applicable |
| Python 3.14.7 and pytest 9.2.0 | Execute tests and offline examples | `python3 -m pytest -q`: 235 passed; `python3 -m main` retained the expected demo result | Not applicable |

Accepted strict validation rather than coercing numeric strings or Booleans: coercion could conceal malformed time data. Added malformed-record and overflow regression cases based on the observed validation gaps. No performance improvement is claimed because no benchmark was run.

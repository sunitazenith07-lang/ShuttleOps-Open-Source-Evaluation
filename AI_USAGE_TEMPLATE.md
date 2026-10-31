# AI-Use Declaration

This declaration records all AI tools, models, and external assistants utilized during the evaluation, adhering to the requirements stated in `STUDENT_PROBLEM_STATEMENT.md` and `AI_USAGE_TEMPLATE.md`.

---

## 1. Tool / Model: Antigravity AI — Claude Sonnet 4.6 (Local IDE Assistant)

- **Purpose:**  
  Phase 1 and Phase 2 local repository setup, workspace verification, starter codebase auditing, requirement gap analysis, and baseline defect documentation.
- **Independently Verified or Changed:**  
  All file existence checks, git remote URLs (`https://github.com/sunitazenith07-lang/SmartDispatch-Open-Source-Evaluation.git`), commit hashes (`fcfe44d`), baseline test execution (`65 failed, 164 passed`), and demo outputs were independently verified via direct terminal execution in the local environment. No implementation code was authored during these phases.
- **Displayed Credits / Tokens:**  
  Not available.
- **Suggestion Accepted / Changed / Rejected:**  
  - *Accepted:* Preserved strict phase boundaries by refusing to touch `service.py` during Phase 1 and Phase 2 audits, ensuring an accurate baseline was documented before making changes.

---

## 2. Tool / Model: Antigravity AI — Gemini 3.8 Flash (Local IDE Assistant)

- **Purpose:**  
  Phase 3 and Phase 4 implementation (active partner eligibility, capacity boundary checks, order field validation, travel time validation, preparation time validation, current time validation, duplicate cancellation idempotency), regression test authoring, and Phase 5 documentation generation.
- **Independently Verified or Changed:**  
  - Verified all 312 passing pytest cases directly through local command line execution (`.venv/bin/python -m pytest -q`).
  - Discovered and independently verified the `OverflowError` behavior on integers larger than $10^{308}$ (e.g. $10^{400}$) via a direct Python subprocess test before implementing the safe resolution.
  - Verified offline demo output (`.venv/bin/python -m main`).
- **Displayed Credits / Tokens:**  
  Not available.
- **Suggestion Accepted / Changed / Rejected:**  
  - *Accepted:* Structured `_is_valid_non_negative_finite(val)` to short-circuit Python `int` instances as finite without invoking `math.isfinite()`, eliminating `OverflowError: int too large to convert to float`.
  - *Rejected:* Rejected suggestion to coerce string inputs (e.g. `"10"`) into numeric integers, as the problem statement explicitly mandates strict rejection of non-numeric types.

---

## 3. Tool / Model: OpenAI ChatGPT (Hosted Assistant)

- **Purpose:**  
  - Phase-by-phase project planning and workflow structuring.
  - Conceptual explanations and technical guidance regarding dispatch heuristics and idempotency.
  - Preparation of structured prompts for the local Claude development workflow.
  - Review of user-provided audit summaries and implementation reports.
  - Discussion of regression-testing evidence and documentation requirements.
  - Identification of disclosure accuracy issues.
- **Independently Verified or Changed:**  
  - ChatGPT did not access the local repository directly.
  - ChatGPT did not execute the project's Python code or pytest suite.
  - The user shared supporting material in the ChatGPT conversation, including a regression-test code excerpt, phase audit summaries, and the complete project ZIP (source code and dataset).
  - Recommendations were reviewed by the user and checked against local execution evidence.
  - The complete repository and dataset ZIP were uploaded to hosted ChatGPT for independent review.
  - Test execution and implementation verification were performed locally.
- **Displayed Credits / Tokens:**  
  Not available.
- **Suggestion Accepted / Changed / Rejected:**  
  - *Accepted:* The phase-by-phase review process was used to separate implementation, regression testing, documentation, and final submission preparation.
  - *Changed:* The AI disclosure was revised to distinguish hosted ChatGPT assistance from local development and execution.

---

## 4. Privacy & Integrity Confirmation

- No secrets, API keys, credentials, or private personal data were intentionally shared.
- Code execution and pytest verification were performed locally on the development workstation.
- The complete repository and dataset ZIP were uploaded to hosted ChatGPT for independent review.
- All reported test results (347 passed, 0 failed) originated strictly from local execution.
- Local IDE agent development activity (Claude Sonnet 4.6 and Gemini 3.8 Flash) operated directly in the local repository workspace, distinct from the hosted ChatGPT advisory conversation.

---
*End of AI-Use Declaration*

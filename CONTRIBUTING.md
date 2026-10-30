# Contribution guide

Thanks for taking a look at SmartDispatch. This is a student evaluation project, so make a small change you understand and keep a record of what you tried.

## Before you start

1. Read `STUDENT_PROBLEM_STATEMENT.md` and `STUDENT_START_HERE.md`.
2. Look through the source files, data, tests, and CI workflow so you know how the project is organized.
3. Create a focused branch, such as `fix/partner-capacity-check`.

## Making and checking a change

1. Make one focused change at a time.
2. Run `python -m pytest -q` after a meaningful change. Keep the tests in place; do not skip or weaken them to hide a failure.
3. Record what you actually tested in `TESTING.md`, including failures or limitations.
4. Complete `approach.md`, `challenges.md`, and `optimizations.md` using your own observations. `challenges.md` is compulsory.
5. Complete `DISPATCH_NOTES.md` and any challenge-specific notes required by the problem statement.

## Pull request

Open one pull request from your fork to the original repository, and do not merge it. Describe the problem, your changes, the tests you ran, known limitations, and the process documents you completed. Check the GitHub Actions result and be ready to explain your work or make a small change during review.

## Writing useful project notes

The three process files are worth 15 marks in total. Use examples and test evidence from your actual work. If you did not run a particular experiment or hit a major obstacle, say so plainly and describe the most difficult case you did check. Explain your engineering choices in your own words; do not include private hidden chain-of-thought.

## AI and individual work

This evaluation is intended to show your own understanding. The project instructions prohibit AI help unless your instructor or mentor has explicitly approved an exception. If you have approval, follow its limits and disclose the AI tools you used, what you used them for, and what you checked or changed. Do not share secrets or private personal data. You are responsible for understanding and being able to explain everything in your submission. Ordinary non-AI documentation is allowed. A walkthrough can support an integrity check; an automated detector cannot prove AI use.

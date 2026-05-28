# Archetype template: TEST

Use for: adding/improving tests for existing code. Emphasis: meaningful coverage of real behavior + edge cases.

## Objective
Add tests for `<target>` covering `<behaviors/edge cases>`. Why: `<risk being de-risked>`.

## Success criteria
- New tests in `<test path>` pass and fail correctly (verify they catch a real defect).
- Cover the stated edge cases: `<list>`.
- No reduction in existing coverage.

## Context
- Target under test: `<verified files>`; current coverage gap: `<brief>`.
- Test framework/conventions: `<from context.json>`.

## Approach
- Follow the project's existing test patterns and fixtures.
- For each test, assert real behavior — prove it fails if the behavior breaks (mutation sanity).

## Guardrails
- Do NOT change production code to make tests pass (flag if a change is needed).
- No trivial/tautological tests; each must be able to fail meaningfully.

## Verification
- Run `<test command>`; paste output. Temporarily break the target to confirm a test catches it, then restore.

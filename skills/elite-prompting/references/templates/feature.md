# Archetype template: FEATURE

Use for: adding new behavior. Emphasis: clear spec → tests → implementation → integration.

## Objective
Add `<capability>` so that `<user value>`. Why: `<motivation>`.

## Success criteria
- New behavior covered by tests in `<test path>`, all passing.
- Integrates with `<existing component>` without regressions.
- `<acceptance example>` works end-to-end.

## Context
- Integration points: `<verified files>`.
- Patterns to follow: `<convention from context.json>`.
- Constraints: `<perf/compat/style>`.

## Approach
- If multi-step or touching several modules, enter **plan mode** first and present the plan.
- Use **test-driven-development**: tests for the new behavior before implementation.
- Follow existing patterns discovered in context; do not introduce a new style.

## Guardrails
- Stay within `<scope>`; do not refactor unrelated code.
- Preserve backward compatibility unless the objective says otherwise.

## Verification
- Run `<test + lint command>`; paste output. Demonstrate the acceptance example.

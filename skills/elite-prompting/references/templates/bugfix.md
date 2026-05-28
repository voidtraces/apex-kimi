# Archetype template: BUGFIX

Use for: a known incorrect behavior to correct. Emphasis: reproduce → diagnose → fix → prove.

## Objective
Fix `<symptom>` so that `<correct behavior>`. Why: `<impact>`.

## Success criteria
- A test reproducing the bug exists and now passes.
- `<existing suite/command>` stays green.
- `<observable correct behavior>` confirmed.

## Context
- Suspect area: `<verified file:line>` (`<why>`).
- Reproduction: `<steps or failing command>`.
- Conventions/constraints: `<from context.json>`.

## Approach
- Use the **systematic-debugging** skill: reproduce first, find root cause before fixing.
- Use **test-driven-development**: write the failing test that captures the bug, then fix.
- If the area is unfamiliar/large, Explore (or query the graph) before editing.

## Guardrails
- Fix the root cause, not the symptom; do not mask it.
- Do not change unrelated behavior or public APIs unless required (state if so).

## Verification
- Run `<test command>`; paste output showing the new test passing and suite green before claiming done.

# Archetype template: REFACTOR

Use for: improving structure without changing behavior. Emphasis: behavior-preservation + safety net.

## Objective
Refactor `<target>` to `<improved structure>` without changing observable behavior. Why: `<maintainability/perf reason>`.

## Success criteria
- All existing tests pass unchanged (behavior preserved).
- `<structural goal>` achieved (e.g., file split, duplication removed).
- No public API change (or: the only intended change is `<X>`).

## Context
- Target: `<verified files>`; current shape: `<brief>`.
- Existing tests covering it: `<test path>` (the safety net).

## Approach
- Enter **plan mode** first — refactors are broad and easy to over-reach.
- Establish/confirm the test safety net before changing structure.
- Make small, behavior-preserving steps; run tests between them.

## Guardrails
- Do NOT change behavior; if a test must change, stop and flag it.
- Do not expand scope into adjacent modules.

## Verification
- Run the full suite before and after; paste output proving identical behavior.

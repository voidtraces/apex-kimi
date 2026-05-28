# Archetype template: INVESTIGATE

Use for: understanding/answering a question about the codebase (no code change). Emphasis: grounded findings, not edits.

## Objective
Determine `<question>` and report findings with evidence. Why: `<decision it informs>`.

## Success criteria
- A clear answer, each claim citing a verified `file:line`.
- Open questions / unknowns explicitly listed.

## Context
- Starting points: `<verified files / graph nodes>`.
- Scope of the question: `<bounded area>`.

## Approach
- Use the **Explore** agent (or query the `graphify-out/` graph if present) to map the area.
- Trace, don't guess; cite evidence for every claim.

## Guardrails
- Do NOT modify code. This is read-only.
- Do not speculate beyond evidence; mark uncertainties as such.

## Verification
- Each finding references a real location; re-read cited spans to confirm before reporting.

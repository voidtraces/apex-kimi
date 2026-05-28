# Archetype template: REVIEW

Use for: reviewing existing code/changes for issues. Emphasis: prioritized, evidence-backed findings.

## Objective
Review `<target/diff>` for `<correctness | security | quality>`. Why: `<gate it informs>`.

## Success criteria
- Findings ranked by severity, each with `file:line` + a concrete fix.
- No false alarms: every finding is justified against the code.

## Context
- Target: `<verified files / diff range>`.
- Project conventions to judge against: `<from context.json>`.

## Approach
- Read the target and its immediate dependencies before judging.
- Prefer high-confidence, high-impact findings; avoid nitpick floods.

## Guardrails
- Do NOT rewrite the code; report findings + suggested fixes only.
- Judge against this project's conventions, not personal preference.

## Verification
- Each finding cites a real location and states why it matters; drop anything unverifiable.

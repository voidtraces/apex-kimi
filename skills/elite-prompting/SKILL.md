---
name: elite-prompting
description: Knowledge base for turning a rough request into an elite, grounded, human-gated prompt for Claude Code. Load when running /apex or when authoring a high-quality prompt for an agentic Claude Code task.
---

# Elite Prompting

This skill carries the knowledge apex uses to draft and critique prompts. The orchestrator (`commands/apex.md`) and the `red-team-critic` agent both read these references. **Do not restate their content elsewhere** — these files are the single source of truth.

## References (load on demand)

- `references/principles.md` — how Claude 4.x prompts should be written (the *why* behind the structure).
- `references/claude-code-systems.md` — when an output prompt should tell Claude Code to use plan mode, Explore, a specific skill, or a verification step.
- `references/rubric.md` — the falsifiable dimensions the critic scores (GROUNDING, AMBIGUITY, CONTRADICTION, COMPLETENESS, DETERMINISM, SAFETY).
- `references/anti-patterns.md` — prompt failures to avoid.
- `references/templates/` — archetype output templates (bugfix, feature, refactor, investigate, review, test).
- `references/schemas.md` / `schemas.json` — data contracts for `context.json`, `critic.json`, `state.json`, log entries.

## The layered output structure (what an elite prompt looks like)

Every apex-generated prompt has a **primary** block (always) and an optional **appendix**.

**Primary:**
1. **Objective** — one crisp sentence: the goal + why it matters.
2. **Success criteria / Definition of done** — verifiable, ideally machine-checkable.
3. **Context** — key files, conventions, constraints (from `context.json`; cite verified paths in backticks).
4. **Approach** — the recommended path, naming which Claude-native systems to use (see `claude-code-systems.md`).
5. **Guardrails** — scope boundaries, what NOT to do, anti-patterns.
6. **Verification** — how Claude should prove it is done (run tests, show output).

**Appendix (optional):** detailed context, examples, file inventory, links.

## Minimum-structure rule

Use the **least** structure that removes ambiguity. A trivial task does not need six headings; a complex one does. Structure serves clarity, never ceremony.

## How apex uses this skill

Triage → (clarify if intent lacks goal/success/scope) → ground via `context-scout` → draft inline using the matching archetype template + these principles → `red-team-critic` scores against `rubric.md` → refine only on CRITICAL/HIGH defects → human-gated output. Every cited path must be verified (the orchestrator backstops the critic with `scripts/pathcheck.py`).

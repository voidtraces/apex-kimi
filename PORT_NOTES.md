# apex → Kimi Code 0.4.0 — Port Notes

Phase 0 of the port was a read-only feasibility gate. Findings were resolved against the **running binary** `/home/nullx/.kimi-code/bin/kimi` (v0.4.0), NOT the legacy Python checkout at `~/projects/kimi-cli` — that is the deprecated `kimi-cli`, superseded by `kimi-code` (confirmed by the binary's `migrate` subcommand: "Migrate data from a legacy kimi-cli installation into kimi-code"). Treat the binary + `~/.kimi-code/` as authoritative; the Python source can differ.

## The four blockers and how they resolved
| # | Claude Code primitive apex used | Resolution on Kimi Code 0.4.0 |
|---|---|---|
| 1 | Load `elite-prompting` knowledge | **Non-issue.** The orchestrator loads it via a plain `Read` of `SKILL.md` + references (not the Skill tool). Kimi Code *also* has a native callable `Skill` tool (`name = "Skill"`, params `skill`+`args`), but apex doesn't need it for this. Path substitution only. |
| 2 | `Agent` `subagent_type='context-scout'` / `'red-team-critic'` | **Adapted.** Kimi Code's `Agent` tool supports only built-in `subagent_type`s `coder`/`explore`/`plan`; custom types are NOT registerable by a plugin. Mapped `context-scout → explore` and `red-team-critic → plan` (both read-only; `plan` chosen for the Read-only critic). The agent's role text (`agents/*.md`, frontmatter stripped) is prepended to the dispatch prompt so the built-in agent behaves as the apex agent. |
| 3 | `/apex` slash command from `commands/apex.md` | **Adapted.** Kimi Code has no `commands/` convention; commands are skills invoked as `/skill:<name>`. apex is packaged as the skill `skills/apex/SKILL.md` → invoked `/skill:apex`. |
| 4 | `.claude-plugin/plugin.json` + `${CLAUDE_PLUGIN_ROOT}` | **Adapted.** Manifest is `.kimi-plugin/plugin.json`. Path anchor is `${KIMI_SKILL_DIR}` (injected into skill content at load time), pointing at the apex skill dir; `scripts/` lives inside it so `PYTHONPATH="${KIMI_SKILL_DIR}"` keeps `from scripts import …` working. (`${KIMI_PLUGIN_ROOT}` is the env equivalent for managed-plugin node entries.) |

## Confirmed Kimi Code 0.4.0 facts (binary evidence)
- **LLM-facing tools** (from `name = "X"` tool-class strings + token frequency): `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`, `Skill`, `Agent`, `AskUserQuestion`, `ReadMediaFile`, `TodoList`, `TaskList`/`TaskOutput`/`TaskStop`, `WebSearch`, `EnterPlanMode`/`ExitPlanMode`, `FetchURL`, `mcp__*`. Everything apex uses (`Bash`, `Read`, `Write`, `Agent`, `AskUserQuestion`) has the **same name** as in Claude Code.
- **Stale config red herring:** `~/.kimi-code/config.toml` kimi-mem hooks match `WriteFile|StrReplaceFile|MultiEdit|Shell`, but `StrReplaceFile` and `MultiEdit` appear **0×** in the binary and `WriteFile`/`Shell` only 1–3×. Those matcher names are NOT the real kimi-code tool names — ignore them when reasoning about the toolset.
- **Skill frontmatter schema:** required `name` + `description` (non-empty) for directory skills; optional `type`, `when-to-use`/`whenToUse`, `disable-model-invocation`. Extra metadata (e.g. `argument-hint`, `tags`) is preserved but not enforced.
- **Plugin manifest schema:** `name`, `version`, `description`, `author`, `license`, `keywords`, `skills` (path), optional `sessionStart`, `skillInstructions`, `interface`.
- **Injected variables:** `${KIMI_SKILL_DIR}`, `${KIMI_SESSION_ID}` (skill render-time); `KIMI_PLUGIN_ROOT` (plugin node env); system-prompt vars `KIMI_OS`/`KIMI_SHELL`/`KIMI_NOW`/`KIMI_WORK_DIR`/`KIMI_AGENTS_MD`/`KIMI_SKILLS`.
- **Non-interactive mode:** `kimi -p "<prompt>" [--output-format text|stream-json] [--skills-dir <dir>]` runs one prompt through the full agentic loop and prints the result — used for isolated testing without touching the live runtime.

## What was copied verbatim (NOT edited)
- `skills/apex/scripts/` — `ctxstore.py`, `validate.py`, `pathcheck.py`, `verdict.py`, `log.py`, `__init__.py` (pure Python, platform-agnostic).
- `skills/apex/agents/` — `context-scout.md`, `red-team-critic.md` (role definitions, used as dispatch-prompt text).
- `skills/elite-prompting/` — `SKILL.md`, `references/*` (rubric, principles, claude-code-systems, anti-patterns, schemas.md/json), `references/templates/*`.

## What changed (only `skills/apex/SKILL.md`, converted from `commands/apex.md`)
1. Frontmatter → Kimi skill schema (`name`, `description`, `argument-hint`); dropped Claude `allowed-tools`.
2. All `${CLAUDE_PLUGIN_ROOT}` → `${KIMI_SKILL_DIR}`; knowledge-base read path → `${KIMI_SKILL_DIR}/../elite-prompting/`.
3. Added a "Kimi Code Adaptation" header block; remapped the two subagent dispatches (GROUNDED?/VERIFIED stages) to built-in `explore`/`plan` with role-text injection.
4. Generalized "for Claude Code" → "for the coding agent"; the state machine, scripts, schemas, and rubric are otherwise unchanged.

## Quality enhancements A+B (closing the apex-on-Kimi quality gap)
An investigation found the ~5–10% quality gap vs apex-on-Claude is caused by **model monoculture**: Claude runs the critic on a stronger model (`opus`) than the scout (`sonnet`), while Kimi runs both subagents (`explore`/`plan`) on the single available model (`kimi-for-coding` / Kimi-k2.6 — already Kimi's flagship). Kimi's *reasoning* is sound; it lacked a stronger second-tier critic, which let omissions and schema drift pass. Kimi 0.4.0's `Agent` tool exposes **no `model` param** and only one model is provisioned, so escalating the critic's model is blocked. Two model-independent fixes were added instead:

- **A — deterministic enforcement** (`scripts/kimi_quality.py`, PORT-ADDED; upstream `validate.py` left byte-identical):
  - `enforce_critic_schema(critic)` — rejects critic output where `dimensions` values aren't the strings `"yes"`/`"no"`, the `verdict` is inconsistent with the defects, defects are malformed, or stray top-level keys appear (caught Kimi emitting `{verdict:bool,defects:[]}` + a stray `refine_passes`). Drives a re-prompt of the critic.
  - `lint_draft(draft)` — makes rubric COMPLETENESS deterministic: requires an Objective, ≥2 verifiable Success-criteria bullets, and Guardrails. Missing Objective/Success = HIGH (forces a refine); missing Guardrails = MEDIUM. No length floor (respects the minimum-structure rule).
- **B — sharper critic** (in `skills/apex/SKILL.md` VERIFIED stage; `agents/red-team-critic.md` left verbatim): an *Adversarial Critic Addendum* prepended to the critic dispatch / inline self-critique — mandates the exact `yes`/`no` schema, forbids a lazy empty `defects` list (requires ≥3 concrete checks first), and requires a second AMBIGUITY/DETERMINISM pass.

Wiring: VERIFIED now runs `pathcheck` **and** `kimi_quality`, merges lint defects into `critic.defects` (HIGH lint → COMPLETENESS=no → REFINE), and re-prompts on schema errors. This moves quality from model-judgment to rules, which is model-independent and would also harden apex on Claude.

## What changed (port-authored files only; upstream copies stay verbatim)
1. `skills/apex/SKILL.md` (converted from `commands/apex.md`): Kimi frontmatter; `${CLAUDE_PLUGIN_ROOT}` → `${KIMI_SKILL_DIR}/../..`; Kimi Code Adaptation block; subagent remap to `explore`/`plan`; **+ A/B quality layer wiring + Adversarial Critic Addendum**.
2. `scripts/kimi_quality.py` — **new, additive**; the six upstream `scripts/*.py` remain byte-identical to source.

## Source integrity
The original Claude Code plugin at `/home/nullx/.claude/plugins/cache/apex/apex/0.2.0` is read-only and untouched: no source `.py`/`.md`/`.json` content changed (verified by 0 content mismatches against the port's verbatim copies). The only session-time deltas in that tree are harness-managed runtime artifacts (`.in_use/*` plugin-use markers and `__pycache__` bytecode), not source edits.

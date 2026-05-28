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

## Source integrity
The original Claude Code plugin at `/home/nullx/.claude/plugins/cache/apex/apex/0.2.0` is read-only and untouched (verified by a before/after sha256 of the full tree).

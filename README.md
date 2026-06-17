# apex for Kimi Code

**Turn a rough request into an elite, grounded, human-gated prompt — natively inside [Kimi Code](https://moonshotai.github.io/kimi-code/) (tested on 0.4.0, 0.5.0, and 0.16.0).**

apex is a prompt-engineering orchestrator. You give it a half-formed idea; it runs a disciplined pipeline — clarify intent, ground in your repo, draft against an archetype template, adversarially red-team the draft against a falsifiable rubric, refine only on real defects, and hand you a verified prompt behind a human gate. It **never auto-runs** the prompt it produces.

This repository is a faithful port of apex (originally a Claude Code plugin) to **Kimi Code**, packaged as the skill `/skill:apex`. Built on 0.4.0 and **verified working on 0.4.0, 0.5.0, and 0.16.0** (see [Compatibility](#compatibility)). The reasoning machinery — the state machine, the prompting knowledge base, the deterministic grounding and refinement logic — is carried over unchanged; only the platform glue was adapted (see [Port notes](#the-kimi-port)).

---

## Why apex

- **Grounded, not guessed.** Every concrete reference in a generated prompt traces to a real file/symbol or to your stated intent. A deterministic path-checker (`pathcheck`) backstops the model and rejects hallucinated paths.
- **Adversarially reviewed.** A red-team critic scores every draft against six falsifiable dimensions — Grounding, Ambiguity, Contradiction, Completeness, Determinism, Safety — and the run only finishes once blocking defects are gone.
- **Human-gated by design.** apex produces a prompt and stops. You decide whether to run it. Destructive steps never auto-execute.
- **Deterministic quality floor.** A port-specific quality layer enforces the critic schema and prompt completeness as *rules*, so output quality does not depend on model luck (see [Quality layer](#quality-layer-ab)).

## Requirements

- **Kimi Code 0.4.0, 0.5.0, or 0.16.0** (the `kimi` binary, typically at `~/.kimi-code/bin/kimi`) — verified on all three.
- `python3` (standard library only — no third-party packages).
- `rsync` (used by the installer for a clean, symlink-free copy).

## Compatibility

Verified working on **Kimi Code 0.4.0, 0.5.0, and 0.16.0**. On each version, all primitives apex relies on are present — the native `Skill` tool, the `Agent` tool with the built-in `coder`/`explore`/`plan` subagent types, the `${KIMI_SKILL_DIR}` injection, the `installed.json` plugin loader, and `AskUserQuestion` — and a live registry-loaded `/skill:apex` run drives the full state machine to `DONE` with a schema-clean, `verdict: OK` critic.

**0.16.0 notes** (binary-verified 2026-06-17; details in [`PORT_NOTES.md`](PORT_NOTES.md)): the core contracts are unchanged — `${KIMI_SKILL_DIR}` is still substituted into skill content, both `.kimi-plugin/plugin.json` and a root `kimi.plugin.json` manifest are accepted, `/plugins reload` still exists, and the tool names match. **One behavioral change required a fix:** the `explore` subagent is now strictly read-only (it cannot write files), so the GROUNDED stage no longer asks the scout to *write* `context.json` — the scout *returns* the digest and the orchestrator persists it (the same return-then-persist pattern already used for the critic). The change is backward-compatible with 0.4.0/0.5.0. Note: if another installed plugin (e.g. **superpowers**) declares a `sessionStart` skill, its startup directive is injected into every session and may nudge the model before apex runs; correctness is unaffected.

Note for 0.5.0: `--prompt` can no longer be combined with `--yolo` (`error: Cannot combine --prompt with --yolo`). This does not affect apex — for non-interactive runs use `kimi -p "..."` on its own; `-p` already runs the full agentic loop.

## Install

```bash
git clone https://github.com/voidtraces/apex-kimi.git
cd apex-kimi
./install.sh
```

`install.sh` copies the plugin into `~/.kimi-code/plugins/managed/apex/` as a real **copy, not a symlink**, and registers it in `~/.kimi-code/plugins/installed.json`. Kimi loads plugins from that registry and does **not** auto-scan `plugins/managed/`, so registration is required — the installer does both.

The install is **fully self-contained**: you can move or delete this clone afterward and `/skill:apex` keeps working. The registry is backed up before every edit, and re-running `install.sh` is idempotent.

```bash
KIMI_CODE_HOME=/custom/path ./install.sh   # if Kimi lives somewhere other than ~/.kimi-code
```

Then, in Kimi:

```
/plugins reload      # only needed inside an already-open session; new sessions auto-load
/skill:apex "<your rough idea>"
```

### Uninstall

```bash
./uninstall.sh       # removes the managed copy + its registry entry (backs up first)
```

### Try it without installing

Load the skills from this checkout without touching your live runtime:

```bash
kimi --skills-dir ./skills -p '/skill:apex add a --verbose flag to a hello-world python script'
```

## Usage

```
/skill:apex "<rough idea>" [--flow L0|L1] [--mode bugfix|feature|refactor|investigate|review|test] [--out <file>]
```

- **`--mode`** picks the archetype template (inferred if omitted; defaults to `feature`).
- **`--flow`** picks the depth:
  - **L1** (default in a code repo) — grounds in the repository via a read-only scout, then dispatches the red-team critic. Highest fidelity.
  - **L0** — no repository grounding and no subagents; a fast, self-critiqued pass for general or repo-less tasks.
- **`--out <file>`** offers to save the approved prompt to a file at the human gate.

apex writes its run state under `.apex/<run_id>/` in the current directory (intent, grounding digest, draft revisions, critic report, and a `log.jsonl` telemetry trail).

## How it works

apex executes a fixed state machine, persisting every transition so a run is auditable and resumable:

```
INIT → CLARIFY? → TRIAGED → GROUNDED? → DRAFTED → VERIFIED → REFINE? → OUTPUT → DONE
                  (1 question)  (L1 only)            (red-team)  (loop ≤2)  (human gate)
```

1. **Clarify** — if the request is missing a goal, success criteria, or scope, apex asks one batched question; otherwise it proceeds and records explicit assumptions.
2. **Ground (L1)** — the `context-scout` reads the repo as untrusted data and emits a verified `context.json` of relevant files, conventions, and constraints.
3. **Draft** — apex writes the prompt inline using the matching archetype template and the elite-prompting principles, citing only verified paths.
4. **Verify** — the `red-team-critic` scores the draft against the rubric; a deterministic `pathcheck` independently verifies every cited path.
5. **Refine** — if a CRITICAL/HIGH defect exists, apex re-drafts (hard cap of two passes), then re-verifies.
6. **Output** — apex presents the layered prompt with a status label and a human gate. It does not execute anything.

## The Kimi port

Four Claude-Code primitives were remapped to Kimi Code equivalents; everything else is identical:

| Claude Code primitive | Kimi Code mapping |
| --- | --- |
| `/apex` slash command (`commands/apex.md`) | the skill `skills/apex/SKILL.md`, invoked `/skill:apex` |
| `Agent` `subagent_type="context-scout"` / `"red-team-critic"` | built-in `explore` / `plan` subagents, with each agent's role text injected into the dispatch prompt (Kimi cannot register custom subagent types) |
| `${CLAUDE_PLUGIN_ROOT}` | `${KIMI_SKILL_DIR}/../..` (the plugin root; the relative anchor survives a verbatim copy) |
| `.claude-plugin/plugin.json` | `.kimi-plugin/plugin.json` |

The native `Skill` tool, `AskUserQuestion`, `Bash`, `Read`, and `Write` all exist in Kimi Code under the same names. Full details and the binary-level evidence are in [`PORT_NOTES.md`](PORT_NOTES.md).

### Quality layer (A+B)

On Claude Code apex runs the critic on a stronger model (Opus) than the scout (Sonnet). Kimi Code 0.4.0 exposes a single model and no per-dispatch model override, so the critic cannot be escalated. Two model-independent reinforcements close the resulting quality gap by turning quality into *rules* rather than model luck:

- **A — deterministic enforcement** (`scripts/kimi_quality.py`): `enforce_critic_schema` rejects a critic whose `dimensions` aren't `"yes"`/`"no"` strings, whose verdict is inconsistent with its defects, or that carries stray keys (and triggers a re-prompt); `lint_draft` makes the rubric's Completeness dimension deterministic (requires an Objective, ≥2 verifiable success criteria, and Guardrails).
- **B — a sharper critic**: an Adversarial Critic Addendum in the Verify stage mandates the exact schema, forbids a lazy empty defect list, and requires a second ambiguity/determinism pass.

These also harden apex on Claude — the gains are not Kimi-specific.

## Project layout

```
apex-kimi/
├── .kimi-plugin/plugin.json     # Kimi plugin manifest (skills: "./skills/")
├── install.sh / uninstall.sh    # self-contained, idempotent installer/uninstaller
├── scripts/                     # pure-Python core (verbatim from upstream apex)
│   ├── ctxstore.py              #   run persistence + state machine ledger
│   ├── validate.py              #   structural schema validation
│   ├── pathcheck.py             #   deterministic grounding backstop
│   ├── verdict.py               #   refinement-loop + final-status decisions
│   ├── log.py                   #   telemetry
│   └── kimi_quality.py          #   PORT-ADDED: A+B quality enforcement
├── agents/                      # context-scout & red-team-critic role definitions
└── skills/
    ├── apex/SKILL.md            # the orchestrator state machine → /skill:apex
    └── elite-prompting/         # prompting knowledge base
        ├── SKILL.md
        └── references/          # rubric, principles, schemas, archetype templates
```

The six upstream `scripts/*.py` are byte-identical to the original apex plugin; `kimi_quality.py` is the only added module, keeping the port in sync with upstream while isolating the Kimi-specific layer.

## Verification

```bash
# Python core imports and validates (run from the repo root)
PYTHONPATH=. python3 -c "from scripts import ctxstore,validate,pathcheck,verdict,log,kimi_quality; \
  print(validate.validate({'repo_mode':'none','relevant_files':[],'conventions':[],'constraints':[],'entry_points':[],'conflicts':[],'untrusted_excerpts':[],'index':[]},'context'))"
# -> []

# Manifest parses
python3 -c "import json; json.load(open('.kimi-plugin/plugin.json')); print('manifest OK')"
```

A live registry-loaded run of `/skill:apex` (no `--skills-dir`) drives the full state machine to `DONE` and produces a schema-clean critic — confirming the install is discoverable and self-contained.

## Credits & license

apex is by its original authors; this is the Kimi Code port. Licensed under **MIT** (see `.kimi-plugin/plugin.json`).

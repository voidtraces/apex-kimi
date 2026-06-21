---
name: apex
description: Turn a rough request into an elite, grounded, human-gated prompt for the coding agent. Use when the user runs /skill:apex or asks to craft a high-quality prompt for an agentic coding task.
argument-hint: "<rough idea> [--flow L0|L1] [--mode bugfix|feature|refactor|investigate|review|test] [--out <file>]"
---

# apex — orchestrator (Kimi Code port)

You are the apex orchestrator. Execute the state machine below **in order**. You hold the user's full-fidelity intent and do all synthesis (clarify, draft, refine, select) inline; you delegate only to `context-scout` (asymmetry) and `red-team-critic` (isolation). Never spawn other agents. Never auto-run the generated prompt.

> ## 🧭 KIMI CODE ADAPTATION — read first (this is the Kimi Code port of apex)
> apex was authored for Claude Code; this skill runs it natively on **Kimi Code 0.4.0–0.16.0** (originally built for 0.4.0/0.5.0; verified on 0.16.0 — see `PORT_NOTES.md`). Three platform mappings apply throughout — everything else is unchanged:
> 1. **Plugin root → `${KIMI_SKILL_DIR}/../..`.** `${KIMI_SKILL_DIR}` is this skill's own directory (substituted at load time), i.e. `<apex-root>/skills/apex`. The portable Python package and the agent role files live at the **apex plugin root** `${KIMI_SKILL_DIR}/../..` (one level above `skills/`). Set `PYTHONPATH="${KIMI_SKILL_DIR}/../.."` so `from scripts import <mod>` resolves AND the scripts find their schemas (which they locate relative to their own dir). The shared knowledge base lives at the sibling skill `${KIMI_SKILL_DIR}/../elite-prompting/`; the agent role files at `${KIMI_SKILL_DIR}/../../agents/`.
> 2. **Subagent dispatch.** Kimi Code's `Agent` tool supports only the built-in `subagent_type`s `coder`/`explore`/`plan` — it cannot register custom types. So apex's two agents are mapped to built-ins and their role is carried IN the dispatch prompt:
>    - `context-scout` → `Agent(subagent_type="explore", …)` — read-only exploration. **On Kimi Code `explore` cannot write files**, so the scout *returns* its `context.json` and the orchestrator persists it (see GROUNDED?).
>    - `red-team-critic` → `Agent(subagent_type="plan", …)` — read-only review (`plan`, not `coder`, because the critic must not write).
>    Before each dispatch, **read the matching role file** (`${KIMI_SKILL_DIR}/../../agents/context-scout.md` or `${KIMI_SKILL_DIR}/../../agents/red-team-critic.md`), strip its YAML frontmatter, and **prepend that role text to the dispatch prompt** so the built-in agent behaves as that apex agent.
> 3. **Tool names are identical** to what the steps reference: `Read`, `Bash`, `Write`, `Agent`, `AskUserQuestion` all exist in Kimi Code under the same names.
>
> The generated prompt targets **the coding agent you are running on (Kimi Code)**. The `elite-prompting` knowledge base names Claude-Code-native systems (plan mode, Explore, skills); Kimi Code has direct equivalents (plan mode via Enter/ExitPlanMode, `Agent subagent_type="explore"`, `/skill:` skills), so apply that guidance to the Kimi equivalents.

> ## ⛔ COMPLETION INVARIANT — read before you start
> **`INIT → OUTPUT` is ONE uninterrupted run — never stop in the middle.** A run halts (silently) the
> moment you end your turn at any stage before `OUTPUT`. This has happened at *every* stage, including
> the very first: a real run froze at `INTENT_CAPTURED` with empty `stages` — intent captured, then the
> turn ended, and nothing else ever ran. **Operational test for ending your turn: end ONLY when
> `current_state` == `DONE`, or when you are blocked on the one `AskUserQuestion` in `CLARIFY?` or the
> `OUTPUT` human gate. Those are the only two sanctioned pauses.** A returned tool call, a finished
> stage, or a `###` heading is **not** a stopping point — immediately begin the next stage in the same
> turn. Each `### ` stage block below ends with a `→` checkpoint naming the next stage; obey it.
>
> Two corollaries (the most-violated specifics of the rule above):
> 1. **A DRAFTED prompt is NOT a result.** Never show, summarize, or stop on the draft — it is an
>    intermediate artifact. The only thing you ever present is the **OUTPUT-stage, human-gated,
>    status-labeled** result (i.e. after `VERIFY` ran: `red-team-critic` dispatched AND `pathcheck`
>    applied, then `final_status` computed). If you feel "the draft looks good, I'll show it," STOP —
>    run VERIFY first.
> 2. **Every stage transition MUST call `ctxstore.advance(...)` — which does `set_state` *and* writes
>    that stage's telemetry line — and that call must *return* before the stage counts as done.** The
>    persisted `stages{}` is the run's ledger; skipping a call (including `GROUNDED`) makes it lie and
>    breaks resume. Producing a stage's artifact (e.g. a `context.json`) without its matching
>    `advance` is itself a defect.

Raw request and flags: `$ARGUMENTS`

**Conventions for every script call** (scripts live in the apex plugin root `${KIMI_SKILL_DIR}/../..`, one level above `skills/`; state lives in the project cwd):
```
PYTHONPATH="${KIMI_SKILL_DIR}/../.." python3 -c "from scripts import <mod>; ..."
```
The persistence base is `.apex` in the current working directory. Load the skill knowledge first: read `${KIMI_SKILL_DIR}/../elite-prompting/SKILL.md` and the references it points to (especially `rubric.md`, `principles.md`, `claude-code-systems.md`, and the matching `templates/<archetype>.md`).

## State machine

### INIT → INTENT_CAPTURED
- `run_id` = UTC timestamp slug (e.g. `20260527-021500`).
- Write immutable intent:
  ```
  PYTHONPATH="${KIMI_SKILL_DIR}/../.." python3 -c "from scripts import ctxstore; ctxstore.init_run('.apex','<run_id>', '''<raw idea>''')"
  ```
- **Resume check:** if `.apex/<run_id>/state.json` already exists with a `current_state` past INIT, resume at the next stage using persisted artifacts instead of restarting.
- → **Do not end your turn here.** Proceed immediately to **CLARIFY?**.

### CLARIFY?
- Determine the archetype (`--mode` if given, else infer: bug→bugfix, add→feature, etc.; default `feature`).
- Decide flow: `--flow` if given; else **L1** if cwd is a code repo (has files / a `.git`) and the task is code-related; else **L0**.
- If the intent is missing any of {goal | success criteria | scope}, ask **one** batched `AskUserQuestion` (≤3 questions). Never re-ask. If the user skips, proceed and record explicit assumptions in the draft.
- `ctxstore.advance('.apex','<run_id>','CLARIFIED', {...})`.
- → After that call returns (and any clarifying answer is in hand), proceed immediately to **TRIAGED**.

### TRIAGED
- `ctxstore.advance('.apex','<run_id>','TRIAGED', {'flow': '<L0|L1>', 'archetype': '<arch>'})`.
- → After that call returns, proceed immediately to **GROUNDED?** (if `flow == L1`) or directly to **DRAFTED** (if `flow == L0`). Do not stop.

### GROUNDED?  (L1 only — skip for L0)
- Dispatch **context-scout** via the `Agent` tool with `subagent_type="explore"` (see Kimi Code Adaptation §2: first read `${KIMI_SKILL_DIR}/../../agents/context-scout.md`, strip its frontmatter, and prepend that role text). Provide: the intent, repo root (cwd), and a max-files cap (e.g. 40 for small repos). **Kimi Code's `explore` subagent is read-only and cannot write files**, so instruct the scout to **return the `context.json` object as its final message**, and **you persist it**: `ctxstore.write_artifact('.apex','<run_id>','context.json', <returned JSON>)` — the same return-then-persist pattern the VERIFIED stage uses for the critic. Parse the returned text as JSON; if it is not valid JSON, retry the scout once asking for a bare JSON object only.
- Validate the return:
  ```
  PYTHONPATH="${KIMI_SKILL_DIR}/../.." python3 -c "from scripts import ctxstore,validate; print(validate.validate(ctxstore.read_artifact('.apex','<run_id>','context.json'),'context'))"
  ```
  - Errors (non-empty list) → **retry scout once** with a widened query. Still invalid → continue **without** grounding (draft will state assumptions) — but still record the transition: `ctxstore.advance('.apex','<run_id>','GROUNDED', {'degraded': True})`. "Without grounding" never means "without the bookkeeping."
- Grounded (normal) path: `ctxstore.advance('.apex','<run_id>','GROUNDED')`.
- → Either way, after the `GROUNDED` call returns, proceed immediately to **DRAFTED**. Do not stop.

### DRAFTED
- Draft the prompt **inline** using the matching `templates/<archetype>.md` + `principles.md`, grounded in `context.json` (cite verified paths in backticks; pull spans lazily via `ctxstore.resolve_pointer` only if you need exact text). Apply the **minimum-structure rule**.
- Persist: `ctxstore.write_draft('.apex','<run_id>', '''<draft markdown>''')`.
- `ctxstore.advance('.apex','<run_id>','DRAFTED')`.
- → **DO NOT STOP OR SHOW THE DRAFT HERE.** A draft is an intermediate artifact, never the deliverable.
  Proceed immediately to **VERIFIED**. (Per the Completion Invariant corollary 1: the user only ever sees the OUTPUT-stage result.)

### VERIFIED
- **L1:** dispatch **red-team-critic** via the `Agent` tool with `subagent_type="plan"` (see Kimi Code Adaptation §2: first read `${KIMI_SKILL_DIR}/../../agents/red-team-critic.md`, strip its frontmatter, and prepend that role text **plus the Adversarial Critic Addendum below**). Pass raw intent + the draft + path to `rubric.md` (`${KIMI_SKILL_DIR}/../elite-prompting/references/rubric.md`). The critic is **Read-only** — it *returns* the critic JSON, it does **not** write a file — so **you persist what it returns**: `ctxstore.write_artifact('.apex','<run_id>','critic.json', <returned JSON>)`. Then validate it (`validate.validate(critic,'critic')`); invalid after one retry → fall back to the inline path-only critic below.
- **L0:** do **not** dispatch any subagent (L0 spawns zero subagents). Perform an **inline self-critique**: judge the draft yourself against `rubric.md` **applying the Adversarial Critic Addendum below**, then write `critic.json` in the `critic` schema shape.
- **Both flows:** always run the deterministic backstop and merge its defects into `critic.defects` (this is the inline path-only critic when a critic is unavailable):
  ```
  PYTHONPATH="${KIMI_SKILL_DIR}/../.." python3 -c "import json,pathlib; from scripts import ctxstore,pathcheck; ctx=ctxstore.read_artifact('.apex','<run_id>','context.json') if pathlib.Path('.apex/<run_id>/context.json').exists() else {'relevant_files':[],'untrusted_excerpts':[]}; print(json.dumps(pathcheck.cross_check(ctxstore.read_draft('.apex','<run_id>'), ctx, '.')))"
  ```
- **Kimi quality layer (port enhancement — deterministic, compensates for single-tier critique):** also run `scripts/kimi_quality` and act on it:
  ```
  PYTHONPATH="${KIMI_SKILL_DIR}/../.." python3 -c "import json; from scripts import ctxstore,kimi_quality; c=ctxstore.read_artifact('.apex','<run_id>','critic.json'); print('SCHEMA_ERRORS='+json.dumps(kimi_quality.enforce_critic_schema(c))); print('DRAFT_DEFECTS='+json.dumps(kimi_quality.lint_draft(ctxstore.read_draft('.apex','<run_id>'))))"
  ```
  - **`SCHEMA_ERRORS` non-empty** → the critic output is malformed (e.g. object-valued dimensions, wrong/inconsistent verdict, stray keys). **Re-dispatch the critic once**, quoting the exact errors and the required shape (`dimensions` values are the strings `"yes"`/`"no"`; top-level keys are exactly `dimensions`/`defects`/`verdict`; `verdict` is `"OK"` only with zero CRITICAL/HIGH). Still malformed → rebuild a minimal valid `critic.json` from the deterministic checks only (path-only critic), then continue.
  - **Merge `DRAFT_DEFECTS` (lint_draft) AND the `pathcheck` defects into `critic.defects`**, and set `critic.dimensions.COMPLETENESS="no"` if any lint defect is HIGH. These make the rubric's COMPLETENESS deterministic, so a weak critic cannot pass an incomplete draft; HIGH lint defects therefore force a REFINE.
  - Re-persist the merged, schema-clean `critic.json`.
- **Adversarial Critic Addendum** (prepended to the critic dispatch in L1 and applied during the L0 self-critique — Kimi port, to recover the sharpness of a dedicated stronger-model critic):
  > 1. Output `dimensions` values MUST be the exact strings `"yes"`/`"no"` — never objects or booleans. Emit only the keys `dimensions`, `defects`, `verdict`. `verdict` is `"OK"` only with zero CRITICAL/HIGH defects.
  > 2. Do **not** return an empty `defects` list lightly. First, internally check at least three concrete things — one each for **AMBIGUITY** (any instruction with ≥2 readings?), **DETERMINISM** (any under-specified decision point?), and **GROUNDING** (any reference not traceable to context/intent?) — and only conclude "no defect" per dimension after that check. Bias toward surfacing real, located, fixable defects over praise.
  > 3. Make a **second pass**: after your first verdict, re-read the draft once more hunting specifically for AMBIGUITY and DETERMINISM gaps you may have missed; add any found.
- `ctxstore.advance('.apex','<run_id>','VERIFIED')`.
- → After that call returns, proceed immediately to **REFINE?**. Do not stop.

### REFINE?
- ```
  PYTHONPATH="${KIMI_SKILL_DIR}/../.." python3 -c "import json; from scripts import verdict, kimi_quality; c=json.load(open('.apex/<run_id>/critic.json')); p=kimi_quality.refine_passes_done('.apex','<run_id>'); print('refine_passes_done='+str(p)); print('should_refine='+str(verdict.should_refine(c, p)))"
  ```
  (use the merged critic with backstop defects). The pass count is computed **deterministically from the telemetry** by `kimi_quality.refine_passes_done` — you do NOT track it yourself — so the `MAX_PASSES=2` hard cap always engages even if you lose count across turns. `should_refine=True` → re-DRAFT applying each CRITICAL/HIGH `fix`, then re-VERIFY. `should_refine=False` → continue.
- → This is a decision, not a pause: on `True` loop back to **DRAFTED**, on `False` proceed immediately to **OUTPUT**. Never end your turn here.

### OUTPUT
- Compute final status:
  ```
  PYTHONPATH="${KIMI_SKILL_DIR}/../.." python3 -c "from scripts import verdict; import json; c=json.load(open('.apex/<run_id>/critic.json')); print(verdict.final_status(c, False))"
  ```
- **Completeness self-audit (bookkeeping backstop):**
  ```
  PYTHONPATH="${KIMI_SKILL_DIR}/../.." python3 -c "from scripts import ctxstore,verdict; st=ctxstore.get_state('.apex','<run_id>'); print('MISSING:', verdict.missing_stages(st, st.get('flow','L1')))"
  ```
  If non-empty, a transition's `set_state` was skipped earlier. **Record the missing key(s) only** (e.g. call `set_state` for each, or note them in the status) — do **NOT** re-execute the stage's work: re-running `GROUNDED` would re-dispatch the scout and re-running `DRAFTED` would mutate the draft after `VERIFY`, voiding the adversarial gate.
- Present the **layered prompt** (primary block; appendix if useful) + a collapsible rationale + any stated assumptions.
- **If status == UNVERIFIED:** label it clearly at the top (`⚠️ UNVERIFIED`) and list the residual CRITICAL/HIGH defects. Never emit UNVERIFIED output without this label + list.
- **HUMAN GATE:** ask the user — "Review the prompt. Run it now / refine further / save to file?" Never execute it yourself. If `--out <file>` was given and the user approves saving, write the prompt there.
- Telemetry is now written **automatically** by each `ctxstore.advance(...)` transition above (one `logentry` per stage in `.apex/log.jsonl`) — no separate batch write. You may attach spec-§8 extras as kwargs, e.g. `advance('.apex','<run_id>','VERIFIED', agent='red-team-critic', verdict='OK')`.
- `ctxstore.advance('.apex','<run_id>','DONE')`.
- → **OUTPUT is the terminal stage** — there is no "next stage." After the human gate and the `DONE` call, the run is complete; this is the one place ending your turn is correct.

## Degradation summary (intelligent, never catastrophic)
- scout invalid after one retry → continue **ungrounded**, draft states assumptions, status may be UNVERIFIED.
- critic invalid after one retry → **inline path-only critic** (deterministic backstop only).
- budget/interruption → persisted state allows **resume**; partial output emitted as `⚠️ UNVERIFIED` with residual defects.
- Any destructive instruction in the draft must sit behind the human gate — never auto-run.

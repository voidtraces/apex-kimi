# apex for Kimi Code 0.4.0

A faithful port of the **apex** prompting system (originally a Claude Code plugin) to **Kimi Code 0.4.0**. apex turns a rough request into an elite, grounded, human-gated prompt for an agentic coding task: it clarifies intent, grounds in the repo via a read-only scout, drafts against archetype templates, red-teams the draft against a falsifiable rubric, refines on blocking defects, and presents a human-gated result. It never auto-runs the generated prompt.

See `PORT_NOTES.md` for the platform mapping (the four Claude-Code primitives and how each was adapted).

## Layout
```
apex-kimi/
  .kimi-plugin/plugin.json     # Kimi plugin manifest (skills: "./skills/")
  skills/
    apex/
      SKILL.md                 # the orchestrator → /skill:apex
      scripts/                 # pure-Python persistence/validation (verbatim)
      agents/                  # context-scout & red-team-critic role defs (verbatim)
    elite-prompting/
      SKILL.md, references/    # prompting knowledge base + archetype templates (verbatim)
  PORT_NOTES.md
```

## Try it without installing (isolated)
`--skills-dir` loads skills from a directory instead of the live runtime, so nothing in `~/.kimi-code/` is touched:
```bash
mkdir -p /tmp/apex-scratch && cd /tmp/apex-scratch
kimi --skills-dir /home/nullx/projects/apex-kimi/skills \
  -p '/skill:apex add a --verbose flag to a hello-world python script'
```
Inspect the run state it produces:
```bash
cat /tmp/apex-scratch/.apex/*/state.json   # expect "current_state": "DONE"
```
For an interactive session (recommended for the clarify step, which uses AskUserQuestion):
```bash
cd /tmp/apex-scratch
kimi --skills-dir /home/nullx/projects/apex-kimi/skills
# then type:  /skill:apex add a --verbose flag to a hello-world python script
```

## Install (self-contained — survives deleting this checkout)
Run the installer from this directory:
```bash
./install.sh
```
It copies the plugin into `~/.kimi-code/plugins/managed/apex/` (a real **copy, not a symlink**) and registers it in `~/.kimi-code/plugins/installed.json` — Kimi loads plugins from that registry; it does **not** auto-scan `plugins/managed/`, so registration is required. The install is fully self-contained: **you can delete or move this source checkout afterward and `/skill:apex` keeps working.** `installed.json` is backed up before editing, and re-running `install.sh` is idempotent.

After installing, in Kimi run:
```
/plugins reload
/skill:apex "<your rough idea>"
```
Override the location with `KIMI_CODE_HOME=/path ./install.sh` if Kimi lives elsewhere.

To remove it:
```bash
./uninstall.sh   # deletes the managed copy + its installed.json entry (backs up first), then /plugins reload
```

## Self-checks
```bash
# Python layer imports + validates (run from the port root — scripts/ lives here)
cd /home/nullx/projects/apex-kimi && \
  PYTHONPATH=. python3 -c "from scripts import ctxstore,validate,pathcheck,verdict,log,kimi_quality; \
  print(validate.validate({'repo_mode':'none','relevant_files':[],'conventions':[],'constraints':[],'entry_points':[],'conflicts':[],'untrusted_excerpts':[],'index':[]},'context'))"
# -> []

# Manifest parses
python3 -c "import json;json.load(open('/home/nullx/projects/apex-kimi/.kimi-plugin/plugin.json'));print('manifest OK')"
```

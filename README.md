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

## Install for real (user-approved step)
Either install as a managed-style plugin or expose just the skills:
- **Skills only:** symlink the two skill dirs into a discovered skills dir, e.g.
  `ln -s /home/nullx/projects/apex-kimi/skills/apex ~/.kimi-code/skills/apex`
  `ln -s /home/nullx/projects/apex-kimi/skills/elite-prompting ~/.kimi-code/skills/elite-prompting`
- **As a plugin:** place this directory under `~/.kimi-code/plugins/managed/apex/` (it already carries `.kimi-plugin/plugin.json`).

Then run `/skill:apex "<your rough idea>"` in any project.

## Self-checks
```bash
# Python layer imports + validates
cd /home/nullx/projects/apex-kimi/skills/apex && \
  PYTHONPATH=. python3 -c "from scripts import ctxstore,validate,pathcheck,verdict,log; \
  print(validate.validate({'repo_mode':'none','relevant_files':[],'conventions':[],'constraints':[],'entry_points':[],'conflicts':[],'untrusted_excerpts':[],'index':[]},'context'))"
# -> []

# Manifest parses
python3 -c "import json;json.load(open('/home/nullx/projects/apex-kimi/.kimi-plugin/plugin.json'));print('manifest OK')"
```

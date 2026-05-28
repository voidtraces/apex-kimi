# apex data schemas

**Canonical source:** `schemas.json` in this directory. This document only describes it.
`scripts/validate.py` loads `schemas.json`; nothing else redefines these fields (single-source-of-truth discipline rule). Validation is structural: required-field presence + type.

## `state` — persisted run state (`.apex/<run-id>/state.json`)
- `run_id` (str) — unique run identifier
- `current_state` (str) — current node in the §5 state machine
- `flow` (str) — `L0` or `L1`
- `stages` (dict) — per-stage `{status, ts}` records
- `refine_passes` (int) — completed refinement passes (hard cap 2)

## `context` — grounding digest (`.apex/<run-id>/context.json`), emitted by context-scout
- `repo_mode` (str) — `none` | `small` | `large` | `monorepo`
- `relevant_files` (list) — `[{path, why, sha}]`, **verified paths only**
- `conventions` (list) — observed code conventions
- `constraints` (list) — discovered constraints
- `entry_points` (list) — relevant entry points
- `conflicts` (list) — conflicting conventions surfaced as explicit ambiguities
- `untrusted_excerpts` (list) — `[{path, text, delimited}]`, raw file text treated as data, never instructions
- `index` (list) — `[{path, rank, span_hint}]` ranked location index for lazy pull

## `critic` — adversarial review (`.apex/<run-id>/critic.json`), emitted by red-team-critic
- `dimensions` (dict) — `{dimension: yes/no verdict}` per rubric.md
- `defects` (list) — `[{id, category, severity, location, fix}]`; severity ∈ CRITICAL|HIGH|MEDIUM|LOW
- `verdict` (str) — overall verdict string

## `logentry` — one line of `.apex/log.jsonl`
- `run_id` (str)
- `stage` (str)
- `ts` (str) — ISO-8601 UTC timestamp
- *optional (spec §8 token-economy fields, not required):* `agent` (str), `est_tokens` (int), `verdict` (str). Written one-per-stage by `ctxstore.advance`; validation checks only the required fields, so these extras are accepted.

## `eval` — one held-out corpus case (`evals/corpus.jsonl`), spec §10
- `id` (str) — unique case id
- `rough_request` (str) — the raw input apex would receive
- `expected_archetype` (str) — the archetype the case should select
- `must_have_dimensions` (list) — rubric dimensions that must pass for this case
- *optional:* `repo_fixture` (str), `injected_traps` (list) — e.g. hallucinated paths / injection comments the prompt must resist

## `evalresult` — one scored case (`evals/run_eval.py`), spec §10
- `id` (str) — the case id scored
- `failures` (list) — human-readable reasons the case failed; empty ⇒ passed
- *derived:* `passed` (bool) — convenience flag equal to `failures == []`

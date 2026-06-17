"""Kimi-port quality layer (PORT-ADDED — not part of upstream apex).

Closes the apex-on-Kimi quality gap by moving two quality checks from
model-judgment into deterministic rules, so a single-tier (no Opus critic)
runtime cannot let weak output through:

- ``enforce_critic_schema`` — the canonical critic shape (rubric.md / schemas.json)
  requires ``dimensions`` values to be the strings "yes"/"no" and ``verdict`` to be
  consistent with the defects. Upstream ``validate.py`` only checks types
  structurally, so a critic that emits object-valued dimensions, a wrong verdict,
  or malformed defects passes silently. This makes that shape a hard rule.
- ``lint_draft`` — makes the rubric's COMPLETENESS dimension deterministic:
  a draft MUST have an Objective, verifiable Success criteria (>=2 bullets), and
  Guardrails. A weak critic can no longer pass an incomplete draft.

Both return ``list[dict]`` defects in the same shape ``pathcheck.cross_check``
uses, so the orchestrator merges them into ``critic.defects`` identically. This
file is intentionally separate from the verbatim upstream ``scripts/`` so the
port stays in sync with upstream while isolating the Kimi-specific divergence.
"""
from __future__ import annotations

import json
import pathlib
import re

_DIMENSIONS = (
    "GROUNDING", "AMBIGUITY", "CONTRADICTION",
    "COMPLETENESS", "DETERMINISM", "SAFETY",
)
_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
_BLOCKING = {"CRITICAL", "HIGH"}
_CRITIC_TOP_KEYS = {"dimensions", "defects", "verdict"}
_DEFECT_KEYS = {"id", "category", "severity", "location", "fix"}


def enforce_critic_schema(critic: dict) -> list[str]:
    """Return a list of schema-violation strings; empty means the critic is well-formed.

    Stricter than the structural ``validate.py``: enforces the *value* shapes the
    rubric mandates, so the orchestrator can re-prompt a critic that drifts
    (e.g. Kimi emitting ``{"verdict": true, "defects": []}`` per dimension).
    """
    errs: list[str] = []

    dims = critic.get("dimensions")
    if not isinstance(dims, dict):
        errs.append("dimensions: must be an object keyed by rubric dimension")
    else:
        for d in _DIMENSIONS:
            if d not in dims:
                errs.append(f"dimensions: missing dimension '{d}'")
            elif dims[d] not in ("yes", "no"):
                errs.append(
                    f"dimensions.{d}: must be the string 'yes' or 'no', "
                    f"got {type(dims[d]).__name__} ({dims[d]!r})"
                )

    defects = critic.get("defects")
    if not isinstance(defects, list):
        errs.append("defects: must be a list")
        defects = []
    for i, df in enumerate(defects):
        if not isinstance(df, dict):
            errs.append(f"defects[{i}]: must be an object")
            continue
        missing = _DEFECT_KEYS - df.keys()
        if missing:
            errs.append(f"defects[{i}]: missing keys {sorted(missing)}")
        if df.get("severity") not in _SEVERITIES:
            errs.append(f"defects[{i}].severity: must be one of {sorted(_SEVERITIES)}")
        if df.get("category") not in _DIMENSIONS:
            errs.append(f"defects[{i}].category: must be a rubric dimension")

    verdict = critic.get("verdict")
    if verdict not in ("OK", "FAIL"):
        errs.append("verdict: must be 'OK' or 'FAIL'")
    else:
        has_blocking = any(
            isinstance(df, dict) and df.get("severity") in _BLOCKING for df in defects
        )
        expected = "FAIL" if has_blocking else "OK"
        if verdict != expected:
            errs.append(
                f"verdict: inconsistent — is '{verdict}' but with "
                f"{'a' if has_blocking else 'no'} CRITICAL/HIGH defect it must be '{expected}'"
            )

    stray = set(critic.keys()) - _CRITIC_TOP_KEYS
    if stray:
        errs.append(f"unexpected top-level keys (not in critic schema): {sorted(stray)}")

    return errs


def _section_present(text: str, *names: str) -> bool:
    """True if any of ``names`` appears as a markdown heading or bold label."""
    for n in names:
        if re.search(rf"(?im)^\s*#{{1,6}}\s*{re.escape(n)}\b", text):
            return True
        if re.search(rf"(?im)^\s*\*\*{re.escape(n)}", text):
            return True
    return False


def _success_bullets(text: str) -> int:
    """Count bullet/numbered lines under the Success-criteria / Definition-of-done heading."""
    m = re.search(
        r"(?ims)^\s*#{1,6}\s*(success criteria|definition of done)\b(.*?)(?=^\s*#{1,6}\s|\Z)",
        text,
    )
    if not m:
        return 0
    body = m.group(2)
    return len(re.findall(r"(?m)^\s*(?:[-*]|\d+[.)])\s+\S", body))


def lint_draft(draft_text: str) -> list[dict]:
    """Deterministic COMPLETENESS check → defects in pathcheck/critic shape.

    Mirrors rubric.md COMPLETENESS severities: missing Objective or verifiable
    Success criteria is HIGH; missing Guardrails is MEDIUM. Deliberately does NOT
    impose a length floor (that would violate apex's minimum-structure rule);
    it only checks that the required sections exist and that success criteria
    carry at least two verifiable bullets.
    """
    defects: list[dict] = []

    if not _section_present(draft_text, "Objective"):
        defects.append(_d("L1", "COMPLETENESS", "HIGH", "missing Objective section",
                          "Add an Objective stating the goal and why it matters."))

    if not _section_present(draft_text, "Success criteria", "Definition of done"):
        defects.append(_d("L2", "COMPLETENESS", "HIGH", "missing Success criteria",
                          "Add verifiable Success criteria (machine-checkable where possible)."))
    elif _success_bullets(draft_text) < 2:
        defects.append(_d("L3", "COMPLETENESS", "HIGH", "Success criteria not verifiable",
                          "List >=2 concrete, checkable success criteria as bullets."))

    if not _section_present(draft_text, "Guardrails"):
        defects.append(_d("L4", "COMPLETENESS", "MEDIUM", "missing Guardrails section",
                          "Add Guardrails bounding scope and stating what NOT to do."))

    return defects


def _d(did: str, category: str, severity: str, location: str, fix: str) -> dict:
    return {"id": did, "category": category, "severity": severity,
            "location": location, "fix": fix}


def refine_passes_done(base: str, run_id: str) -> int:
    """Deterministic refine-pass count for the MAX_PASSES cap (model-independent).

    ``verdict.should_refine(critic, passes)`` enforces the hard cap only if the
    orchestrator passes a truthful ``passes``. On a runtime where the model may
    not reliably track that counter across turns, the cap can silently fail to
    engage (observed live: an unbounded refine churn while each adversarial
    critic kept finding defects). This derives the count from the telemetry that
    every ``ctxstore.advance`` writes: the number of DRAFTED transitions that
    occur *after* the first VERIFIED for this run — i.e. the re-drafts produced
    by the refine loop (the initial drafting before the first verify does not
    count). Trusting the ledger instead of the model makes the cap robust; it
    errs conservative (a stray same-pass re-save counts up), which only ever
    stops the loop sooner, never later.
    """
    log = pathlib.Path(base) / "log.jsonl"
    if not log.exists():
        return 0
    seen_verified = False
    passes = 0
    for line in log.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get("run_id") != run_id:
            continue
        stage = entry.get("stage")
        if stage == "VERIFIED":
            seen_verified = True
        elif stage == "DRAFTED" and seen_verified:
            passes += 1
    return passes

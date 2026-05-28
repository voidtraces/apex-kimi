"""apex run persistence: immutable intent, state machine, artifacts, pointers.

State lives under ``<base>/<run_id>/`` (base is typically ``.apex``). This module
holds NO prompting knowledge — only deterministic persistence + grounding I/O.
"""
import hashlib
import json
import pathlib
import time


def _run_dir(base: str, run_id: str) -> pathlib.Path:
    """Return the directory ``<base>/<run_id>/`` that holds one run's files.

    ``base`` is the path to the ``.apex`` directory; ``run_id`` is the
    caller-supplied run identifier (in practice a ``YYYYMMDD-HHMMSS`` stamp).
    Everything a single run owns lives under this directory:

    - ``intent.txt`` — the immutable raw intent (``init_run``, written once).
    - ``state.json`` — the run ledger / current state (``_write_state``, via
      ``init_run`` and ``set_state``).
    - arbitrary named artifacts, e.g. the grounding ``context.json`` and the
      review ``critic.json`` digests (``write_artifact`` / ``read_artifact``).
    - ``draft.md`` plus versioned ``draft.vN.md`` snapshots (``write_draft``).
    """
    return pathlib.Path(base) / run_id


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_state(base: str, run_id: str, state: dict) -> None:
    state["updated_ts"] = _now()
    (_run_dir(base, run_id) / "state.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )


def init_run(base: str, run_id: str, intent: str) -> str:
    """Create the run directory, write immutable intent.txt, init state.

    intent.txt is written once and never overwritten (Context Fidelity Law).
    """
    d = _run_dir(base, run_id)
    d.mkdir(parents=True, exist_ok=True)
    intent_path = d / "intent.txt"
    if not intent_path.exists():
        intent_path.write_text(intent, encoding="utf-8")
    if not (d / "state.json").exists():
        _write_state(base, run_id, {
            "run_id": run_id,
            "created_ts": _now(),
            "updated_ts": _now(),
            "current_state": "INTENT_CAPTURED",
            "flow": "",
            "archetype": "",
            "repo_mode": "",
            "stages": {},
            "refine_passes": 0,
        })
    return str(d)


def get_state(base: str, run_id: str) -> dict:
    return json.loads((_run_dir(base, run_id) / "state.json").read_text(encoding="utf-8"))


def set_state(base: str, run_id: str, current_state: str, updates: dict | None = None) -> None:
    st = get_state(base, run_id)
    st["current_state"] = current_state
    if updates:
        st.update(updates)
    st.setdefault("stages", {})[current_state] = {"status": "done", "ts": _now()}
    _write_state(base, run_id, st)


def advance(base: str, run_id: str, current_state: str, updates: dict | None = None, **log_extra) -> None:
    """``set_state`` plus a per-stage telemetry line, in one call.

    The orchestrator used to batch-write the log once at OUTPUT, so stages went
    missing and timestamps collapsed. Coupling the transition with its log line
    here makes the ledger and ``.apex/log.jsonl`` impossible to drift apart: one
    ``logentry`` ({run_id, stage, ts} plus any spec-§8 extras such as ``agent`` /
    ``est_tokens`` / ``verdict``) is appended for every transition.
    """
    set_state(base, run_id, current_state, updates)
    from scripts import log  # local import keeps ctxstore's module load free of log/validate
    entry = {"run_id": run_id, "stage": current_state, "ts": _now()}
    entry.update(log_extra)
    log.append(base, entry)


def write_artifact(base: str, run_id: str, name: str, data) -> str:
    p = _run_dir(base, run_id) / name
    p.write_text(
        json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data),
        encoding="utf-8",
    )
    return str(p)


def read_artifact(base: str, run_id: str, name: str):
    p = _run_dir(base, run_id) / name
    txt = p.read_text(encoding="utf-8")
    return json.loads(txt) if name.endswith(".json") else txt


def write_draft(base: str, run_id: str, text: str) -> str:
    """Append a new draft revision (draft.vN.md) and update the draft.md pointer."""
    d = _run_dir(base, run_id)
    n = len(list(d.glob("draft.v*.md"))) + 1
    p = d / f"draft.v{n}.md"
    p.write_text(text, encoding="utf-8")
    (d / "draft.md").write_text(text, encoding="utf-8")
    return str(p)


def read_draft(base: str, run_id: str) -> str:
    return (_run_dir(base, run_id) / "draft.md").read_text(encoding="utf-8")


def pull_span(file: str, start_line: int, end_line: int) -> str:
    """Return lines [start_line, end_line] (1-indexed, inclusive) from a file."""
    lines = pathlib.Path(file).read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[start_line - 1:end_line])


def resolve_pointer(ref: dict):
    """Resolve a grounding pointer to its text span, or None if unverifiable.

    Returns None when the file is missing or (if a sha is supplied) the file's
    content sha does not match — stale/tampered pointers are refused, never
    silently returned (Grounding Integrity Law).
    """
    p = pathlib.Path(ref["file"])
    if not p.exists():
        return None
    if "sha" in ref:
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        if actual != ref["sha"]:
            return None
    return pull_span(ref["file"], ref["start_line"], ref["end_line"])

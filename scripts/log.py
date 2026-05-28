"""Append-only run telemetry for apex (`.apex/log.jsonl`).

Each entry is validated against the ``logentry`` schema before being written, so
malformed telemetry can never silently corrupt the log.
"""
import json
import pathlib

from scripts.validate import validate


def append(base: str, entry: dict) -> None:
    errs = validate(entry, "logentry")
    if errs:
        raise ValueError("invalid log entry: " + "; ".join(errs))
    p = pathlib.Path(base) / "log.jsonl"
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

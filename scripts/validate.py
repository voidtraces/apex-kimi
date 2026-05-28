"""Structural validation of apex data artifacts against the canonical schemas.

The single source of truth for schemas is
``skills/elite-prompting/references/schemas.json``. This module holds NO
prompting knowledge — only data-contract enforcement (field presence + type).
"""
import json
import pathlib

_SCHEMA_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "skills/elite-prompting/references/schemas.json"
)
_TYPES = {"str": str, "list": list, "dict": dict, "int": int}


def _schemas() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def validate(data: dict, schema_name: str) -> list[str]:
    """Return a list of error strings; empty means valid.

    Raises KeyError if ``schema_name`` is not defined in schemas.json.
    """
    spec = _schemas()[schema_name]["required"]
    errs: list[str] = []
    for field, typename in spec.items():
        if field not in data:
            errs.append(f"missing field: {field}")
        elif not isinstance(data[field], _TYPES[typename]):
            errs.append(f"field {field} must be {typename}")
    return errs

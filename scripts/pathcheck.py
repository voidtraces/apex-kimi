"""Deterministic grounding cross-check — the code backstop for the critic.

Every backticked, file-like token cited in a draft must be a *verified* path:
present in ``context.relevant_files`` OR existing on disk under the repo root.
Paths appearing only inside ``untrusted_excerpts`` do NOT count as verified.
"""
import pathlib
import re

# Backticked tokens that look like a file path (have a dotted extension).
_PATH_RE = re.compile(r"`([A-Za-z0-9_./-]+\.[A-Za-z0-9_]+)`")

# A bare token is only treated as a *path claim* if it carries a known source
# extension; otherwise dotted code refs (`obj.method`) and numeric literals
# (`0.0`) would false-positive. Tokens containing "/" are always path claims.
_KNOWN_EXTS = {
    "py", "js", "ts", "tsx", "jsx", "go", "rs", "java", "rb", "c", "h", "cpp",
    "hpp", "cc", "cs", "php", "swift", "kt", "scala", "lua", "sh", "bash",
    "md", "txt", "rst", "json", "toml", "yaml", "yml", "cfg", "ini", "env",
    "xml", "html", "css", "scss", "sql", "proto", "tf",
}


def _is_path_claim(token: str) -> bool:
    if "/" in token:
        return True
    return token.rsplit(".", 1)[-1].lower() in _KNOWN_EXTS


def cross_check(draft_text: str, context: dict, repo_root: str) -> list[dict]:
    """Return GROUNDING defects for every cited path that is not verified."""
    known = {f["path"] for f in context.get("relevant_files", [])}
    # Basenames of verified files: a draft may cite a bare `verdict.py` when the
    # verified relevant file is `scripts/verdict.py`. That is grounded (it names a
    # real, verified file), so it must not be a false CRITICAL — only a *bare*
    # token (no "/") with a known basename qualifies; `ghost.py` stays flagged.
    known_basenames = {k.rsplit("/", 1)[-1] for k in known}
    root = pathlib.Path(repo_root)
    defects: list[dict] = []
    candidates = [m for m in dict.fromkeys(_PATH_RE.findall(draft_text)) if _is_path_claim(m)]
    for i, m in enumerate(candidates):  # dedupe, keep order
        if m in known or (root / m).exists():
            continue
        if "/" not in m and m in known_basenames:
            continue
        defects.append({
            "id": f"G{i}",
            "category": "GROUNDING",
            "severity": "CRITICAL",
            "location": m,
            "fix": f"Path `{m}` is unverified; remove it or replace with a verified path.",
        })
    return defects

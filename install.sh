#!/usr/bin/env bash
# Self-contained installer for the apex Kimi Code plugin.
# Copies this port into Kimi's managed-plugins dir (NOT a symlink) and registers
# it in installed.json, so deleting this source checkout never breaks the install.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIMI_HOME="${KIMI_CODE_HOME:-$HOME/.kimi-code}"
DEST="$KIMI_HOME/plugins/managed/apex"
REG="$KIMI_HOME/plugins/installed.json"

# --- sanity checks -----------------------------------------------------------
[ -f "$SRC/.kimi-plugin/plugin.json" ] || {
  echo "ERROR: run from the apex-kimi port root (no .kimi-plugin/plugin.json found)" >&2; exit 1; }
[ -d "$KIMI_HOME/plugins" ] || {
  echo "ERROR: $KIMI_HOME/plugins not found — is Kimi Code installed? (set KIMI_CODE_HOME to override)" >&2; exit 1; }
[ -f "$REG" ] || { echo "ERROR: registry not found: $REG" >&2; exit 1; }
command -v rsync >/dev/null || { echo "ERROR: rsync is required" >&2; exit 1; }

# --- 1. self-contained copy (no symlinks; single source so --delete is safe) -
echo "==> Copying apex -> $DEST"
mkdir -p "$DEST"
rsync -a --delete \
  --exclude='.git/' --exclude='.gitignore' \
  --exclude='__pycache__/' --exclude='*.py[cod]' \
  --exclude='.apex/' --exclude='*.swp' --exclude='.DS_Store' \
  --exclude='install.sh' --exclude='uninstall.sh' \
  "$SRC"/ "$DEST"/

# --- 2. register in installed.json (idempotent upsert, with backup) ----------
echo "==> Registering in $REG"
APEX_ROOT="$DEST" APEX_ORIGIN="$SRC" python3 - "$REG" <<'PY'
import json, os, sys, shutil, datetime
reg = sys.argv[1]
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
bak = reg + ".bak." + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
shutil.copy2(reg, bak)
data = json.load(open(reg))
if not isinstance(data.get("plugins"), list):
    print("ERROR: installed.json has no 'plugins' array", file=sys.stderr); sys.exit(1)
entry = next((p for p in data["plugins"] if p.get("id") == "apex"), None)
if entry is None:
    data["plugins"].append({
        "id": "apex", "root": os.environ["APEX_ROOT"], "source": "local-path",
        "enabled": True, "installedAt": now, "updatedAt": now,
        "originalSource": os.environ["APEX_ORIGIN"],
    })
    action = "registered new"
else:
    entry.update(root=os.environ["APEX_ROOT"], source="local-path", enabled=True, updatedAt=now)
    entry.setdefault("installedAt", now)
    entry.setdefault("originalSource", os.environ["APEX_ORIGIN"])
    action = "updated existing"
json.dump(data, open(reg, "w"), indent=2)
open(reg, "a").write("\n")
print(f"    {action} 'apex' entry  (backup: {bak})")
PY

echo
echo "apex installed (self-contained) at: $DEST"
echo "Next: in Kimi run  /plugins reload   then  /skill:apex \"<your idea>\""

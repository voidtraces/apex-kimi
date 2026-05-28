#!/usr/bin/env bash
# Uninstaller for the apex Kimi Code plugin. Removes the managed copy and its
# installed.json entry (idempotent; backs up the registry first). Leaves all
# other plugins untouched.
set -euo pipefail

KIMI_HOME="${KIMI_CODE_HOME:-$HOME/.kimi-code}"
DEST="$KIMI_HOME/plugins/managed/apex"
REG="$KIMI_HOME/plugins/installed.json"

if [ -f "$REG" ]; then
  echo "==> Removing 'apex' from $REG"
  python3 - "$REG" <<'PY'
import json, sys, shutil, datetime
reg = sys.argv[1]
data = json.load(open(reg))
bak = reg + ".bak." + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
shutil.copy2(reg, bak)
before = len(data.get("plugins", []))
data["plugins"] = [p for p in data.get("plugins", []) if p.get("id") != "apex"]
json.dump(data, open(reg, "w"), indent=2)
open(reg, "a").write("\n")
print(f"    removed {before - len(data['plugins'])} 'apex' entry  (backup: {bak})")
PY
else
  echo "==> registry not found ($REG) — skipping deregistration"
fi

if [ -d "$DEST" ]; then
  rm -rf "$DEST"
  echo "==> removed $DEST"
else
  echo "==> $DEST not present — nothing to remove"
fi

echo
echo "apex uninstalled. In Kimi run  /plugins reload  to apply."

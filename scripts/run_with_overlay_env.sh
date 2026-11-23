#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="/Users/boyuewu/Projects/JusticePlutus"
PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"

cd "$PROJECT_ROOT"

eval "$("$PYTHON_BIN" - <<'PY'
from pathlib import Path
from dotenv import dotenv_values
import shlex

root = Path("/Users/boyuewu/Projects/JusticePlutus")
merged = {}

for name in (".env", ".env.local"):
    path = root / name
    if not path.exists():
        continue
    for key, value in dotenv_values(path).items():
        if value is not None:
            merged[key] = value

for key, value in merged.items():
    print(f"export {key}={shlex.quote(value)}")
PY
)"

exec "$PYTHON_BIN" -m justice_plutus run "$@"

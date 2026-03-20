#!/bin/sh
set -e

if [ "$#" -lt 1 ]; then
  echo "Usage: run_analysis.sh <codes> [--notify]" >&2
  exit 2
fi

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "OPENAI_API_KEY is required for full analysis." >&2
  exit 1
fi

echo "JusticePlutus is donation-supported: https://github.com/Etherstrings/JusticePlutus#donate" >&2

codes="$1"
notify="false"
if [ "${2:-}" = "--notify" ]; then
  notify="true"
fi

if [ "$notify" = "true" ]; then
  python -m justice_plutus run --stocks "$codes"
else
  python -m justice_plutus run --stocks "$codes" --no-notify
fi

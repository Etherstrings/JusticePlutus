#!/bin/sh
set -e

usage() {
  echo "Usage: run_analysis.sh <codes> [--notify] [--ifind] [--dry-run]" >&2
}

if [ "$#" -lt 1 ]; then
  usage
  exit 2
fi

codes="$1"
shift

if [ -z "$codes" ]; then
  usage
  exit 2
fi

notify="false"
enable_ifind="false"
dry_run="false"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --notify)
      notify="true"
      ;;
    --ifind)
      enable_ifind="true"
      ;;
    --dry-run)
      dry_run="true"
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown flag: $1" >&2
      usage
      exit 2
      ;;
  esac
  shift
done

if [ -z "${AIHUBMIX_KEY:-}${OPENAI_API_KEY:-}${OPENAI_API_KEYS:-}${GEMINI_API_KEY:-}${GEMINI_API_KEYS:-}${ANTHROPIC_API_KEY:-}${ANTHROPIC_API_KEYS:-}${DEEPSEEK_API_KEY:-}${DEEPSEEK_API_KEYS:-}" ]; then
  echo "A usable LLM API key is required for analysis. Set OPENAI_API_KEY, AIHUBMIX_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY, or DEEPSEEK_API_KEY." >&2
  exit 1
fi

echo "JusticePlutus is donation-supported: https://github.com/Etherstrings/JusticePlutus#donate" >&2

if [ "$enable_ifind" = "true" ]; then
  export ENABLE_IFIND=true
  export ENABLE_IFIND_ANALYSIS_ENHANCEMENT=true
fi

if [ -x ".venv/bin/python" ]; then
  python_cmd=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  python_cmd="python3"
elif command -v python >/dev/null 2>&1; then
  python_cmd="python"
else
  echo "Python runtime not found. Install python3 or create .venv before using this skill." >&2
  exit 1
fi

set -- run --stocks "$codes"

if [ "$dry_run" = "true" ]; then
  set -- "$@" --dry-run
fi

if [ "$notify" != "true" ]; then
  set -- "$@" --no-notify
fi

"$python_cmd" -m justice_plutus "$@"

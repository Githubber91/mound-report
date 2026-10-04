#!/usr/bin/env bash
# Task runner. `make` could not be written to this folder, so this script
# does the same job: ./tasks.sh check
set -euo pipefail

# Always run from this folder, and find the package from source.
cd "$(dirname "$0")"
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-check}" in
  setup)  uv venv --python 3.12 && uv pip install -e ".[dev]" ;;
  format) uv run ruff format src tests && uv run ruff check --fix src tests ;;
  lint)   uv run ruff check src tests && uv run ruff format --check src tests ;;
  types)  uv run mypy src tests ;;
  test)   uv run pytest ;;
  check)  uv run ruff check src tests && uv run ruff format --check src tests && uv run mypy src tests && uv run pytest ;;
  season) uv run python -m pitchlab.ingest --season "${2:-2026}" ;;
  export) uv run python -m pitchlab.export --season "${2:-2026}" --out ../public/data ;;
  ingest) uv run python -m pitchlab.ingest --start "${2:?start date}" --end "${3:?end date}" ;;
  *)      echo "usage: ./tasks.sh {setup|format|lint|types|test|check|season [year]|export [year]|ingest start end}" ; exit 1 ;;
esac

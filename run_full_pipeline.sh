#!/bin/bash
# Thin wrapper around the Python pipeline orchestrator.

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
    echo "Virtual environment not found: $VENV_PYTHON"
    exit 1
fi

cd "$PROJECT_DIR"
export MPLBACKEND=Agg
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/ubs-mpl}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/ubs-cache}"
mkdir -p "$MPLCONFIGDIR" "$XDG_CACHE_HOME"
PYTHONPATH="$PROJECT_DIR" "$VENV_PYTHON" -m src.run_full_pipeline "$@"

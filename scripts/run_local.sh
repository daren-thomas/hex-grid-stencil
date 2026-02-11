#!/usr/bin/env bash
set -euo pipefail

# Run the full local workflow with uv-managed dependencies.
# Usage: ./scripts/run_local.sh

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed. Install it: https://docs.astral.sh/uv/" >&2
  exit 1
fi

uv sync
uv run python hex_grid_template.py
uv run python render_stl_preview.py

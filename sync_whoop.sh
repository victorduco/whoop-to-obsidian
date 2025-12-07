#!/bin/bash
# Whoop to Obsidian sync wrapper script
# This script runs the Python module and handles logging

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR" || exit 1

# Set up Python environment
export PYTHONUNBUFFERED=1

# Run the sync using uv
uv run python -m whoop_obsidian

# Capture exit code
EXIT_CODE=$?

# Log completion
if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Sync completed successfully"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Sync failed with exit code $EXIT_CODE" >&2
fi

exit $EXIT_CODE

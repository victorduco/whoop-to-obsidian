#!/bin/bash
# Install and set up the Whoop to Obsidian scheduler

set -e  # Exit on error

echo "==================================="
echo "Whoop to Obsidian Scheduler Setup"
echo "==================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "Error: config.yaml not found!"
    echo "Please create config.yaml from config.example.yaml first"
    exit 1
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if PyYAML is available
echo "Checking dependencies..."
if ! uv run python -c "import yaml" 2>/dev/null; then
    echo "Installing PyYAML..."
    uv add pyyaml
fi

echo ""
echo "Installing scheduler..."
echo ""

# Run the update_schedule.py script to install
uv run python update_schedule.py install

echo ""
echo "==================================="
echo "✓ Installation Complete!"
echo "==================================="
echo ""
echo "The sync will now run automatically according to the schedule"
echo "configured in config.yaml"
echo ""
echo "Useful commands:"
echo "  uv run python update_schedule.py status     - Check scheduler status"
echo "  uv run python update_schedule.py install    - Update schedule from config"
echo "  uv run python update_schedule.py uninstall  - Remove scheduler"
echo "  ./sync_whoop.sh                             - Run sync manually"
echo ""

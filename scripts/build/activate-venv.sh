#!/bin/bash
# Convenience script to activate the virtual environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Navigate to project root (two levels up from scripts/build/)
cd "$SCRIPT_DIR/../.."

echo "Activating Python virtual environment..."
source venv/bin/activate
echo "Virtual environment activated!"
echo ""
echo "Python: $(which python3)"
echo "Pip: $(which pip)"
echo ""
echo "To deactivate, run: deactivate"

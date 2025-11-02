#!/bin/bash
# Convenience script to activate the virtual environment

echo "Activating Python virtual environment..."
source venv/bin/activate
echo "Virtual environment activated!"
echo ""
echo "Python: $(which python3)"
echo "Pip: $(which pip)"
echo ""
echo "To deactivate, run: deactivate"

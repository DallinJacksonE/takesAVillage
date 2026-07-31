#!/bin/bash

VENV_DIR="venv"

# 1. Check if the venv is actually valid (looks for the activate script)
if [ ! -f "$VENV_DIR/bin/activate" ]; then
  echo "Venv missing or broken. Creating/Re-creating..."
  # Remove the folder if it exists but is broken
  rm -rf "$VENV_DIR"
  python3 -m venv "$VENV_DIR"
else
  echo "Valid virtual environment found."
fi

# 2. Activate
source "$VENV_DIR/bin/activate"

# 3. Install the reproducible dependency manifest from the repository root.
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r ../requirements-dev.txt
echo "Setup complete!"

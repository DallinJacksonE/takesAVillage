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

# 3. Install Flask using the venv's pip specifically
echo "Installing dependencies..."
pip install --upgrade pip
pip install flask
pip install flask-socketio
pip install eventlet
pip install mysql-connector-python
pip install matplotlib
pip install uuid
echo "Setup complete!"

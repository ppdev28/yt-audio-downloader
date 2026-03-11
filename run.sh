#!/bin/bash
# This script runs the youtube downloader using the correct python interpreter from the virtual environment.

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Path to the virtual environment's python
VENV_PYTHON="$DIR/.venv/bin/python3"
VENV_PIP="$DIR/.venv/bin/pip"

# Path to the main script
MAIN_SCRIPT="$DIR/backend/main.py"

# Check if the virtual environment's python exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Python interpreter not found in virtual environment."
    echo "Please run the following commands to create the virtual environment and install dependencies:"
    echo "python3 -m venv .venv"
    echo "source .venv/bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

# Install/update dependencies
"$VENV_PIP" install -r "$DIR/requirements.txt"

# Run the script with all the arguments passed to this script
"$VENV_PYTHON" "$MAIN_SCRIPT" "$@"

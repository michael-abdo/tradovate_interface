#!/bin/bash
# Simple test runner with Python environment detection

# Find a suitable Python with pytest installed
if python3 -c "import pytest" 2>/dev/null; then
    PYTHON="python3"
elif python -c "import pytest" 2>/dev/null; then
    PYTHON="python"
elif /usr/bin/python3 -c "import pytest" 2>/dev/null; then
    PYTHON="/usr/bin/python3"
else
    echo "Error: Could not find a Python installation with pytest installed."
    echo "Please run: pip install pytest pychrome requests flask"
    exit 1
fi

echo "Using Python: $($PYTHON --version)"

# Make sure we're in the project root directory
cd "$(dirname "$0")/.." || exit 1

# Set up environment variables
export SKIP_BROWSER_TESTS=true
export SKIP_INTEGRATION_TESTS=true

# Run the specified test file or all tests
if [ -n "$1" ]; then
    TEST_PATH="tests/$1"
    if [ ! -e "$TEST_PATH" ]; then
        TEST_PATH="$1"
    fi
    echo "Running test: $TEST_PATH"
    $PYTHON -m pytest -xvs "$TEST_PATH"
else
    echo "Running all tests"
    $PYTHON -m pytest -xvs tests/test_simple.py
fi
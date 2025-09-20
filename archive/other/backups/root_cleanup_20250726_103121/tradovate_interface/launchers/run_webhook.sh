#!/bin/bash
# This script launches the pinescript_webhook service with the correct Python path

# Get the project root directory (parent of the script directory)
PROJECT_ROOT=$(dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)")

# Add execution permissions to the script if not already executable
chmod +x "$0"

# Change to the project root directory to ensure all imports work correctly
cd "$PROJECT_ROOT"

# Run the webhook service
python "$PROJECT_ROOT/src/pinescript_webhook.py"
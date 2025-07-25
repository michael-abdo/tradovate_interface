#!/usr/bin/env python3
"""
Launcher script for pinescript_webhook.py
This script allows users to continue using the command as before
while the actual implementation has moved to the src directory
"""
import sys
import os

# Add the project root to the path so we can import from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.pinescript_webhook import run_flask

if __name__ == "__main__":
    run_flask()
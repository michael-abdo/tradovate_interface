#!/usr/bin/env python3
"""
Launcher script for dashboard.py
This script allows users to continue using the command as before
while the actual implementation has moved to the src directory
"""
import sys
from src.dashboard import run_flask_dashboard, app

if __name__ == "__main__":
    run_flask_dashboard()
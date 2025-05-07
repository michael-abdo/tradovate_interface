#!/usr/bin/env python3
"""
Launcher script for login_helper.py
This script allows users to continue using the command as before
while the actual implementation has moved to the src directory
"""
import sys
from src.login_helper import main

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Launcher script for chrome_logger.py
This script allows users to continue using the command as before
while the actual implementation has moved to the src directory
"""
import sys
import os
from src.chrome_logger import main

if __name__ == "__main__":
    sys.exit(main())
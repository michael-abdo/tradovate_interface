#!/usr/bin/env python3
"""
Launcher script for chrome_stability.py
"""
import sys
import os

# Add the project root to the path so we can import from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.utils.chrome_stability import main

if __name__ == "__main__":
    sys.exit(main())
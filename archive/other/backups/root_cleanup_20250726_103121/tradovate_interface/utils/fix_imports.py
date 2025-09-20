"""
Module to fix Python imports by adding the project root to the path.
Include this at the top of any script that needs to import from src:

import sys
import os
# Add the project root to the path
from utils.fix_imports import add_project_root_to_path
add_project_root_to_path()

# Now you can import from src
from src.app import TradovateController
"""

import os
import sys


def add_project_root_to_path():
    """
    Add the project root directory to the Python sys.path
    This allows importing from the src directory regardless of the current working directory
    
    Returns:
        str: The path added to sys.path
    """
    # Find the project root (parent of the utils directory)
    file_path = os.path.abspath(__file__)
    utils_dir = os.path.dirname(file_path)
    project_root = os.path.dirname(utils_dir)
    
    # Add to path if not already there
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"Added {project_root} to Python path")
    
    return project_root


if __name__ == "__main__":
    # If run directly, show the current Python path
    path = add_project_root_to_path()
    print(f"Project root: {path}")
    print("Current Python path:")
    for i, p in enumerate(sys.path):
        print(f"{i}: {p}")
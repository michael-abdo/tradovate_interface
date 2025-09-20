#!/usr/bin/env python3
"""
Minimal test for Tradovate Interface.

This test verifies that the basic file structure and imports work.
It doesn't require any browser or external dependencies.
"""

import os
import sys
import pytest

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_project_structure():
    """Test that key project directories exist."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check for essential directories
    assert os.path.isdir(os.path.join(project_root, "src")), "src directory missing"
    assert os.path.isdir(os.path.join(project_root, "tests")), "tests directory missing"
    assert os.path.isdir(os.path.join(project_root, "config")), "config directory missing"
    
    # Check for key source files
    assert os.path.isfile(os.path.join(project_root, "src", "__init__.py")), "src/__init__.py missing"
    
    # Output success message
    print("\nProject structure verification passed!")
    return True

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
#!/usr/bin/env python3
"""
Minimal test for Tradovate Interface.

This test is completely isolated from the pytest framework and doesn't
depend on any external libraries. It's meant to be a basic sanity check.
"""

import os
import sys

def test_project_structure():
    """Test that key project directories exist."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check for essential directories
    errors = []
    
    if not os.path.isdir(os.path.join(project_root, "src")):
        errors.append("src directory missing")
    
    if not os.path.isdir(os.path.join(project_root, "tests")):
        errors.append("tests directory missing")
    
    if not os.path.isdir(os.path.join(project_root, "config")):
        errors.append("config directory missing")
    
    # Check for key source files
    if not os.path.isfile(os.path.join(project_root, "src", "__init__.py")):
        errors.append("src/__init__.py missing")
    
    # Return results
    if errors:
        print("\n❌ Project structure verification failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n✅ Project structure verification passed!")
        return True

def test_credentials_file():
    """Test that the credentials file exists."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    credentials_path = os.path.join(project_root, "config", "credentials.json")
    
    if os.path.isfile(credentials_path):
        print(f"✅ Credentials file exists at: {credentials_path}")
        return True
    else:
        print(f"❌ Credentials file missing: {credentials_path}")
        return False

def main():
    """Run all tests."""
    print("\n=== Running Minimal Tests ===\n")
    
    # Run tests
    structure_ok = test_project_structure()
    credentials_ok = test_credentials_file()
    
    # Summarize results
    print("\n=== Test Summary ===")
    print(f"Project Structure: {'✅ PASS' if structure_ok else '❌ FAIL'}")
    print(f"Credentials File: {'✅ PASS' if credentials_ok else '❌ FAIL'}")
    
    # Overall result
    if structure_ok and credentials_ok:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
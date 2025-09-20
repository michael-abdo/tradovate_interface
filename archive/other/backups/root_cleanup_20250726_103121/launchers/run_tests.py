#!/usr/bin/env python3
"""
Test runner for Tradovate Interface.

This script provides a simple way to run different test sets:
- Smoke test: Basic functionality check
- Unit tests: Fast tests that don't require browser
- Integration tests: Full tests including browser interaction
- Full workflow test: Complete end-to-end test
"""

import os
import sys
import argparse
import subprocess

def run_tests(test_type, credentials=None):
    """Run the specified type of tests."""
    # Set environment variables if credentials provided
    if credentials:
        username, password = credentials
        os.environ['TRADOVATE_TEST_USERNAME'] = username
        os.environ['TRADOVATE_TEST_PASSWORD'] = password
    
    # Build the command based on test type
    if test_type == 'smoke':
        print("Running smoke test...")
        test_command = [
            sys.executable,  # Current Python executable
            "-m",
            "pytest",
            "-xvs",
            "tests/test_smoke.py"
        ]
    elif test_type == 'unit':
        print("Running unit tests...")
        # Skip browser-dependent tests
        os.environ['SKIP_BROWSER_TESTS'] = 'true'
        os.environ['SKIP_INTEGRATION_TESTS'] = 'true'
        test_command = [
            sys.executable,
            "-m",
            "pytest",
            "-xvs",
            "tests"
        ]
    elif test_type == 'integration':
        print("Running integration tests...")
        os.environ['TRADOVATE_TEST_LOGIN'] = 'true'
        test_command = [
            sys.executable,
            "-m",
            "pytest",
            "-xvs",
            "tests/test_integration.py"
        ]
    elif test_type == 'workflow':
        print("Running full workflow test...")
        os.environ['TRADOVATE_TEST_LOGIN'] = 'true'
        test_command = [
            sys.executable,
            "-m",
            "pytest",
            "-xvs",
            "tests/test_full_workflow.py"
        ]
    else:
        print(f"Unknown test type: {test_type}")
        return False
    
    # Run the test
    print(f"Executing: {' '.join(test_command)}")
    result = subprocess.run(test_command)
    
    return result.returncode == 0

def main():
    """Parse arguments and run tests."""
    parser = argparse.ArgumentParser(description='Run Tradovate Interface tests')
    parser.add_argument('test_type', choices=['smoke', 'unit', 'integration', 'workflow'], 
                        help='Type of test to run')
    parser.add_argument('--username', help='Tradovate username')
    parser.add_argument('--password', help='Tradovate password')
    
    args = parser.parse_args()
    
    credentials = None
    if args.username and args.password:
        credentials = (args.username, args.password)
    
    success = run_tests(args.test_type, credentials)
    
    if success:
        print("\n✅ Tests completed successfully!")
        return 0
    else:
        print("\n❌ Tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Test launcher for full workflow testing.

This script executes the full workflow test:
1. Starts Chrome 
2. Auto-logins to Tradovate
3. Starts dashboard
4. Executes a trade
5. Confirms the position
"""

import os
import sys
import subprocess
import argparse

def run_test(credentials=None):
    """Run the full workflow test with optional credentials."""
    # Set environment variables
    if credentials:
        username, password = credentials
        os.environ['TRADOVATE_TEST_USERNAME'] = username
        os.environ['TRADOVATE_TEST_PASSWORD'] = password
    
    # Always enable login for this test
    os.environ['TRADOVATE_TEST_LOGIN'] = 'true'
    
    # Build the command
    test_command = [
        sys.executable,  # Current Python executable
        "-m",
        "pytest",
        "-xvs",
        "tests/test_full_workflow.py"
    ]
    
    # Run the test
    print(f"Running test: {' '.join(test_command)}")
    result = subprocess.run(test_command)
    
    return result.returncode == 0

def main():
    """Parse arguments and run the test."""
    parser = argparse.ArgumentParser(description='Run the full workflow test')
    parser.add_argument('--username', help='Tradovate username')
    parser.add_argument('--password', help='Tradovate password')
    
    args = parser.parse_args()
    
    credentials = None
    if args.username and args.password:
        credentials = (args.username, args.password)
    
    success = run_test(credentials)
    
    if success:
        print("\n✅ Test completed successfully!")
        return 0
    else:
        print("\n❌ Test failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
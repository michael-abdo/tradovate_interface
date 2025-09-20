#!/usr/bin/env python3
import subprocess
import sys

try:
    # Try to run the fetch script
    result = subprocess.run([sys.executable, 'fetch_todays_data.py'], 
                          capture_output=True, 
                          text=True,
                          cwd='/Users/Mike/trading/algos/EOD')
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
        
    print(f"\nReturn code: {result.returncode}")
    
except Exception as e:
    print(f"Error: {e}")
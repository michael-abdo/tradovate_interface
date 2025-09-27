#!/usr/bin/env python3
"""
Test auto_login startup to see if Chrome windows open
"""
import subprocess
import sys
import time
import os

print("Testing auto_login.py startup...")
print("This will start Chrome windows for configured accounts\n")

# Start auto_login
proc = subprocess.Popen(
    [sys.executable, "-m", "src.auto_login"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

print(f"Process started with PID: {proc.pid}")
print("\nMonitoring output for 15 seconds:")
print("-" * 50)

start_time = time.time()
cleanup_file = None

try:
    while time.time() - start_time < 15:
        if proc.poll() is not None:
            print(f"\n!!! Process exited early with code: {proc.returncode}")
            # Read any remaining output
            for line in proc.stdout:
                print(f"  {line.rstrip()}")
            break
            
        line = proc.stdout.readline()
        if line:
            print(f"  {line.rstrip()}")
            if "CLEANUP_STATUS_FILE:" in line:
                cleanup_file = line.split(":", 1)[1].strip()
                print(f"\n>>> Detected cleanup file: {cleanup_file}")
            if "Chrome instances running:" in line:
                print("\n>>> SUCCESS: Chrome instances are running!")
            if "Failed to start any Chrome instances" in line:
                print("\n>>> ERROR: No Chrome instances started!")
                
except KeyboardInterrupt:
    print("\n\nInterrupted by user")

finally:
    print("\n" + "-" * 50)
    print("Cleaning up...")
    
    if proc.poll() is None:
        print("Sending SIGINT to auto_login...")
        proc.terminate()
        try:
            proc.wait(timeout=10)
            print("Process terminated successfully")
        except subprocess.TimeoutExpired:
            print("Process didn't terminate, killing...")
            proc.kill()
            proc.wait()
    
    # Check for Chrome processes
    print("\nChecking for Chrome processes on managed ports:")
    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True
    )
    
    found = 0
    for line in result.stdout.split('\n'):
        if "remote-debugging-port=922" in line and "tradovate" in line.lower():
            port = line.split("remote-debugging-port=")[1].split()[0]
            if int(port) >= 9223:
                found += 1
                print(f"  Found Chrome on port {port}")
    
    if found == 0:
        print("  No Chrome processes found on managed ports")
    
    print("\nTest complete!")
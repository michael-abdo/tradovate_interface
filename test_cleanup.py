#!/usr/bin/env python3
"""
Test script to verify robust subprocess cleanup implementation.
This script tests various shutdown scenarios to ensure all daemon threads are properly stopped.
"""
import subprocess
import time
import os
import signal
import sys
import threading

def run_test(test_name, test_func):
    """Run a test and report results"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    
    try:
        result = test_func()
        if result:
            print(f"✓ PASSED: {test_name}")
        else:
            print(f"✗ FAILED: {test_name}")
        return result
    except Exception as e:
        print(f"✗ FAILED: {test_name} - Exception: {e}")
        return False

def test_graceful_shutdown():
    """Test graceful shutdown with SIGINT (Ctrl+C)"""
    print("Starting start_all.py...")
    
    # Start the process
    proc = subprocess.Popen(
        [sys.executable, "start_all.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Let it run for a bit
    print("Letting services start up for 10 seconds...")
    time.sleep(10)
    
    # Send SIGINT (Ctrl+C)
    print("\nSending SIGINT to trigger graceful shutdown...")
    proc.send_signal(signal.SIGINT)
    
    # Monitor output
    print("\nMonitoring shutdown output:")
    print("-" * 40)
    
    start_time = time.time()
    cleanup_detected = False
    graceful_complete = False
    
    # Read output with timeout
    def read_output():
        nonlocal cleanup_detected, graceful_complete
        for line in proc.stdout:
            print(f"  {line.rstrip()}")
            if "[CLEANUP]" in line:
                cleanup_detected = True
            if "Subprocess cleanup completed successfully" in line:
                graceful_complete = True
            if "Cleanup Summary:" in line:
                # Read a few more lines to get the summary
                for _ in range(5):
                    try:
                        line = proc.stdout.readline()
                        if line:
                            print(f"  {line.rstrip()}")
                    except:
                        break
    
    # Run output reader in thread with timeout
    reader = threading.Thread(target=read_output)
    reader.daemon = True
    reader.start()
    
    # Wait for process to exit
    try:
        proc.wait(timeout=30)
        shutdown_time = time.time() - start_time
        print("-" * 40)
        print(f"\nProcess exited with code: {proc.returncode}")
        print(f"Shutdown took: {shutdown_time:.1f} seconds")
        
        # Check results
        if proc.returncode == 0 and cleanup_detected and graceful_complete:
            print("✓ Graceful shutdown completed successfully")
            return True
        else:
            print("✗ Shutdown did not complete gracefully")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n✗ Process did not exit within 30 seconds")
        proc.kill()
        return False

def test_sigterm_shutdown():
    """Test shutdown with SIGTERM"""
    print("Starting start_all.py...")
    
    # Start the process
    proc = subprocess.Popen(
        [sys.executable, "start_all.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Let it run for a bit
    print("Letting services start up for 10 seconds...")
    time.sleep(10)
    
    # Send SIGTERM
    print("\nSending SIGTERM to test termination handling...")
    proc.terminate()
    
    # Monitor output
    print("\nMonitoring shutdown output:")
    print("-" * 40)
    
    cleanup_detected = False
    for line in proc.stdout:
        print(f"  {line.rstrip()}")
        if "[CLEANUP]" in line:
            cleanup_detected = True
        if "Process exited" in line or "terminated with SIGTERM" in line:
            break
    
    # Wait for process to exit
    try:
        proc.wait(timeout=15)
        print("-" * 40)
        print(f"\nProcess exited with code: {proc.returncode}")
        
        if cleanup_detected:
            print("✓ SIGTERM handled with cleanup")
            return True
        else:
            print("✗ SIGTERM did not trigger proper cleanup")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n✗ Process did not exit after SIGTERM")
        proc.kill()
        return False

def test_quick_shutdown():
    """Test very quick shutdown (immediate Ctrl+C after start)"""
    print("Starting start_all.py and immediately sending SIGINT...")
    
    # Start the process
    proc = subprocess.Popen(
        [sys.executable, "start_all.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Send SIGINT almost immediately
    time.sleep(2)
    print("\nSending SIGINT after only 2 seconds...")
    proc.send_signal(signal.SIGINT)
    
    # Monitor output
    print("\nMonitoring shutdown output:")
    print("-" * 40)
    
    for line in proc.stdout:
        print(f"  {line.rstrip()}")
        if "Cleanup Summary:" in line:
            # Read a few more lines to get the summary
            for _ in range(5):
                try:
                    line = proc.stdout.readline()
                    if line:
                        print(f"  {line.rstrip()}")
                except:
                    break
            break
    
    # Wait for process to exit
    try:
        proc.wait(timeout=15)
        print("-" * 40)
        print(f"\nProcess exited with code: {proc.returncode}")
        
        if proc.returncode == 0:
            print("✓ Quick shutdown handled successfully")
            return True
        else:
            print("✗ Quick shutdown failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n✗ Process did not exit quickly")
        proc.kill()
        return False

def check_no_orphaned_processes():
    """Check that no Chrome processes are left running on managed ports"""
    print("\nChecking for orphaned Chrome processes...")
    
    # Check for Chrome processes on ports 9223+
    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True
    )
    
    orphaned = []
    for line in result.stdout.split('\n'):
        if "remote-debugging-port=" in line and "tradovate" in line.lower():
            # Extract port
            import re
            port_match = re.search(r'remote-debugging-port=(\d+)', line)
            if port_match:
                port = int(port_match.group(1))
                if port >= 9223:  # Managed ports only
                    orphaned.append(line.strip())
    
    if orphaned:
        print(f"✗ Found {len(orphaned)} orphaned Chrome processes:")
        for proc in orphaned:
            print(f"  {proc[:100]}...")
        return False
    else:
        print("✓ No orphaned Chrome processes found")
        return True

def main():
    """Run all cleanup tests"""
    print("Robust Subprocess Cleanup Test Suite")
    print("====================================")
    print("This will test the new cleanup implementation")
    print("\nNote: This will start and stop Chrome instances multiple times")
    
    # Kill any existing processes first
    print("\nCleaning up any existing processes...")
    subprocess.run(["pkill", "-f", "start_all.py"], capture_output=True)
    subprocess.run(["pkill", "-f", "auto_login.py"], capture_output=True)
    time.sleep(2)
    
    # Run tests
    results = []
    
    results.append(run_test("Graceful Shutdown (SIGINT)", test_graceful_shutdown))
    time.sleep(5)  # Wait between tests
    
    results.append(run_test("SIGTERM Shutdown", test_sigterm_shutdown))
    time.sleep(5)
    
    results.append(run_test("Quick Shutdown", test_quick_shutdown))
    time.sleep(5)
    
    results.append(run_test("No Orphaned Processes", check_no_orphaned_processes))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests PASSED! The robust cleanup is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} tests FAILED. Please review the cleanup implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
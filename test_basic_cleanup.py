#!/usr/bin/env python3
"""
Basic test to verify the cleanup mechanism works
"""
import subprocess
import sys
import time
import signal

print("Basic Cleanup Test")
print("==================")
print("This will start start_all.py and test graceful shutdown\n")

# Start the process
print("Starting start_all.py with short wait time...")
proc = subprocess.Popen(
    [sys.executable, "start_all.py", "--background", "--wait", "3"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1  # Line buffered
)

print(f"Process started with PID: {proc.pid}")
print("\nOutput from start_all.py:")
print("-" * 50)

# Monitor output in real-time
start_time = time.time()
lines_shown = 0

try:
    # Show output for 8 seconds
    while time.time() - start_time < 8:
        if proc.poll() is not None:
            print(f"\nProcess exited early with code: {proc.returncode}")
            break
            
        # Non-blocking read
        line = proc.stdout.readline()
        if line:
            print(f"  {line.rstrip()}")
            lines_shown += 1
            
        # Brief sleep to avoid CPU spinning
        time.sleep(0.01)
    
    if proc.poll() is None:
        print("\n" + "-" * 50)
        print("\nSending SIGINT (Ctrl+C) to test graceful shutdown...")
        proc.send_signal(signal.SIGINT)
        
        print("\nShutdown output:")
        print("-" * 50)
        
        # Read remaining output
        shutdown_start = time.time()
        while True:
            if proc.poll() is not None:
                break
                
            line = proc.stdout.readline()
            if line:
                print(f"  {line.rstrip()}")
            else:
                # Check timeout
                if time.time() - shutdown_start > 30:
                    print("\nTimeout waiting for shutdown!")
                    break
                time.sleep(0.01)
        
        # Final status
        print("-" * 50)
        if proc.poll() is not None:
            print(f"\nProcess exited with code: {proc.returncode}")
            shutdown_time = time.time() - shutdown_start
            print(f"Shutdown took: {shutdown_time:.1f} seconds")
            
            if proc.returncode == 0:
                print("\n✓ Graceful shutdown completed successfully!")
            else:
                print("\n✗ Process exited with non-zero code")
        else:
            print("\n✗ Process did not exit, forcing kill...")
            proc.kill()
            
except Exception as e:
    print(f"\nError during test: {e}")
    if proc.poll() is None:
        proc.kill()
        
finally:
    # Make sure process is dead
    if proc.poll() is None:
        proc.kill()
    proc.wait()

print("\nTest complete!")
#!/usr/bin/env python3
"""Simple PID tracking for process cleanup"""
import os
import json
import signal
import tempfile
from pathlib import Path

# Single shared PID file for all processes
PID_FILE = Path(tempfile.gettempdir()) / "tradovate_pids.json"


def add_pid(pid, process_type="unknown"):
    """Add a PID to the tracking file"""
    pids = load_pids()
    pids[str(pid)] = process_type
    save_pids(pids)
    print(f"[PID_TRACKER] Added {process_type} (PID: {pid})")


def load_pids():
    """Load PIDs from file"""
    try:
        if PID_FILE.exists():
            return json.loads(PID_FILE.read_text())
    except:
        pass
    return {}


def save_pids(pids):
    """Save PIDs to file"""
    try:
        PID_FILE.write_text(json.dumps(pids, indent=2))
    except:
        pass


def kill_all_pids():
    """Kill all tracked PIDs"""
    pids = load_pids()
    if not pids:
        print("[CLEANUP] No PIDs to kill")
        return
        
    print(f"\n[CLEANUP] Killing {len(pids)} tracked processes...")
    
    for pid_str, process_type in pids.items():
        try:
            pid = int(pid_str)
            os.kill(pid, signal.SIGKILL)
            print(f"[CLEANUP] Killed {process_type} (PID: {pid})")
        except ProcessLookupError:
            print(f"[CLEANUP] {process_type} (PID: {pid}) already dead")
        except Exception as e:
            print(f"[CLEANUP] Error killing {process_type} (PID: {pid}): {e}")
    
    # Clear the PID file
    try:
        PID_FILE.unlink()
        print("[CLEANUP] PID file cleared")
    except:
        pass


def cleanup_and_exit(sig=None, frame=None):
    """Signal handler that kills all PIDs and exits"""
    if sig:
        print(f"\n[CLEANUP] Received signal {sig}")
    kill_all_pids()
    print("[CLEANUP] Exiting...")
    os._exit(0)


def setup_signal_handler():
    """Setup signal handler that kills all PIDs on Ctrl+C"""
    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)
    print("[PID_TRACKER] Signal handlers installed")
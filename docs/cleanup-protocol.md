# Robust Subprocess Cleanup Protocol

## Overview

This document describes the enhanced cleanup protocol implemented for the Tradovate Interface to ensure all daemon threads are properly stopped when the application shuts down. This addresses the issue where monitor threads would continue running after Chrome processes terminated, causing "Error checking login status: Tab has been stopped" messages.

## Architecture

### 1. Event-Based Coordination

- **Global shutdown event**: `shutdown_event` in auto_login.py signals all threads to stop
- **Instance-specific events**: Each ChromeInstance has its own `stop_event` for targeted shutdown
- **Thread termination**: Monitor threads use `event.wait()` instead of `time.sleep()` for responsive shutdown

### 2. Status File Communication

- **Temporary status file**: Created by auto_login.py to communicate cleanup progress
- **Path sharing**: Status file path printed to stdout with prefix "CLEANUP_STATUS_FILE:"
- **Progress tracking**: JSON file tracks:
  - `instances_total`: Total Chrome instances to stop
  - `instances_stopped`: Chrome instances successfully stopped
  - `threads_total`: Total monitor threads to stop
  - `threads_stopped`: Monitor threads successfully stopped
  - `cleanup_complete`: Boolean indicating cleanup is finished

### 3. Signal Handling

- **SIGINT (Ctrl+C)**: Graceful shutdown request
- **SIGTERM**: Standard termination request
- **Signal handlers**: Set `shutdown_event` and let main loop handle cleanup

## Cleanup Flow

### Phase 1: Graceful Shutdown Request

1. start_all.py sends SIGINT to auto_login subprocess
2. auto_login.py signal handler sets global shutdown event
3. Monitor threads detect shutdown event and exit their loops
4. ChromeInstance.stop() called for each instance

### Phase 2: Progress Monitoring

1. start_all.py polls the cleanup status file every 500ms
2. Displays real-time progress: "instances stopped, threads stopped"
3. Waits up to 20 seconds for graceful cleanup completion

### Phase 3: Fallback Escalation

If graceful cleanup times out:
1. Send SIGTERM to auto_login process (5 second timeout)
2. If SIGTERM fails, send SIGKILL to force termination
3. Clean up any remaining Chrome processes on managed ports (9223+)

## Timing Expectations

- **Graceful cleanup**: 20 seconds maximum
- **SIGTERM timeout**: 5 seconds
- **Total worst case**: ~25-30 seconds for complete cleanup
- **Typical case**: 2-5 seconds for graceful shutdown

## Logging

Enhanced logging with [CLEANUP] prefix provides visibility into:
- Cleanup phases and progress
- Instance and thread termination status
- Signal handling events
- Final cleanup summary with counts

## Port Management

- **Port 9222**: Protected, never terminated by cleanup
- **Ports 9223+**: Managed ports, terminated during cleanup
- **Dashboard port 9321**: Special port for dashboard Chrome window

## Testing Considerations

The cleanup protocol handles various scenarios:
- Normal shutdown (Ctrl+C during operation)
- Quick shutdown (immediate Ctrl+C after start)
- SIGTERM from process managers
- Hanging threads that don't respond to events
- Multiple Chrome instances with different states

## Known Issues

1. **Existing Chrome on port 9222**: If Chrome is already running on the protected port, auto_login may connect to it instead of creating new instances. This can interfere with cleanup testing.

2. **Orphaned threads**: While the new protocol significantly reduces orphaned threads, network issues or Chrome crashes may still occasionally leave threads running.

## Usage Notes

- Always use Ctrl+C for graceful shutdown when possible
- Monitor logs for [CLEANUP] messages to verify proper shutdown
- Check for orphaned processes with: `ps aux | grep -E "Chrome.*remote-debugging-port"`
- The cleanup status file is automatically removed after successful cleanup
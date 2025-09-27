#!/usr/bin/env python3
"""
Refresh all Chrome tabs showing http://localhost:6001.
Uses AppleScript on macOS for a simpler approach.
"""

import subprocess
import sys
import platform

def refresh_tabs_macos():
    """Refresh localhost:6001 tabs on macOS using AppleScript."""
    applescript = '''
    tell application "Google Chrome"
        set refreshed_count to 0
        set tab_count to 0
        
        -- Loop through all windows
        repeat with w in windows
            -- Loop through all tabs in each window
            repeat with t in tabs of w
                set tab_count to tab_count + 1
                set tab_url to URL of t
                
                -- Check if URL starts with http://localhost:6001
                if tab_url starts with "http://localhost:6001" then
                    -- Reload the tab
                    tell t to reload
                    set refreshed_count to refreshed_count + 1
                    
                    -- Log which tab was refreshed
                    log "Refreshed: " & (title of t) & " [" & tab_url & "]"
                end if
            end repeat
        end repeat
        
        -- Return results
        return "Checked " & tab_count & " tabs, refreshed " & refreshed_count & " localhost:6001 tabs"
    end tell
    '''
    
    try:
        # Execute AppleScript
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("Chrome Tab Refresh Results:")
        print(result.stdout)
        
        # Also capture any logged messages
        if result.stderr:
            print("\nRefreshed tabs:")
            for line in result.stderr.strip().split('\n'):
                if line:
                    print(f"  - {line}")
        
        return 0
    except subprocess.CalledProcessError as e:
        print(f"!!! ERROR !!!")
        print(f"Failed to refresh Chrome tabs: {e}")
        print(f"Error output: {e.stderr}")
        return 1
    except Exception as e:
        print(f"!!! ERROR !!!")
        print(f"Unexpected error: {e}")
        return 1

def refresh_tabs_windows():
    """Refresh localhost:6001 tabs on Windows (placeholder)."""
    print("Windows support not yet implemented.")
    print("Please use Chrome DevTools or manually refresh the tabs.")
    return 1

def refresh_tabs_linux():
    """Refresh localhost:6001 tabs on Linux (placeholder)."""
    print("Linux support not yet implemented.")
    print("Please use Chrome DevTools or manually refresh the tabs.")
    return 1

def main():
    """Main entry point."""
    print("Refreshing all Chrome tabs with http://localhost:6001...")
    
    # Detect platform and use appropriate method
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return refresh_tabs_macos()
    elif system == "Windows":
        return refresh_tabs_windows()
    elif system == "Linux":
        return refresh_tabs_linux()
    else:
        print(f"Unsupported platform: {system}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
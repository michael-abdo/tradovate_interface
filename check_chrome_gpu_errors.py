#!/usr/bin/env python3
"""
Quick script to check for Chrome GPU errors and provide recommendations
"""
import subprocess
import json
import datetime

def check_chrome_gpu_flags():
    """Check if Chrome is running with GPU stability flags"""
    try:
        # Get Chrome processes
        result = subprocess.run(
            ['ps', 'aux'], 
            capture_output=True, 
            text=True
        )
        
        chrome_processes = [line for line in result.stdout.split('\n') 
                          if 'Google Chrome' in line and '--remote-debugging-port' in line]
        
        gpu_flags = [
            '--disable-gpu-sandbox',
            '--disable-software-rasterizer',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-gpu-compositing'
        ]
        
        print("=" * 80)
        print("CHROME GPU ERROR ANALYSIS")
        print("=" * 80)
        print(f"Timestamp: {datetime.datetime.now()}")
        print()
        
        if not chrome_processes:
            print("❌ No Chrome processes found with remote debugging enabled")
            return
            
        for proc in chrome_processes:
            if 'Helper' not in proc:  # Main Chrome process
                print("Chrome Process Found:")
                print("-" * 40)
                
                # Check for GPU flags
                missing_flags = []
                for flag in gpu_flags:
                    if flag not in proc:
                        missing_flags.append(flag)
                
                if missing_flags:
                    print("⚠️  MISSING GPU STABILITY FLAGS:")
                    for flag in missing_flags:
                        print(f"   - {flag}")
                    print()
                    print("🔧 RECOMMENDATION:")
                    print("   Chrome is NOT running with GPU crash prevention flags!")
                    print("   To fix GPU crashes, restart Chrome using the updated auto_login.py")
                    print()
                    print("   Steps to fix:")
                    print("   1. Stop current Chrome: pkill -f 'remote-debugging-port'")
                    print("   2. Restart with: python3 src/auto_login.py")
                    print()
                else:
                    print("✅ All GPU stability flags are present")
                    print()
                
        # Check system logs for recent GPU errors
        print("\nRecent GPU Errors (last 5 minutes):")
        print("-" * 40)
        
        # Get logs from last 5 minutes
        five_min_ago = (datetime.datetime.now() - datetime.timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        
        log_cmd = [
            'log', 'show',
            '--predicate', 'process == "Google Chrome" AND (eventMessage CONTAINS "GPU" OR eventMessage CONTAINS "SharedImage")',
            '--start', five_min_ago,
            '--style', 'json'
        ]
        
        try:
            result = subprocess.run(log_cmd, capture_output=True, text=True, timeout=5)
            if result.stdout:
                logs = json.loads(result.stdout)
                if logs:
                    print(f"Found {len(logs)} GPU-related errors")
                    for log in logs[:5]:  # Show first 5
                        print(f"   {log.get('timestamp', '')} - {log.get('eventMessage', '')}")
                else:
                    print("✅ No GPU errors found in recent logs")
            else:
                print("✅ No GPU errors found in recent logs")
        except Exception as e:
            print(f"Could not check system logs: {e}")
            
        print()
        print("=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        print("The GPU crashes are happening because Chrome is running WITHOUT")
        print("the necessary GPU stability flags. The auto_login.py has been")
        print("updated with these flags, but Chrome needs to be restarted.")
        print()
        print("Quick fix command:")
        print("  pkill -f 'remote-debugging-port' && python3 src/auto_login.py")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error checking Chrome: {e}")

if __name__ == "__main__":
    check_chrome_gpu_flags()
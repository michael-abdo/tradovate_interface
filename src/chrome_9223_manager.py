#!/usr/bin/env python3
"""
Chrome 9223 Manager - Handles the dedicated Chrome instance on port 9223
"""
import os
import sys
import time
import signal
import subprocess
import requests
import json
from pathlib import Path

class Chrome9223Manager:
    def __init__(self):
        self.port = 9223
        self.chrome_process = None
        self.user_data_dir = "/tmp/chrome-debug-9223"
        self.chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
    def is_running(self):
        """Check if Chrome is already running on port 9223"""
        try:
            response = requests.get(f"http://localhost:{self.port}/json/version", timeout=2)
            return response.status_code == 200
        except:
            return False
            
    def start_chrome(self):
        """Start Chrome on port 9223 if not already running"""
        if self.is_running():
            print(f"✅ Chrome already running on port {self.port}")
            return True
            
        print(f"🚀 Starting Chrome on port {self.port}...")
        
        # Clean up any old data directory
        if os.path.exists(self.user_data_dir):
            import shutil
            shutil.rmtree(self.user_data_dir, ignore_errors=True)
            
        # Chrome startup arguments
        chrome_args = [
            self.chrome_path,
            f"--remote-debugging-port={self.port}",
            "--no-first-run",
            "--no-default-browser-check", 
            f"--user-data-dir={self.user_data_dir}",
            "--disable-blink-features=AutomationControlled",
            "--disable-features=VizDisplayCompositor",
            "--password-store=basic",
            "--use-mock-keychain",
            "--disable-extensions",
            "--disable-plugins",
            "--window-size=1200,800",
            "--window-position=100,100"
            # Removed --headless=new so you can see the Chrome window
        ]
        
        try:
            # Start Chrome process
            self.chrome_process = subprocess.Popen(
                chrome_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Wait for Chrome to start
            for attempt in range(10):
                time.sleep(1)
                if self.is_running():
                    print(f"✅ Chrome started successfully on port {self.port} (PID: {self.chrome_process.pid})")
                    return True
                    
            print(f"❌ Chrome failed to start on port {self.port}")
            return False
            
        except Exception as e:
            print(f"❌ Error starting Chrome: {e}")
            return False
            
    def create_tradovate_tab(self):
        """Create a new tab and navigate to Tradovate"""
        if not self.is_running():
            print("❌ Chrome is not running on port 9223")
            return False
            
        try:
            # Create new tab with Tradovate URL
            response = requests.put(
                f"http://localhost:{self.port}/json/new?https://trader.tradovate.com/welcome",
                timeout=5
            )
            
            if response.status_code == 200:
                tab_info = response.json()
                print(f"✅ Created Tradovate tab: {tab_info.get('id', 'Unknown ID')}")
                return True
            else:
                print(f"❌ Failed to create tab: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating Tradovate tab: {e}")
            return False
            
    def stop_chrome(self):
        """Stop the Chrome process"""
        if self.chrome_process:
            try:
                # Terminate the entire process group
                os.killpg(os.getpgid(self.chrome_process.pid), signal.SIGTERM)
                self.chrome_process.wait(timeout=5)
                print(f"✅ Chrome stopped (PID: {self.chrome_process.pid})")
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop gracefully
                os.killpg(os.getpgid(self.chrome_process.pid), signal.SIGKILL)
                print(f"🔨 Chrome force-killed (PID: {self.chrome_process.pid})")
            except Exception as e:
                print(f"⚠️  Error stopping Chrome: {e}")
            finally:
                self.chrome_process = None
        else:
            # Try to find and kill Chrome process by port
            try:
                import psutil
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                            cmdline = proc.info['cmdline']
                            if cmdline and f'--remote-debugging-port={self.port}' in ' '.join(cmdline):
                                print(f"🔍 Found Chrome process (PID: {proc.info['pid']})")
                                proc.terminate()
                                proc.wait(timeout=5)
                                print(f"✅ Chrome stopped (PID: {proc.info['pid']})")
                                return
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                print(f"⚠️  No Chrome process found on port {self.port}")
            except ImportError:
                # Fallback to pkill if psutil is not available
                result = subprocess.run([
                    'pkill', '-f', f'remote-debugging-port={self.port}'
                ], capture_output=True)
                if result.returncode == 0:
                    print(f"✅ Chrome stopped (using pkill)")
                else:
                    print(f"⚠️  No Chrome process found on port {self.port}")
                
    def get_status(self):
        """Get Chrome status information"""
        if not self.is_running():
            return {
                "running": False,
                "port": self.port,
                "message": f"Chrome not running on port {self.port}"
            }
            
        try:
            # Get Chrome version info
            response = requests.get(f"http://localhost:{self.port}/json/version", timeout=2)
            version_info = response.json()
            
            # Get tab list
            tabs_response = requests.get(f"http://localhost:{self.port}/json", timeout=2)
            tabs = tabs_response.json()
            
            # Count Tradovate tabs
            tradovate_tabs = [tab for tab in tabs if "tradovate" in tab.get("url", "").lower()]
            
            return {
                "running": True,
                "port": self.port,
                "browser": version_info.get("Browser", "Unknown"),
                "total_tabs": len(tabs),
                "tradovate_tabs": len(tradovate_tabs),
                "user_data_dir": self.user_data_dir,
                "process_id": self.chrome_process.pid if self.chrome_process else "Unknown"
            }
            
        except Exception as e:
            return {
                "running": True,
                "port": self.port,
                "error": str(e)
            }

def main():
    """CLI interface for Chrome 9223 Manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chrome 9223 Manager")
    parser.add_argument("action", choices=["start", "stop", "status", "restart"], 
                       help="Action to perform")
    
    args = parser.parse_args()
    manager = Chrome9223Manager()
    
    if args.action == "start":
        success = manager.start_chrome()
        if success:
            manager.create_tradovate_tab()
        return 0 if success else 1
        
    elif args.action == "stop":
        manager.stop_chrome()
        return 0
        
    elif args.action == "status":
        status = manager.get_status()
        print(json.dumps(status, indent=2))
        return 0
        
    elif args.action == "restart":
        manager.stop_chrome()
        time.sleep(2)
        success = manager.start_chrome()
        if success:
            manager.create_tradovate_tab()
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
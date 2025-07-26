#!/usr/bin/env python3
"""
Chrome Cleanup Script - Safely clean up Chrome processes and locks
Protects port 9222 from any modifications
"""

import os
import signal
import time
import psutil
import shutil
from pathlib import Path
from typing import List, Dict


class ChromeCleanup:
    def __init__(self, protected_ports: List[int] = [9222]):
        self.protected_ports = protected_ports
        self.debug_ports = [9223, 9224]
        self.cleanup_log = []
        
    def log(self, message: str, level: str = "info"):
        """Log cleanup actions"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"
        self.cleanup_log.append(log_entry)
        print(log_entry)
    
    def find_chrome_processes(self) -> List[Dict]:
        """Find all Chrome processes with debug ports"""
        chrome_processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        
                        # Look for remote debugging port
                        if '--remote-debugging-port=' in cmdline:
                            port_str = cmdline.split('--remote-debugging-port=')[1].split()[0]
                            try:
                                port = int(port_str)
                                
                                # Skip protected ports
                                if port in self.protected_ports:
                                    self.log(f"Skipping protected port {port} (PID: {proc.info['pid']})", "warning")
                                    continue
                                
                                chrome_processes.append({
                                    'pid': proc.info['pid'],
                                    'port': port,
                                    'cmdline': cmdline,
                                    'created': time.time() - proc.info['create_time']
                                })
                            except ValueError:
                                self.log(f"Invalid port value: {port_str}", "error")
                                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
        except Exception as e:
            self.log(f"Error finding Chrome processes: {e}", "error")
        
        return chrome_processes
    
    def kill_chrome_process(self, pid: int, port: int) -> bool:
        """Safely kill a Chrome process"""
        try:
            proc = psutil.Process(pid)
            
            # Try graceful termination first
            self.log(f"Terminating Chrome process PID {pid} on port {port}")
            proc.terminate()
            
            # Wait up to 5 seconds for graceful shutdown
            try:
                proc.wait(timeout=5)
                self.log(f"Process {pid} terminated gracefully")
                return True
            except psutil.TimeoutExpired:
                # Force kill if graceful termination failed
                self.log(f"Force killing process {pid} (graceful termination timeout)")
                proc.kill()
                proc.wait(timeout=5)
                self.log(f"Process {pid} force killed")
                return True
                
        except psutil.NoSuchProcess:
            self.log(f"Process {pid} no longer exists")
            return True
        except Exception as e:
            self.log(f"Error killing process {pid}: {e}", "error")
            return False
    
    def clean_chrome_profiles(self) -> int:
        """Clean up temporary Chrome profile directories"""
        cleaned_count = 0
        temp_dirs = [
            "/tmp",
            "/var/folders",
            "/Users/Mike/trading/temp"
        ]
        
        profile_patterns = [
            "chrome-debug-*",
            "chrome-dev-profile-*",
            "chrome-watchdog-test*",
            "chrome_debug_*",
            "tradovate_debug_profile_*"
        ]
        
        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue
                
            for pattern in profile_patterns:
                # Skip protected port profiles
                skip_patterns = [f"*_{port}" for port in self.protected_ports]
                
                try:
                    temp_path = Path(temp_dir)
                    for profile_dir in temp_path.glob(pattern):
                        # Check if this is a protected profile
                        is_protected = False
                        for skip_pattern in skip_patterns:
                            if profile_dir.match(skip_pattern):
                                is_protected = True
                                self.log(f"Skipping protected profile: {profile_dir}", "warning")
                                break
                        
                        if is_protected:
                            continue
                        
                        # Check if directory is old (> 1 hour)
                        try:
                            age_hours = (time.time() - profile_dir.stat().st_mtime) / 3600
                            if age_hours > 1:
                                self.log(f"Removing old Chrome profile: {profile_dir} (age: {age_hours:.1f} hours)")
                                shutil.rmtree(profile_dir)
                                cleaned_count += 1
                            else:
                                self.log(f"Keeping recent profile: {profile_dir} (age: {age_hours:.1f} hours)")
                        except Exception as e:
                            self.log(f"Error checking profile age: {e}", "error")
                            
                except Exception as e:
                    self.log(f"Error cleaning profiles in {temp_dir}: {e}", "error")
        
        return cleaned_count
    
    def clean_lock_files(self) -> int:
        """Clean up Chrome lock files"""
        cleaned_count = 0
        lock_patterns = [
            "SingletonLock",
            "SingletonSocket",
            "SingletonCookie",
            ".parentlock",
            "lockfile"
        ]
        
        profile_dirs = []
        
        # Find all Chrome profile directories
        for temp_dir in ["/tmp", "/var/folders"]:
            if os.path.exists(temp_dir):
                temp_path = Path(temp_dir)
                profile_dirs.extend(temp_path.glob("chrome*"))
                profile_dirs.extend(temp_path.glob("tradovate_debug_profile_*"))
        
        for profile_dir in profile_dirs:
            # Skip protected profiles
            is_protected = False
            for port in self.protected_ports:
                if str(port) in str(profile_dir):
                    is_protected = True
                    break
            
            if is_protected:
                continue
            
            # Look for lock files
            for lock_pattern in lock_patterns:
                for lock_file in profile_dir.rglob(lock_pattern):
                    try:
                        # Check if lock file is stale (> 10 minutes old)
                        age_minutes = (time.time() - lock_file.stat().st_mtime) / 60
                        if age_minutes > 10:
                            self.log(f"Removing stale lock file: {lock_file} (age: {age_minutes:.1f} minutes)")
                            lock_file.unlink()
                            cleaned_count += 1
                    except Exception as e:
                        self.log(f"Error removing lock file {lock_file}: {e}", "error")
        
        return cleaned_count
    
    def perform_cleanup(self, kill_processes: bool = True, clean_profiles: bool = True, clean_locks: bool = True) -> Dict:
        """Perform comprehensive Chrome cleanup"""
        self.log("Starting Chrome cleanup...")
        results = {
            'processes_found': 0,
            'processes_killed': 0,
            'profiles_cleaned': 0,
            'locks_cleaned': 0
        }
        
        # Find and kill Chrome processes
        if kill_processes:
            chrome_processes = self.find_chrome_processes()
            results['processes_found'] = len(chrome_processes)
            
            if chrome_processes:
                self.log(f"Found {len(chrome_processes)} Chrome debug processes")
                for proc in chrome_processes:
                    self.log(f"  PID {proc['pid']} on port {proc['port']} (age: {proc['created']:.1f}s)")
                
                # Kill processes
                for proc in chrome_processes:
                    if proc['port'] in self.debug_ports:
                        if self.kill_chrome_process(proc['pid'], proc['port']):
                            results['processes_killed'] += 1
                    else:
                        self.log(f"Skipping unknown port {proc['port']}", "warning")
            else:
                self.log("No Chrome debug processes found")
        
        # Clean Chrome profiles
        if clean_profiles:
            self.log("\nCleaning Chrome profiles...")
            results['profiles_cleaned'] = self.clean_chrome_profiles()
            self.log(f"Cleaned {results['profiles_cleaned']} Chrome profiles")
        
        # Clean lock files
        if clean_locks:
            self.log("\nCleaning Chrome lock files...")
            results['locks_cleaned'] = self.clean_lock_files()
            self.log(f"Cleaned {results['locks_cleaned']} lock files")
        
        # Summary
        self.log("\n" + "="*50)
        self.log("CLEANUP SUMMARY:")
        self.log(f"  Chrome processes found: {results['processes_found']}")
        self.log(f"  Chrome processes killed: {results['processes_killed']}")
        self.log(f"  Chrome profiles cleaned: {results['profiles_cleaned']}")
        self.log(f"  Lock files cleaned: {results['locks_cleaned']}")
        self.log("="*50)
        
        return results
    
    def save_log(self, filename: str = "chrome_cleanup.log"):
        """Save cleanup log to file"""
        with open(filename, 'w') as f:
            f.write('\n'.join(self.cleanup_log))
        self.log(f"Log saved to {filename}")


def main():
    """CLI for Chrome cleanup"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chrome Cleanup Tool")
    parser.add_argument('--no-kill', action='store_true', help="Don't kill Chrome processes")
    parser.add_argument('--no-profiles', action='store_true', help="Don't clean Chrome profiles")
    parser.add_argument('--no-locks', action='store_true', help="Don't clean lock files")
    parser.add_argument('--dry-run', action='store_true', help="Show what would be done without making changes")
    parser.add_argument('--save-log', help="Save cleanup log to file")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    
    cleanup = ChromeCleanup()
    
    if args.dry_run:
        # Just show what would be done
        chrome_processes = cleanup.find_chrome_processes()
        if chrome_processes:
            print(f"Would kill {len(chrome_processes)} Chrome processes:")
            for proc in chrome_processes:
                print(f"  PID {proc['pid']} on port {proc['port']}")
    else:
        # Perform actual cleanup
        cleanup.perform_cleanup(
            kill_processes=not args.no_kill,
            clean_profiles=not args.no_profiles,
            clean_locks=not args.no_locks
        )
    
    if args.save_log:
        cleanup.save_log(args.save_log)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script Watcher - Layer 2 of the script reloader system
Watches for changes to .user.js files and triggers script injection via CDP
"""

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import time
import threading  
import logging

class ScriptFileHandler(FileSystemEventHandler):
    """
    🔍 LAYER 2: File System Event Handler for .user.js files
    Handles file system events and triggers callbacks for script changes
    """
    
    def __init__(self, callback=None):
        """Initialize the event handler with callback function
        
        Args:
            callback (callable): Function to call when .user.js files change
        """
        super().__init__()
        self.callback = callback
        print("🔍 LAYER 2: ScriptFileHandler initialized")
        print(f"🔍 LAYER 2: Callback function: {'SET' if callback else 'NOT SET'}")
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return  # Ignore directory changes
            
        file_path = event.src_path
        
        # Only process .user.js files
        if not file_path.endswith('.user.js'):
            return
            
        print(f"🔍 LAYER 2: File modified detected: {file_path}")
        
        # Extract filename for logging
        filename = os.path.basename(file_path)
        print(f"🔍 LAYER 2: Processing userscript: {filename}")
        
        # Special logging for critical autoOrder.user.js
        if 'autoOrder' in filename.lower():
            print(f"🔥 LAYER 2: CRITICAL FILE MODIFIED - {filename}")
            print(f"🔥 LAYER 2: Trading script update detected!")
        else:
            print(f"📄 LAYER 2: Standard userscript modified - {filename}")
        
        # Execute callback if available
        if self.callback:
            try:
                print(f"🔍 LAYER 2: Triggering callback for {filename}")
                self.callback(file_path)
                print(f"✅ LAYER 2: Callback executed successfully for {filename}")
            except Exception as e:
                print(f"🔴 LAYER 2: ERROR - Callback failed for {filename}: {e}")
        else:
            print(f"⚠️ LAYER 2: WARNING - No callback set for {filename}")

class ScriptWatcher:
    """
    🔍 LAYER 2: File System Watcher for Tampermonkey Scripts
    Watches for changes to .user.js files and triggers script injection
    """
    
    def __init__(self, script_directory=None, callback=None):
        """Initialize the ScriptWatcher with script directory and callback
        
        Args:
            script_directory (str): Directory to watch for .user.js files
            callback (callable): Function to call when files change
        """
        print("🔍 LAYER 2: Initializing ScriptWatcher")
        
        # Set script directory - default to tampermonkey scripts directory
        if script_directory is None:
            # Get project root and default to scripts/tampermonkey
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.script_directory = os.path.join(project_root, 'scripts', 'tampermonkey')
        else:
            self.script_directory = script_directory
            
        # Store callback function for file change notifications
        self.callback = callback
        
        print(f"🔍 LAYER 2: Watching directory: {self.script_directory}")
        print(f"🔍 LAYER 2: Callback function: {'SET' if callback else 'NOT SET'}")
        
        # Validate script directory exists
        if not os.path.exists(self.script_directory):
            print(f"⚠️ LAYER 2: WARNING - Script directory does not exist: {self.script_directory}")
        elif not os.path.isdir(self.script_directory):
            print(f"⚠️ LAYER 2: WARNING - Script path is not a directory: {self.script_directory}")
        else:
            print(f"✅ LAYER 2: Script directory validated")
            
        # Thread management and control flags
        self.is_running = False
        self.observer = None
        self.watch_thread = None
        
        # ChromeLogger registry for Layer 2 → Layer 3 handoff
        self.chrome_loggers = []
        
        print(f"🔍 LAYER 2: Thread management initialized")
        print(f"🔍 LAYER 2: Observer: {self.observer}")
        print(f"🔍 LAYER 2: Running state: {self.is_running}")
        print(f"🔍 LAYER 2: ChromeLogger registry: EMPTY (0 instances)")
    
    def start(self):
        """Start the file system watcher"""
        if self.is_running:
            print("⚠️ LAYER 2: WARNING - ScriptWatcher is already running")
            return False
            
        print("🔍 LAYER 2: Starting ScriptWatcher...")
        
        try:
            # Create the file system event handler with Layer 2 → Layer 3 callback
            event_handler = ScriptFileHandler(callback=self.inject_script_to_all_chrome_loggers)
            
            # Create and configure the observer
            self.observer = Observer()
            self.observer.schedule(event_handler, self.script_directory, recursive=False)
            
            # Start the observer
            self.observer.start()
            self.is_running = True
            
            print(f"✅ LAYER 2: ScriptWatcher started successfully")
            print(f"🔍 LAYER 2: Monitoring directory: {self.script_directory}")
            print(f"🔍 LAYER 2: Watching for .user.js file changes")
            print(f"🔍 LAYER 2: Observer status: ACTIVE")
            
            # List existing .user.js files for reference
            try:
                userscripts = [f for f in os.listdir(self.script_directory) if f.endswith('.user.js')]
                if userscripts:
                    print(f"🔍 LAYER 2: Found {len(userscripts)} userscript(s): {', '.join(userscripts)}")
                    for script in userscripts:
                        if 'autoOrder' in script.lower():
                            print(f"🔥 LAYER 2: CRITICAL SCRIPT DETECTED - {script}")
                else:
                    print(f"🔍 LAYER 2: No .user.js files found in directory")
            except Exception as e:
                print(f"⚠️ LAYER 2: WARNING - Could not list directory contents: {e}")
            
            return True
            
        except Exception as e:
            print(f"🔴 LAYER 2: ERROR - Failed to start ScriptWatcher: {e}")
            self.is_running = False
            self.observer = None
            return False
    
    def stop(self):
        """Stop the file system watcher"""
        if not self.is_running:
            print("⚠️ LAYER 2: WARNING - ScriptWatcher is not running")
            return False
            
        print("🔍 LAYER 2: Stopping ScriptWatcher...")
        
        try:
            # Stop and cleanup the observer
            if self.observer:
                self.observer.stop()
                print("🔍 LAYER 2: Observer stop signal sent")
                
                # Wait for observer to finish (with timeout)
                self.observer.join(timeout=5.0)
                
                if self.observer.is_alive():
                    print("⚠️ LAYER 2: WARNING - Observer did not stop within timeout")
                else:
                    print("✅ LAYER 2: Observer stopped successfully")
                
                self.observer = None
            
            # Reset state flags
            self.is_running = False
            
            print("✅ LAYER 2: ScriptWatcher stopped successfully")
            print("🔍 LAYER 2: Observer status: INACTIVE")
            print("🔍 LAYER 2: Running state: STOPPED")
            
            return True
            
        except Exception as e:
            print(f"🔴 LAYER 2: ERROR - Failed to stop ScriptWatcher: {e}")
            # Force reset state even if error occurred
            self.is_running = False
            self.observer = None
            return False
    
    def add_chrome_logger(self, chrome_logger):
        """
        Add a ChromeLogger to the registry for Layer 2 → Layer 3 handoff
        
        Args:
            chrome_logger: ChromeLogger instance to register
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        if chrome_logger is None:
            print("⚠️ LAYER 2: WARNING - Cannot add None ChromeLogger to registry")
            return False
            
        if chrome_logger in self.chrome_loggers:
            print("⚠️ LAYER 2: WARNING - ChromeLogger already in registry")
            return False
            
        self.chrome_loggers.append(chrome_logger)
        print(f"✅ LAYER 2: ChromeLogger added to registry")
        print(f"🔍 LAYER 2: Registry now has {len(self.chrome_loggers)} ChromeLogger(s)")
        
        return True
    
    def remove_chrome_logger(self, chrome_logger):
        """
        Remove a ChromeLogger from the registry
        
        Args:
            chrome_logger: ChromeLogger instance to remove
            
        Returns:
            bool: True if removed successfully, False otherwise
        """
        if chrome_logger in self.chrome_loggers:
            self.chrome_loggers.remove(chrome_logger)
            print(f"✅ LAYER 2: ChromeLogger removed from registry")
            print(f"🔍 LAYER 2: Registry now has {len(self.chrome_loggers)} ChromeLogger(s)")
            return True
        else:
            print("⚠️ LAYER 2: WARNING - ChromeLogger not found in registry")
            return False
    
    def get_chrome_loggers(self):
        """
        Get the list of active ChromeLoggers
        
        Returns:
            list: List of ChromeLogger instances
        """
        return self.chrome_loggers.copy()
    
    def clear_chrome_loggers(self):
        """Clear all ChromeLoggers from the registry"""
        count = len(self.chrome_loggers)
        self.chrome_loggers.clear()
        print(f"🔍 LAYER 2: Cleared {count} ChromeLogger(s) from registry")
        print(f"🔍 LAYER 2: Registry is now EMPTY")
    
    def inject_script_to_all_chrome_loggers(self, script_file_path):
        """
        🔍→🔥 LAYER 2 → LAYER 3: Inject script to all registered ChromeLoggers
        
        This is the key callback method that bridges file change detection 
        to script injection across all Chrome instances.
        
        Args:
            script_file_path (str): Path to the script file that changed
            
        Returns:
            dict: Result summary with success/failure counts
        """
        filename = os.path.basename(script_file_path)
        
        # Layer 2 → Layer 3 handoff logging
        print(f"🔍→🔥 LAYER 2 → LAYER 3: HANDOFF INITIATED")
        print(f"🔍→🔥 File: {filename}")
        print(f"🔍→🔥 Path: {script_file_path}")
        print(f"🔍→🔥 Target ChromeLoggers: {len(self.chrome_loggers)}")
        
        if not self.chrome_loggers:
            print(f"⚠️ LAYER 2 → LAYER 3: WARNING - No ChromeLoggers registered!")
            print(f"⚠️ Cannot inject {filename} - registry is empty")
            return {'success': 0, 'failed': 0, 'total': 0}
        
        # Special logging for critical files
        if 'autoOrder' in filename.lower():
            print(f"🔥🔥 LAYER 2 → LAYER 3: CRITICAL FILE HANDOFF - {filename}")
            print(f"🔥🔥 Trading script will be injected to ALL Chrome instances!")
        
        # Track injection results
        successful_injections = 0
        failed_injections = 0
        
        # Inject script to all registered ChromeLoggers
        for i, chrome_logger in enumerate(self.chrome_loggers):
            try:
                print(f"🔍→🔥 LAYER 2 → LAYER 3: Injecting to ChromeLogger #{i+1}")
                
                # Validate ChromeLogger before injection
                if chrome_logger is None:
                    print(f"🔴 LAYER 2 → LAYER 3: ERROR - ChromeLogger #{i+1} is None")
                    failed_injections += 1
                    continue
                
                if not hasattr(chrome_logger, 'inject_script'):
                    print(f"🔴 LAYER 2 → LAYER 3: ERROR - ChromeLogger #{i+1} has no inject_script method")
                    failed_injections += 1
                    continue
                
                # Attempt injection
                injection_success = chrome_logger.inject_script(script_file_path)
                
                if injection_success:
                    successful_injections += 1
                    print(f"✅ LAYER 2 → LAYER 3: SUCCESS - ChromeLogger #{i+1} injection complete")
                else:
                    failed_injections += 1
                    print(f"🔴 LAYER 2 → LAYER 3: FAILED - ChromeLogger #{i+1} injection failed")
                    
            except Exception as e:
                failed_injections += 1
                print(f"🔴 LAYER 2 → LAYER 3: ERROR - Exception in ChromeLogger #{i+1}: {e}")
        
        # Summary logging
        total_loggers = len(self.chrome_loggers)
        print(f"🔍→🔥 LAYER 2 → LAYER 3: HANDOFF COMPLETE")
        print(f"📊 Results: {successful_injections} success, {failed_injections} failed, {total_loggers} total")
        
        if successful_injections == total_loggers:
            print(f"🎉 LAYER 2 → LAYER 3: PERFECT SUCCESS - All injections completed!")
            if 'autoOrder' in filename.lower():
                print(f"⭐ CRITICAL SUCCESS - {filename} deployed to ALL trading Chrome instances!")
        elif successful_injections > 0:
            print(f"⚠️ LAYER 2 → LAYER 3: PARTIAL SUCCESS - Some injections failed")
        else:
            print(f"💥 LAYER 2 → LAYER 3: TOTAL FAILURE - No successful injections")
            if 'autoOrder' in filename.lower():
                print(f"🚨 CRITICAL FAILURE - {filename} not deployed to any trading instances!")
        
        return {
            'success': successful_injections,
            'failed': failed_injections, 
            'total': total_loggers
        }
    
# TODO: Add detailed logging for Layer 2 file watcher events
# TODO: Add detailed logging for Layer 2 file watcher events
# TODO: Add on_modified callback method
# TODO: Add file change debouncing
# TODO: Add script file validation
# TODO: Add callback execution with error handling

if __name__ == "__main__":
    print("🚀 LAYER 2: Script Watcher")
    print("TODO: Implement file watching functionality")
#!/usr/bin/env python3
import time
import datetime
import json
import pychrome
from threading import Thread
from pathlib import Path
from src.utils.core import get_project_root, setup_logging
from src.services.scraper_service import get_scraper_service

class ChromeLogger:
    def __init__(self, tab, log_file=None, account_name=None):
        """
        Initialize a logger for Chrome DevTools Protocol
        
        Args:
            tab: The Chrome tab to log from (pychrome tab object)
            log_file: Path to log file (if None, will only use callbacks)
            account_name: Name of the account associated with this tab
        """
        self.tab = tab
        self.log_file = log_file
        self.account_name = account_name or 'Unknown'
        self.callbacks = []
        self.is_running = False
        self.log_thread = None
        self.dom_snapshot_enabled = False
        self.combined_log_entries = []  # Store combined log + DOM data for Claude Code analysis
        
        # Create log file directory if needed
        if log_file:
            log_path = Path(log_file)
            if not log_path.is_absolute():
                log_path = get_project_root() / log_path
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_file = str(log_path)
        else:
            self.log_file = None
    
    def start(self):
        """Start capturing logs from the browser"""
        if self.is_running:
            return
            
        try:
            # Enable various logging domains
            self.tab.Log.enable()
            self.tab.Runtime.enable()
            self.tab.Console.enable()
            self.tab.DOM.enable()  # Enable DOM for snapshot capability
            self.tab.Page.enable()  # Enable Page events
            
            # Set up event listeners
            self.tab.Log.entryAdded = self._on_log_entry
            self.tab.Runtime.consoleAPICalled = self._on_console_api
            self.tab.Runtime.exceptionThrown = self._on_exception
            self.tab.Console.messageAdded = self._on_console_message
            
            # Start background thread for processing logs
            self.is_running = True
            self.log_thread = Thread(target=self._process_logs)
            self.log_thread.daemon = True
            self.log_thread.start()
            
            print("Chrome logger started")
            return True
        except Exception as e:
            print(f"Error starting Chrome logger: {e}")
            return False
    
    def stop(self):
        """Stop the logger and clean up WebSocket connections"""
        self.is_running = False
        
        # Disable CDP domains to stop WebSocket events and avoid blocking
        try:
            if self.tab:
                self.tab.Log.disable()
                self.tab.Runtime.disable()
                self.tab.Console.disable()
                self.tab.DOM.disable()
                self.tab.Page.disable()
                
                # IMPORTANT: Stop the tab to close WebSocket connection
                # This prevents the _recv_loop thread from hanging
                try:
                    self.tab.stop()
                except Exception:
                    pass  # Ignore errors if already stopped
                    
        except Exception as e:
            # Ignore WebSocket errors during cleanup - tab may already be closed
            pass
        
        # Clear the tab reference to prevent further operations
        self.tab = None
        
        # Wait for background thread with shorter timeout to avoid blocking
        if self.log_thread:
            self.log_thread.join(timeout=0.5)
            if self.log_thread.is_alive():
                print(f"Warning: ChromeLogger thread did not stop cleanly within timeout")
            self.log_thread = None
        
        print("Chrome logger stopped")
    
    def add_callback(self, callback):
        """
        Add a callback function that will be called for each log entry
        The callback should accept a dictionary with log information
        """
        self.callbacks.append(callback)
        return len(self.callbacks) - 1  # Return callback index for removal
    
    def remove_callback(self, callback_id):
        """Remove a callback by its ID"""
        if 0 <= callback_id < len(self.callbacks):
            self.callbacks.pop(callback_id)
            return True
        return False
    
    def inject_script(self, script_file_path):
        """
        🔥 LAYER 3: Inject a script file into the Chrome tab via CDP
        
        Args:
            script_file_path (str): Path to the script file to inject
            
        Returns:
            bool: True if injection successful, False otherwise
        """
        print(f"🔥 LAYER 3: CDP Injection requested for: {script_file_path}")
        
        # Validate tab is available
        if not self.tab:
            print(f"🔴 LAYER 3: ERROR - No Chrome tab available for injection")
            return False
            
        # Validate file exists
        script_path = Path(script_file_path)
        if not script_path.exists():
            print(f"🔴 LAYER 3: ERROR - Script file not found: {script_file_path}")
            return False
            
        if not script_path.is_file():
            print(f"🔴 LAYER 3: ERROR - Path is not a file: {script_file_path}")
            return False
            
        # Extract filename for logging
        filename = script_path.name
        print(f"🔥 LAYER 3: Processing script: {filename}")
        
        # Special logging for critical autoOrder.user.js
        if 'autoOrder' in filename.lower():
            print(f"💥 LAYER 3: CRITICAL INJECTION - {filename}")
            print(f"💥 LAYER 3: Trading script injection via CDP!")
        else:
            print(f"📄 LAYER 3: Standard script injection - {filename}")
            
        try:
            # Read script file content
            print(f"🔥 LAYER 3: Reading script content from {filename}")
            with open(script_file_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
                
            if not script_content.strip():
                print(f"⚠️ LAYER 3: WARNING - Script file is empty: {filename}")
                return False
                
            print(f"🔥 LAYER 3: Script content loaded ({len(script_content)} characters)")
            
            # Basic script validation for userscripts
            if script_file_path.endswith('.user.js'):
                if '// ==UserScript==' not in script_content:
                    print(f"⚠️ LAYER 3: WARNING - Missing UserScript header in {filename}")
                else:
                    print(f"✅ LAYER 3: UserScript header validated in {filename}")
            
            # Hot-reload cleanup for autoOrder script
            if 'autoOrder' in filename.lower():
                print(f"🔥 LAYER 3: HOT-RELOAD - Cleaning up existing autoOrder UI")
                cleanup_script = """
                console.log('🔥 HOT RELOAD: Removing old autoOrder UI...');
                let oldUI = document.getElementById('bracket-trade-box');
                if (oldUI) {
                    oldUI.remove();
                    console.log('🔥 HOT RELOAD: Old UI removed');
                }
                // Clear localStorage quantity to force new defaults
                localStorage.removeItem('bracketTrade_qty');
                console.log('🔥 HOT RELOAD: localStorage cleared for fresh defaults');
                """
                cleanup_result = self.tab.Runtime.evaluate(expression=cleanup_script)
                print(f"🔥 LAYER 3: HOT-RELOAD cleanup completed")
            
            # Inject script via Chrome DevTools Protocol
            print(f"🔥 LAYER 3: Executing Runtime.evaluate for {filename}")
            result = self.tab.Runtime.evaluate(expression=script_content)
            
            # Check injection result
            if result.get('wasThrown'):
                error_msg = result.get('result', {}).get('description', 'Unknown error')
                print(f"🔴 LAYER 3: ERROR - Script injection failed for {filename}: {error_msg}")
                return False
            else:
                print(f"✅ LAYER 3: Script injection successful for {filename}")
                
                # Special success logging for critical files
                if 'autoOrder' in filename.lower():
                    print(f"⭐ LAYER 3: CRITICAL SUCCESS - {filename} injected via CDP!")
                    
                return True
                
        except FileNotFoundError:
            print(f"🔴 LAYER 3: ERROR - File not found during read: {filename}")
            return False
        except UnicodeDecodeError as e:
            print(f"🔴 LAYER 3: ERROR - Unicode decode error in {filename}: {e}")
            return False
        except IOError as e:
            print(f"🔴 LAYER 3: ERROR - IO error reading {filename}: {e}")
            return False
        except Exception as e:
            print(f"🔴 LAYER 3: ERROR - CDP injection failed for {filename}: {e}")
            return False
    
    def enable_dom_snapshots(self):
        """
        Enable DOM snapshot capture for comprehensive debugging
        
        When enabled, DOM snapshots will be captured automatically on:
        - Console errors
        - JavaScript exceptions  
        - Critical console.log events (configurable)
        """
        self.dom_snapshot_enabled = True
        print("🔍 DOM Snapshot capture enabled for comprehensive debugging")
    
    def disable_dom_snapshots(self):
        """Disable DOM snapshot capture to reduce overhead"""
        self.dom_snapshot_enabled = False
        print("🔍 DOM Snapshot capture disabled")
        
    def capture_dom_snapshot(self, trigger_event=None):
        """
        Capture complete DOM snapshot using CDP DOMSnapshot domain
        
        Args:
            trigger_event (str): Optional description of what triggered the snapshot
            
        Returns:
            dict: DOM snapshot data or None if failed
        """
        if not self.tab:
            print("🔴 ERROR: No Chrome tab available for DOM snapshot")
            return None
            
        try:
            print(f"🔍 Capturing DOM snapshot{f' (trigger: {trigger_event})' if trigger_event else ''}")
            
            # Capture DOM snapshot with comprehensive data
            snapshot_result = self.tab.DOMSnapshot.captureSnapshot(
                computedStyles=[],  # Include computed styles for elements
                includePaintOrder=True,  # Include paint order information
                includeDOMRects=True,   # Include element positioning rectangles  
                includeBlendedBackgroundColors=True  # Include background color info
            )
            
            if snapshot_result:
                # Add metadata
                snapshot_data = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'trigger_event': trigger_event,
                    'url': self._get_current_url(),
                    'snapshot': snapshot_result
                }
                
                print(f"✅ DOM snapshot captured successfully ({len(str(snapshot_result))} chars)")
                return snapshot_data
            else:
                print("🔴 ERROR: DOM snapshot capture returned empty result")
                return None
                
        except Exception as e:
            print(f"🔴 ERROR: DOM snapshot capture failed: {e}")
            return None
    
    def _get_current_url(self):
        """Get the current page URL"""
        try:
            target_info = self.tab.Target.getTargetInfo(targetId=self.tab.target_id)
            return target_info.get('targetInfo', {}).get('url', 'unknown')
        except Exception:
            return 'unknown'
    
    def get_combined_debug_data(self, include_snapshots=True):
        """
        Get comprehensive debugging data for Claude Code analysis
        
        Args:
            include_snapshots (bool): Whether to include DOM snapshots in output
            
        Returns:
            dict: Combined log entries and DOM snapshots formatted for analysis
        """
        debug_data = {
            'session_info': {
                'timestamp': datetime.datetime.now().isoformat(),
                'url': self._get_current_url(),
                'dom_snapshots_enabled': self.dom_snapshot_enabled,
                'total_log_entries': len(self.combined_log_entries)
            },
            'log_entries': self.combined_log_entries.copy()
        }
        
        if include_snapshots:
            # Filter entries that have DOM snapshots
            entries_with_snapshots = [
                entry for entry in self.combined_log_entries 
                if entry.get('dom_snapshot') is not None
            ]
            debug_data['entries_with_dom_snapshots'] = len(entries_with_snapshots)
        else:
            # Remove DOM snapshot data to reduce size
            for entry in debug_data['log_entries']:
                entry.pop('dom_snapshot', None)
            
        return debug_data
    
    def save_debug_data_for_claude(self, output_file=None):
        """
        Save comprehensive debugging data in a format optimized for Claude Code analysis
        
        Args:
            output_file (str): Optional output file path. If None, auto-generates filename.
            
        Returns:
            str: Path to saved debug data file
        """
        if not output_file:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            if self.log_file:
                log_dir = Path(self.log_file).parent
            else:
                log_dir = get_project_root() / 'logs'
            output_file = log_dir / f'claude_debug_data_{timestamp}.json'
        else:
            output_file = Path(output_file)
            
        # Ensure directory exists
        if not output_file.is_absolute():
            output_file = get_project_root() / output_file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        debug_data = self.get_combined_debug_data(include_snapshots=True)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False)
                
            print(f"💾 Debug data saved for Claude Code analysis: {output_file}")
            print(f"📊 Data includes {len(debug_data['log_entries'])} log entries")
            
            if debug_data.get('entries_with_dom_snapshots', 0) > 0:
                print(f"🔍 Includes {debug_data['entries_with_dom_snapshots']} DOM snapshots")
                
            return str(output_file)
            
        except Exception as e:
            print(f"🔴 ERROR: Failed to save debug data: {e}")
            return None
    
    def _write_to_file(self, entry):
        """Write log entry to file if configured"""
        if not self.log_file:
            return
            
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                f.write(f"[{timestamp}] {entry['level']} - {entry['text']}\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def _process_callbacks(self, entry):
        """Process all registered callbacks"""
        for callback in self.callbacks:
            try:
                callback(entry)
            except Exception as e:
                print(f"Error in callback: {e}")
                import traceback
                traceback.print_exc()
    
    def _on_log_entry(self, **kwargs):
        """Handle Log.entryAdded event"""
        entry = kwargs.get('entry', {})
        log_entry = {
            'source': 'browser',
            'level': entry.get('level', 'INFO'),
            'text': entry.get('text', ''),
            'url': entry.get('url', ''),
            'timestamp': entry.get('timestamp', time.time()),
            'raw': entry
        }
        
        # Capture DOM snapshot for errors if enabled
        if self.dom_snapshot_enabled and entry.get('level') in ['error', 'ERROR']:
            dom_snapshot = self.capture_dom_snapshot(f"Browser error: {entry.get('text', '')[:100]}")
            log_entry['dom_snapshot'] = dom_snapshot
            
        # Add to combined log entries for Claude Code analysis
        self.combined_log_entries.append(log_entry.copy())
        
        self._write_to_file(log_entry)
        self._process_callbacks(log_entry)
    
    def _on_console_api(self, **kwargs):
        """Handle Runtime.consoleAPICalled event"""
        args = kwargs.get('args', [])
        # Fix: Ensure all values are properly converted to strings before joining
        message_parts = []
        for arg in args:
            if 'value' in arg:
                value = arg['value']
                # Convert all types to string safely
                message_parts.append(str(value))
        message = ' '.join(message_parts)
        console_type = kwargs.get('type', 'log').upper()
        
        # Check if this is scraper data
        if message.startswith('[SCRAPER_DATA] '):
            try:
                # Extract JSON data after the marker
                json_str = message[15:]  # Remove '[SCRAPER_DATA] ' prefix
                scraper_data = json.loads(json_str)
                
                # Use the account name from logger instance
                account = self.account_name
                
                # Send to scraper service
                scraper_service = get_scraper_service()
                scraper_service.add_scraped_data(account, scraper_data)
                
                # Log successful capture
                print(f"[Chrome Logger] Captured scraper data from {account}: {len(scraper_data.get('trades', []))} trades")
            except Exception as e:
                print(f"[Chrome Logger] Error parsing scraper data: {e}")
        
        log_entry = {
            'source': 'console',
            'level': console_type,
            'text': message,
            'url': kwargs.get('stackTrace', {}).get('callFrames', [{}])[0].get('url', ''),
            'timestamp': time.time(),
            'raw': kwargs
        }
        
        # Capture DOM snapshot for errors and critical events if enabled
        should_capture_snapshot = False
        if self.dom_snapshot_enabled:
            if console_type in ['ERROR', 'WARN']:
                should_capture_snapshot = True
            elif console_type == 'LOG' and any(keyword in message.lower() for keyword in 
                ['error', 'fail', 'critical', 'exception', 'crash', 'timeout']):
                should_capture_snapshot = True
                
        if should_capture_snapshot:
            dom_snapshot = self.capture_dom_snapshot(f"Console {console_type}: {message[:100]}")
            log_entry['dom_snapshot'] = dom_snapshot
            
        # Add to combined log entries for Claude Code analysis
        self.combined_log_entries.append(log_entry.copy())
        
        self._write_to_file(log_entry)
        self._process_callbacks(log_entry)
    
    def _on_exception(self, **kwargs):
        """Handle Runtime.exceptionThrown event"""
        exception_details = kwargs.get('exceptionDetails', {})
        exception = exception_details.get('exception', {})
        exception_text = f"Exception: {exception.get('description', exception.get('value', 'Unknown error'))}"
        
        log_entry = {
            'source': 'exception',
            'level': 'ERROR',
            'text': exception_text,
            'url': exception_details.get('url', ''),
            'timestamp': time.time(),
            'raw': kwargs
        }
        
        # Always capture DOM snapshot for exceptions if enabled
        if self.dom_snapshot_enabled:
            dom_snapshot = self.capture_dom_snapshot(f"JavaScript Exception: {exception_text[:100]}")
            log_entry['dom_snapshot'] = dom_snapshot
            
        # Add to combined log entries for Claude Code analysis
        self.combined_log_entries.append(log_entry.copy())
        
        self._write_to_file(log_entry)
        self._process_callbacks(log_entry)
    
    def _on_console_message(self, **kwargs):
        """Handle Console.messageAdded event"""
        message = kwargs.get('message', {})
        message_level = message.get('level', 'INFO').upper()
        message_text = message.get('text', '')
        
        log_entry = {
            'source': 'console',
            'level': message_level,
            'text': message_text,
            'url': message.get('url', ''),
            'timestamp': time.time(),
            'raw': kwargs
        }
        
        # Capture DOM snapshot for console messages with errors if enabled
        if self.dom_snapshot_enabled and message_level in ['ERROR', 'WARNING']:
            dom_snapshot = self.capture_dom_snapshot(f"Console {message_level}: {message_text[:100]}")
            log_entry['dom_snapshot'] = dom_snapshot
            
        # Add to combined log entries for Claude Code analysis
        self.combined_log_entries.append(log_entry.copy())
        
        self._write_to_file(log_entry)
        self._process_callbacks(log_entry)
    
    def _process_logs(self):
        """Background thread to process log events"""
        while self.is_running:
            try:
                time.sleep(0.1)  # Prevent excessive CPU usage
            except Exception:
                break


def create_logger(tab, log_file=None, callback=None, account_name=None):
    """
    Create and start a Chrome logger for the given tab
    
    Args:
        tab: Chrome tab object from pychrome
        log_file: Optional file to write logs to
        callback: Optional callback function for log entries
        account_name: Name of the account associated with this tab
        
    Returns:
        ChromeLogger instance if successful, None otherwise
    """
    logger = ChromeLogger(tab, log_file, account_name)
    if callback:
        logger.add_callback(callback)
        
    if logger.start():
        return logger
    return None


def main():
    """Main function for running the Chrome logger as a standalone tool"""
    import sys
    from src import login_helper
    
    # Simple callback to print logs to console
    def print_log(entry):
        level_colors = {
            'DEBUG': '\033[36m',  # Cyan
            'INFO': '\033[32m',   # Green
            'LOG': '\033[32m',    # Green
            'WARNING': '\033[33m', # Yellow
            'ERROR': '\033[31m',  # Red
            'CRITICAL': '\033[41m\033[37m'  # White on red background
        }
        reset = '\033[0m'
        
        level = entry['level']
        color = level_colors.get(level, '')
        print(f"{color}[{level}]{reset} {entry['text']}")
    
    # Connect to Chrome and set up logging
    success, tab, browser = login_helper.login_to_existing_chrome(port=9222)
    
    if success:
        print("Connected to Chrome, setting up logger...")
        log_file = get_project_root() / 'logs' / 'chrome.log'
        logger = create_logger(tab, str(log_file), print_log)
        
        if logger:
            print(f"Logger started, writing to {log_file}")
            print("Press Ctrl+C to exit")
            
            # Run a test script in the browser
            test_js = """
            console.log('Chrome logger test - INFO message');
            console.warn('Chrome logger test - WARNING message');
            console.error('Chrome logger test - ERROR message');
            console.debug('Chrome logger test - DEBUG message');
            """
            tab.Runtime.evaluate(expression=test_js)
            
            # Enable DOM snapshots for comprehensive debugging
            logger.enable_dom_snapshots()
            print("🔍 DOM snapshots enabled for comprehensive debugging")
            
            # Test DOM snapshot capture
            print("🧪 Testing DOM snapshot capture...")
            snapshot = logger.capture_dom_snapshot("Test snapshot")
            if snapshot:
                print("✅ DOM snapshot test successful")
            else:
                print("🔴 DOM snapshot test failed")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                # Save debug data for Claude Code analysis before stopping
                debug_file = logger.save_debug_data_for_claude()
                if debug_file:
                    print(f"🔄 Debug data saved: {debug_file}")
                    
                logger.stop()
                print("Logger stopped")
                return 0
        else:
            print("Failed to start logger")
            return 1
    else:
        print("Failed to connect to Chrome")
        return 1

# Simple usage example
if __name__ == "__main__":
    import sys
    sys.exit(main())
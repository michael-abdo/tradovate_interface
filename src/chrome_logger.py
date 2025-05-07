#!/usr/bin/env python3
import time
import datetime
import os
import pychrome
from threading import Thread

class ChromeLogger:
    def __init__(self, tab, log_file=None):
        """
        Initialize a logger for Chrome DevTools Protocol
        
        Args:
            tab: The Chrome tab to log from (pychrome tab object)
            log_file: Path to log file (if None, will only use callbacks)
        """
        self.tab = tab
        self.log_file = log_file
        self.callbacks = []
        self.is_running = False
        self.log_thread = None
        
        # Create log file directory if needed
        if log_file:
            os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
    
    def start(self):
        """Start capturing logs from the browser"""
        if self.is_running:
            return
            
        try:
            # Enable various logging domains
            self.tab.Log.enable()
            self.tab.Runtime.enable()
            self.tab.Console.enable()
            
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
        """Stop the logger"""
        self.is_running = False
        if self.log_thread:
            self.log_thread.join(timeout=1.0)
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
        
        self._write_to_file(log_entry)
        self._process_callbacks(log_entry)
    
    def _on_console_api(self, **kwargs):
        """Handle Runtime.consoleAPICalled event"""
        args = kwargs.get('args', [])
        message = ' '.join([arg.get('value', str(arg)) for arg in args if 'value' in arg])
        
        log_entry = {
            'source': 'console',
            'level': kwargs.get('type', 'log').upper(),
            'text': message,
            'url': kwargs.get('stackTrace', {}).get('callFrames', [{}])[0].get('url', ''),
            'timestamp': time.time(),
            'raw': kwargs
        }
        
        self._write_to_file(log_entry)
        self._process_callbacks(log_entry)
    
    def _on_exception(self, **kwargs):
        """Handle Runtime.exceptionThrown event"""
        exception_details = kwargs.get('exceptionDetails', {})
        exception = exception_details.get('exception', {})
        
        log_entry = {
            'source': 'exception',
            'level': 'ERROR',
            'text': f"Exception: {exception.get('description', exception.get('value', 'Unknown error'))}",
            'url': exception_details.get('url', ''),
            'timestamp': time.time(),
            'raw': kwargs
        }
        
        self._write_to_file(log_entry)
        self._process_callbacks(log_entry)
    
    def _on_console_message(self, **kwargs):
        """Handle Console.messageAdded event"""
        message = kwargs.get('message', {})
        
        log_entry = {
            'source': 'console',
            'level': message.get('level', 'INFO').upper(),
            'text': message.get('text', ''),
            'url': message.get('url', ''),
            'timestamp': time.time(),
            'raw': kwargs
        }
        
        self._write_to_file(log_entry)
        self._process_callbacks(log_entry)
    
    def _process_logs(self):
        """Background thread to process log events"""
        while self.is_running:
            try:
                time.sleep(0.1)  # Prevent excessive CPU usage
            except Exception:
                break


def create_logger(tab, log_file=None, callback=None):
    """
    Create and start a Chrome logger for the given tab
    
    Args:
        tab: Chrome tab object from pychrome
        log_file: Optional file to write logs to
        callback: Optional callback function for log entries
        
    Returns:
        ChromeLogger instance if successful, None otherwise
    """
    logger = ChromeLogger(tab, log_file)
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
        log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'chrome.log')
        logger = create_logger(tab, log_file, print_log)
        
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
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
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
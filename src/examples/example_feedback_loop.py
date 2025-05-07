#!/usr/bin/env python3
import sys
import os
import time
import json
from login_helper import login_to_existing_chrome, execute_js, wait_for_element
from chrome_logger import create_logger

def log_callback(entry):
    """Custom callback to process Chrome log entries"""
    # Format log entries with different colors based on level
    level_colors = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'LOG': '\033[32m',      # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[41m\033[37m'  # White on red background
    }
    reset = '\033[0m'
    
    level = entry['level']
    color = level_colors.get(level, '')
    source = entry['source']
    
    # Format the message
    if source == 'console':
        print(f"{color}[CONSOLE]{reset} {entry['text']}")
    elif source == 'exception':
        print(f"{color}[EXCEPTION]{reset} {entry['text']}")
    else:
        print(f"{color}[{level}]{reset} {entry['text']}")
    
    # You could also handle specific messages here
    # For example, parse JSON messages or look for specific errors
    if "autoOrder" in entry['text'] or "autoriskManagement" in entry['text']:
        print(f"\033[1m>>> TamperMonkey script activity detected! <<<\033[0m")

def main():
    # Connect to an existing Chrome instance
    print("Connecting to Chrome...")
    success, tab, browser = login_to_existing_chrome(port=9222)
    
    if not success:
        print("Failed to connect to Chrome")
        return 1
        
    # Set up logging
    print("Setting up Chrome logger...")
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    log_file = os.path.join(logs_dir, f'chrome_{int(time.time())}.log')
    logger = create_logger(tab, log_file, log_callback)
    
    if not logger:
        print("Failed to set up logger")
        return 1
        
    print(f"Logger started, writing to {log_file}")
    
    # Inject custom JavaScript to send structured log data
    inject_js = """
    // Enhanced logging function
    window.sendStructuredLog = function(category, message, data = null) {
        const logObject = {
            timestamp: new Date().toISOString(),
            category: category,
            message: message,
            data: data
        };
        
        // Send as JSON string for easy parsing
        console.log('STRUCTURED_LOG: ' + JSON.stringify(logObject));
    };
    
    // Test the structured logging
    sendStructuredLog('TEST', 'Testing structured logging', {status: 'ok'});
    
    // Hook into fetch API to log requests and responses
    const originalFetch = window.fetch;
    window.fetch = async function(url, options) {
        const startTime = performance.now();
        sendStructuredLog('FETCH', `Request started: ${url}`, options);
        
        try {
            const response = await originalFetch(url, options);
            
            // Clone the response to read its body without consuming it
            const clonedResponse = response.clone();
            const responseTime = performance.now() - startTime;
            
            // Log basic response info immediately
            sendStructuredLog('FETCH', `Response received: ${url}`, {
                status: response.status,
                statusText: response.statusText,
                responseTime: responseTime.toFixed(2) + 'ms'
            });
            
            // For JSON responses, we can log the body content
            if (clonedResponse.headers.get('content-type')?.includes('application/json')) {
                try {
                    const json = await clonedResponse.json();
                    // Log only essential parts to avoid overwhelming logs
                    const simplifiedJson = typeof json === 'object' ? 
                        { type: Array.isArray(json) ? 'array' : 'object', length: Array.isArray(json) ? json.length : Object.keys(json).length } : 
                        { value: json };
                    
                    sendStructuredLog('FETCH', `Response body (JSON): ${url}`, simplifiedJson);
                } catch (e) {
                    sendStructuredLog('FETCH', `Error parsing JSON response: ${url}`, { error: e.message });
                }
            }
            
            return response;
        } catch (error) {
            sendStructuredLog('FETCH', `Request failed: ${url}`, { error: error.message });
            throw error;
        }
    };
    
    sendStructuredLog('SYSTEM', 'Fetch API hooks installed');
    """
    
    print("Injecting JavaScript hooks for enhanced logging...")
    execute_js(tab, inject_js)
    
    print("\nRunning interactive session with Chrome logging enabled")
    print("You can now interact with the browser and see logs here")
    print("Press Ctrl+C to exit\n")
    
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.stop()
        print("\nLogger stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
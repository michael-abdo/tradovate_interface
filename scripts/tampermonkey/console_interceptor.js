// Console Interceptor for Tradovate Interface
// This script captures all console output and stores it in localStorage for retrieval
// Must be injected BEFORE any other scripts to capture all console output

(function() {
    'use strict';
    
    // Store original console methods
    const originalConsole = {
        log: console.log.bind(console),
        error: console.error.bind(console),
        warn: console.warn.bind(console),
        info: console.info.bind(console),
        debug: console.debug.bind(console),
        trace: console.trace.bind(console),
        table: console.table.bind(console),
        group: console.group.bind(console),
        groupEnd: console.groupEnd.bind(console)
    };
    
    // Configuration
    const MAX_LOGS = 500;  // Maximum number of logs to keep
    const LOG_KEY_PREFIX = 'tradovate_console_';
    const INDEX_KEY = 'tradovate_console_index';
    
    // Initialize or get current index
    let logIndex = parseInt(localStorage.getItem(INDEX_KEY) || '0');
    
    // Helper to safely stringify objects
    function safeStringify(obj) {
        try {
            // Handle primitive types
            if (obj === null || obj === undefined) return String(obj);
            if (typeof obj !== 'object') return String(obj);
            
            // Handle circular references
            const seen = new WeakSet();
            return JSON.stringify(obj, function(key, value) {
                if (typeof value === 'object' && value !== null) {
                    if (seen.has(value)) {
                        return '[Circular Reference]';
                    }
                    seen.add(value);
                }
                return value;
            }, 2);
        } catch (e) {
            return '[Stringify Error: ' + e.message + ']';
        }
    }
    
    // Helper to format arguments
    function formatArgs(args) {
        return Array.from(args).map(arg => {
            if (typeof arg === 'string') return arg;
            return safeStringify(arg);
        }).join(' ');
    }
    
    // Helper to store log entry
    function storeLog(level, args) {
        try {
            const timestamp = new Date().toISOString();
            const message = formatArgs(args);
            
            const logEntry = {
                timestamp: timestamp,
                level: level,
                message: message,
                url: window.location.href
            };
            
            // Store with rotating index
            const key = LOG_KEY_PREFIX + (logIndex % MAX_LOGS);
            localStorage.setItem(key, JSON.stringify(logEntry));
            
            // Update index
            logIndex++;
            localStorage.setItem(INDEX_KEY, String(logIndex));
            
        } catch (e) {
            // If localStorage is full or unavailable, still call original console
            originalConsole.error('Console interceptor storage error:', e);
        }
    }
    
    // Override console methods
    ['log', 'error', 'warn', 'info', 'debug'].forEach(method => {
        console[method] = function() {
            // Store the log
            storeLog(method, arguments);
            
            // Call original method
            originalConsole[method].apply(console, arguments);
        };
    });
    
    // Special handling for trace (includes stack trace)
    console.trace = function() {
        const stack = new Error().stack;
        const args = Array.from(arguments);
        args.push('\nStack trace:\n' + stack);
        storeLog('trace', args);
        originalConsole.trace.apply(console, arguments);
    };
    
    // Special handling for table (convert to string representation)
    console.table = function() {
        storeLog('table', [safeStringify(arguments[0])]);
        originalConsole.table.apply(console, arguments);
    };
    
    // Group methods (just log the labels)
    console.group = function() {
        storeLog('group', arguments);
        originalConsole.group.apply(console, arguments);
    };
    
    console.groupEnd = function() {
        storeLog('groupEnd', ['']);
        originalConsole.groupEnd.apply(console, arguments);
    };
    
    // Add a method to clear console logs
    window.clearConsoleLogs = function() {
        const currentIndex = parseInt(localStorage.getItem(INDEX_KEY) || '0');
        for (let i = 0; i < MAX_LOGS; i++) {
            localStorage.removeItem(LOG_KEY_PREFIX + i);
        }
        localStorage.setItem(INDEX_KEY, '0');
        console.log('Console logs cleared');
    };
    
    // Add a method to get all console logs
    window.getConsoleLogs = function() {
        const logs = [];
        const currentIndex = parseInt(localStorage.getItem(INDEX_KEY) || '0');
        const startIndex = Math.max(0, currentIndex - MAX_LOGS);
        
        for (let i = startIndex; i < currentIndex; i++) {
            const key = LOG_KEY_PREFIX + (i % MAX_LOGS);
            const logStr = localStorage.getItem(key);
            if (logStr) {
                try {
                    logs.push(JSON.parse(logStr));
                } catch (e) {
                    // Skip corrupted entries
                }
            }
        }
        
        // Sort by timestamp
        return logs.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    };
    
    // Log that interceptor is active
    console.log('Console interceptor initialized - all console output will be captured');
})();
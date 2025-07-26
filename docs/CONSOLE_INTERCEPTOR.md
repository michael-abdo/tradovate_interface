# Console Interceptor Documentation

## Overview

The Console Interceptor is a localStorage-based logging system that captures all browser console output from Tradovate pages. It bypasses pychrome's WebSocket JSON parsing issues by storing logs in localStorage and retrieving them via JavaScript evaluation.

## How It Works

### 1. Console Method Interception
The interceptor overrides all console methods while preserving their original functionality:
- `console.log()`
- `console.error()`
- `console.warn()`
- `console.info()`
- `console.debug()`
- `console.trace()` (includes stack trace)
- `console.table()` (converts to string representation)
- `console.group()` / `console.groupEnd()`

### 2. LocalStorage Storage
- Logs are stored with a rotating buffer (max 500 entries)
- Each log entry includes:
  - `timestamp`: ISO 8601 format timestamp
  - `level`: Log level (log, error, warn, info, debug, trace, table, group)
  - `message`: The formatted log message
  - `url`: Current page URL where the log originated

### 3. Python Integration
The Python code retrieves logs using `JSON.stringify()` to avoid pychrome parsing errors:
```python
# Retrieves logs as JSON string and parses them
js_code = "JSON.stringify(window.getConsoleLogs())"
result = self.tab.Runtime.evaluate(expression=js_code)
```

## File Locations

### JavaScript Interceptor
`scripts/tampermonkey/console_interceptor.js`
- Must be injected BEFORE any other scripts
- Self-contained IIFE (Immediately Invoked Function Expression)
- No external dependencies

### Python Integration
`src/app.py`
- `inject_tampermonkey()`: Injects console interceptor first (lines 75-86)
- `get_console_logs()`: Retrieves captured logs (lines 255-305)
- `auto_trade()`: Captures logs during trade execution (lines 155-181)
- `exit_positions()`: Captures logs during position exit (lines 182-208)

## Usage

### Basic Retrieval
```python
# Get all console logs
result = connection.get_console_logs()
logs = result['logs']  # List of log entries
```

### With Options
```python
# Get only the last 20 logs
result = connection.get_console_logs(limit=20)

# Clear logs after retrieval
result = connection.get_console_logs(clear_after=True)

# Combine options
result = connection.get_console_logs(limit=50, clear_after=True)
```

### Trade Execution with Logs
```python
# Execute trade - console logs are automatically captured
result = connection.auto_trade('NQ', quantity=1, action='Buy')

# Access console logs from the trade
if 'console_logs' in result:
    for log in result['console_logs']:
        print(f"[{log['level']}] {log['message']}")
```

### Manual Console Operations
```python
# Clear all console logs
connection.tab.Runtime.evaluate(expression="window.clearConsoleLogs()")

# Check if interceptor is loaded
result = connection.tab.Runtime.evaluate(expression="typeof window.getConsoleLogs")
is_loaded = result.get('result', {}).get('value') == 'function'
```

## Example Log Entry

```json
{
  "timestamp": "2025-07-25T02:06:34.684Z",
  "level": "error",
  "message": "Failed to execute trade: Invalid symbol",
  "url": "https://trader.tradovate.com/welcome"
}
```

## Benefits

1. **Bypasses pychrome JSON errors**: Uses localStorage instead of WebSocket events
2. **Captures all console output**: Including logs from injected scripts
3. **Persistent storage**: Logs survive page navigation (within same domain)
4. **Circular reference handling**: Safely serializes complex objects
5. **No performance impact**: Original console methods work normally

## Troubleshooting

### Logs Not Appearing
1. Verify interceptor is injected:
   ```python
   result = conn.tab.Runtime.evaluate(expression="typeof window.getConsoleLogs")
   print(result.get('result', {}).get('value'))  # Should print "function"
   ```

2. Check localStorage is available:
   ```python
   result = conn.tab.Runtime.evaluate(expression="typeof localStorage")
   print(result.get('result', {}).get('value'))  # Should print "object"
   ```

### JSON Parse Errors
- The interceptor handles circular references automatically
- Complex objects are serialized with 2-space indentation
- Errors during serialization show as `[Stringify Error: ...]`

### Storage Limits
- Maximum 500 logs are kept (rotating buffer)
- Older logs are automatically overwritten
- Use `clear_after=True` to prevent accumulation

## Integration with Dashboard

The console logs are automatically included in:
- Trade execution responses (`/api/trade` endpoint)
- Position exit responses (`/api/exit` endpoint)
- Can be added to any operation by calling `get_console_logs()`

## Future Enhancements

1. **Filtering by level**: Add ability to retrieve only errors or warnings
2. **Search functionality**: Search logs by message content
3. **Export functionality**: Save logs to file for debugging
4. **Real-time streaming**: WebSocket endpoint for live log monitoring
5. **Performance metrics**: Track execution times and API calls
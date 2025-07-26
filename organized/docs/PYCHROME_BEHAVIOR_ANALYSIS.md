# Pychrome Exception Types & Response Format Analysis

## Current Exception Handling Patterns

### **Existing Error Handling**: Generic Exception Catching
```python
try:
    result = tab.Runtime.evaluate(expression=js_code)
    return result.get("result", {}).get("value", "")
except Exception as e:
    print(f"Error executing script: {e}")
    return None
```

**Problems with Current Approach:**
- **No specific exception typing** - all exceptions treated the same
- **No response validation** - doesn't check for JavaScript errors
- **No retry logic** - single failure = permanent failure
- **No error classification** - cannot determine recovery strategy

---

## Pychrome Response Structure Analysis

### **Successful Response Format:**
```python
{
    "result": {
        "type": "number|string|object|boolean|undefined",
        "value": <actual_value>,
        "description": "string_representation"
    },
    "id": <message_id>
}
```

### **JavaScript Exception Response Format:**
```python
{
    "result": {
        "type": "object",
        "subtype": "error", 
        "className": "Error",
        "description": "ReferenceError: someFunction is not defined"
    },
    "exceptionDetails": {
        "exceptionId": 1,
        "text": "Uncaught ReferenceError: someFunction is not defined",
        "lineNumber": 1,
        "columnNumber": 1,
        "scriptId": "123",
        "stackTrace": {
            "callFrames": [...]
        }
    },
    "id": <message_id>
}
```

### **Network/Connection Error:**
```python
# pychrome raises requests.exceptions.ConnectionError
# or websocket connection errors
```

---

## Exception Types Classification

### **1. Network-Level Exceptions** (Immediate Retry)
- `requests.exceptions.ConnectionError` - Chrome not responding
- `websocket.exceptions.ConnectionClosed` - WebSocket dropped
- `requests.exceptions.Timeout` - Request timeout
- `ConnectionRefusedError` - Chrome not listening on port

**Recovery Strategy**: Immediate retry (up to 3x)

### **2. Chrome Protocol Exceptions** (Delayed Retry)
- Chrome returns HTTP 500 - Internal server error
- Chrome busy/overloaded responses
- Tab not accessible errors

**Recovery Strategy**: Exponential backoff retry

### **3. JavaScript Execution Errors** (No Retry)
- `exceptionDetails` present in response
- Syntax errors in JavaScript
- Runtime errors (undefined functions, etc.)
- Type errors

**Recovery Strategy**: No retry, log and fail

### **4. Tab State Exceptions** (Tab Validation)
- Tab closed/crashed
- Tab navigated away from Tradovate
- Tab in wrong state

**Recovery Strategy**: Tab recovery or failover

---

## Response Validation Patterns

### **Current Pattern** (Inadequate):
```python
result = tab.Runtime.evaluate(expression=js_code)
value = result.get("result", {}).get("value", "")
```

**Missing Validations:**
- No check for `exceptionDetails`
- No validation of `result.type`
- No handling of `undefined` responses
- No verification of expected value type

### **Required Validation Pattern:**
```python
def validate_pychrome_response(result, expected_type=None):
    """Comprehensive response validation"""
    
    # Check for network/protocol errors
    if not result or not isinstance(result, dict):
        return {"error": "Invalid response format", "retry": True}
    
    # Check for JavaScript execution errors
    if "exceptionDetails" in result:
        exception = result["exceptionDetails"]
        return {
            "error": f"JavaScript error: {exception.get('text', 'Unknown error')}", 
            "retry": False,
            "details": exception
        }
    
    # Check for missing result
    if "result" not in result:
        return {"error": "Missing result in response", "retry": True}
    
    result_obj = result["result"]
    
    # Check for JavaScript errors without exceptionDetails
    if (result_obj.get("type") == "object" and 
        result_obj.get("subtype") == "error"):
        return {
            "error": f"JavaScript error: {result_obj.get('description', 'Unknown error')}", 
            "retry": False
        }
    
    # Validate expected type if specified
    if expected_type and result_obj.get("type") != expected_type:
        return {
            "error": f"Expected {expected_type}, got {result_obj.get('type')}", 
            "retry": False
        }
    
    # Check for undefined results
    if result_obj.get("type") == "undefined":
        return {"error": "JavaScript returned undefined", "retry": False}
    
    return {"success": True, "value": result_obj.get("value")}
```

---

## Timeout Behavior Analysis

### **pychrome Default Timeouts:**
- **Connection timeout**: Usually 10 seconds
- **Read timeout**: Usually 30 seconds  
- **No JavaScript execution timeout** by default

### **Required Timeout Strategy:**
```python
# Different timeouts for different operation types
OPERATION_TIMEOUTS = {
    "CRITICAL": 10,      # Trade execution
    "IMPORTANT": 5,      # UI updates
    "NON_CRITICAL": 2    # Testing/monitoring
}
```

---

## Chrome Tab State Detection

### **Tab Accessibility Test:**
```javascript
// Test if tab is responsive and in correct state
(function() {
    try {
        return {
            url: window.location.href,
            readyState: document.readyState,
            tradovateLoaded: typeof window !== 'undefined' && 
                           window.location.href.includes('tradovate.com'),
            timestamp: Date.now()
        };
    } catch(e) {
        return {error: e.message};
    }
})();
```

### **Function Availability Test:**
```javascript
// Test if required functions are available
(function() {
    const requiredFunctions = ['autoTrade', 'getAllAccountTableData', 'updateSymbol'];
    const missing = requiredFunctions.filter(fn => typeof window[fn] !== 'function');
    return {
        allFunctionsAvailable: missing.length === 0,
        missingFunctions: missing,
        availableFunctions: requiredFunctions.filter(fn => typeof window[fn] === 'function')
    };
})();
```

---

## Error Recovery Decision Tree

```
Runtime.evaluate() Call
│
├─ Network Error (ConnectionError, Timeout)
│  ├─ Retry Count < 3? → IMMEDIATE RETRY
│  └─ Retry Count >= 3 → FAIL with Circuit Breaker
│
├─ Chrome Protocol Error (HTTP 500, Busy)
│  ├─ Retry Count < 2? → EXPONENTIAL BACKOFF RETRY  
│  └─ Retry Count >= 2 → FAIL with Circuit Breaker
│
├─ JavaScript Error (exceptionDetails present)
│  └─ NO RETRY → LOG and FAIL (fix required)
│
├─ Tab State Error (tab closed, navigated)
│  ├─ Critical Operation? → TAB RECOVERY ATTEMPT
│  └─ Non-Critical → SKIP and CONTINUE
│
└─ Success Response
   ├─ Validate Response Type/Value
   ├─ Check for undefined/null
   └─ Return Parsed Value
```

---

## Implementation Requirements

### **1. Exception Type Detection:**
```python
import requests.exceptions
import websocket.exceptions

def classify_exception(exception):
    if isinstance(exception, (requests.exceptions.ConnectionError, 
                             requests.exceptions.Timeout,
                             websocket.exceptions.ConnectionClosed)):
        return "NETWORK_ERROR"
    elif "500" in str(exception) or "busy" in str(exception).lower():
        return "CHROME_BUSY"
    elif "tab" in str(exception).lower():
        return "TAB_ERROR"
    else:
        return "UNKNOWN_ERROR"
```

### **2. Response Validation:**
```python
def safe_evaluate(tab, js_code, operation_type="IMPORTANT", expected_type=None):
    max_retries = RETRY_LIMITS[operation_type]
    timeout = OPERATION_TIMEOUTS[operation_type]
    
    for attempt in range(max_retries + 1):
        try:
            result = tab.Runtime.evaluate(expression=js_code, timeout=timeout)
            validation = validate_pychrome_response(result, expected_type)
            
            if validation.get("success"):
                return validation["value"]
            elif not validation.get("retry", False):
                # JavaScript error - no retry
                raise JavaScriptExecutionError(validation["error"])
            
        except Exception as e:
            error_type = classify_exception(e)
            
            if attempt < max_retries and error_type in ["NETWORK_ERROR", "CHROME_BUSY"]:
                wait_time = BACKOFF_STRATEGY[error_type](attempt)
                time.sleep(wait_time)
                continue
            else:
                raise ChromeCommunicationError(f"Failed after {attempt + 1} attempts: {e}")
    
    raise ChromeCommunicationError("Max retries exceeded")
```

---

## Testing Edge Cases Required

### **Network Simulation:**
- Chrome process killed during execution
- Network disconnection scenarios
- Firewall blocking Chrome ports

### **Chrome State Simulation:**
- Chrome busy/high load conditions
- Memory pressure scenarios
- Multiple concurrent operations

### **JavaScript Error Simulation:**
- Syntax errors in JavaScript
- Undefined function calls
- Type mismatches

### **Tab State Simulation:**
- Tab navigation during execution
- Tab crashes/recovers
- Multiple tabs competing for resources

---

*This analysis provides the foundation for implementing robust pychrome communication with proper error handling, validation, and recovery strategies.*
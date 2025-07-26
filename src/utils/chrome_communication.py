#!/usr/bin/env python3
"""
Chrome Communication Framework for Tradovate Interface

This module provides robust, logged, and validated communication with Chrome via pychrome.
Implements comprehensive error handling, retry logic, and visibility for all Chrome operations.

Key Features:
- Classification of operations by criticality
- Retry strategies based on error types  
- Tab health validation
- Circuit breaker pattern for repeated failures
- Operation queuing for concurrent safety
- Comprehensive logging and monitoring

Usage:
    from src.utils.chrome_communication import ChromeCommunicationManager, OperationType
    
    manager = ChromeCommunicationManager()
    result = manager.safe_evaluate(
        tab=chrome_tab,
        js_code="autoTrade('NQ', 1, 'Buy', 100, 40, 0.25)",
        operation_type=OperationType.CRITICAL,
        description="Execute NQ trade"
    )
"""

import time
import json
import logging
import threading
import queue
from enum import Enum
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests.exceptions

# Handle optional websocket import gracefully
try:
    import websocket.exceptions
    WEBSOCKET_AVAILABLE = True
except ImportError:
    try:
        import websocket_client as websocket
        WEBSOCKET_AVAILABLE = True
    except ImportError:
        # Create dummy websocket exceptions for type checking
        class _DummyWebsocketExceptions:
            class ConnectionClosed(Exception):
                pass
            class WebSocketException(Exception):
                pass
        
        class websocket:
            exceptions = _DummyWebsocketExceptions()
        
        WEBSOCKET_AVAILABLE = False

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

# Operation timeouts by criticality (seconds)
OPERATION_TIMEOUTS = {
    "CRITICAL": 15,      # Trade execution, authentication
    "IMPORTANT": 8,      # UI updates, data fetching  
    "NON_CRITICAL": 3    # Testing, monitoring
}

# Retry limits by operation type
RETRY_LIMITS = {
    "CRITICAL": 3,       # Maximum retries for critical operations
    "IMPORTANT": 2,      # Maximum retries for important operations
    "NON_CRITICAL": 0    # No retries for non-critical operations
}

# Backoff strategies (seconds to wait between retries)
BACKOFF_STRATEGIES = {
    "IMMEDIATE": [0.1, 0.2, 0.5],           # Network errors
    "EXPONENTIAL": [1, 2, 4],               # Chrome busy
    "LINEAR": [1, 2, 3],                    # Tab errors
    "NONE": []                              # No retry
}

# Circuit breaker thresholds
CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": 5,      # Failures before opening circuit
    "recovery_timeout": 30,      # Seconds before attempting recovery
    "half_open_limit": 3         # Test calls before closing circuit
}

# Performance monitoring thresholds
PERFORMANCE_THRESHOLDS = {
    "slow_operation": 2.0,       # Log operations slower than 2s
    "very_slow_operation": 5.0,  # Alert for operations slower than 5s
    "max_queue_size": 10,        # Maximum operations in queue per tab
    "max_concurrent_ops": 3      # Maximum concurrent operations per tab
}

# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class OperationType(Enum):
    """Operation criticality classification"""
    CRITICAL = "CRITICAL"        # Trade execution, authentication - zero tolerance for failure
    IMPORTANT = "IMPORTANT"      # UI updates, data fetching - degraded functionality acceptable  
    NON_CRITICAL = "NON_CRITICAL"  # Testing, monitoring - failure acceptable

class ErrorType(Enum):
    """Classification of error types for retry strategy selection"""
    NETWORK_ERROR = "NETWORK_ERROR"        # Connection issues - immediate retry
    CHROME_BUSY = "CHROME_BUSY"           # Chrome overloaded - exponential backoff
    JAVASCRIPT_ERROR = "JAVASCRIPT_ERROR"  # JS syntax/runtime - no retry
    TAB_ERROR = "TAB_ERROR"               # Tab closed/navigated - tab recovery
    UNKNOWN_ERROR = "UNKNOWN_ERROR"       # Unclassified - conservative handling

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"        # Normal operation
    OPEN = "OPEN"           # Failing - reject all calls
    HALF_OPEN = "HALF_OPEN" # Testing recovery

class ResponseStatus(Enum):
    """Response validation status"""
    SUCCESS = "SUCCESS"
    JAVASCRIPT_ERROR = "JAVASCRIPT_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"

@dataclass
class OperationResult:
    """Result of a Chrome operation"""
    success: bool
    value: Any = None
    error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    execution_time: float = 0.0
    retry_count: int = 0
    operation_id: Optional[str] = None

@dataclass
class TabHealthStatus:
    """Tab health check result"""
    healthy: bool
    url: str = ""
    ready_state: str = ""
    tradovate_loaded: bool = False
    functions_available: List[str] = None
    errors: List[str] = None
    last_check: datetime = None
    
    def __post_init__(self):
        if self.functions_available is None:
            self.functions_available = []
        if self.errors is None:
            self.errors = []
        if self.last_check is None:
            self.last_check = datetime.now()

@dataclass
class CircuitBreakerStatus:
    """Circuit breaker state information"""
    state: CircuitState
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    half_open_attempts: int = 0
    total_operations: int = 0
    success_rate: float = 100.0

# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class ChromeCommunicationError(Exception):
    """Base exception for Chrome communication issues"""
    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR, 
                 retry_count: int = 0, operation_id: str = None):
        super().__init__(message)
        self.error_type = error_type
        self.retry_count = retry_count
        self.operation_id = operation_id

class JavaScriptExecutionError(ChromeCommunicationError):
    """JavaScript execution failed - no retry recommended"""
    def __init__(self, message: str, js_details: dict = None, operation_id: str = None):
        super().__init__(message, ErrorType.JAVASCRIPT_ERROR, 0, operation_id)
        self.js_details = js_details or {}

class CircuitBreakerOpenError(ChromeCommunicationError):
    """Circuit breaker is open - operation rejected"""
    def __init__(self, message: str = "Circuit breaker is open", operation_id: str = None):
        super().__init__(message, ErrorType.UNKNOWN_ERROR, 0, operation_id)

class TabHealthError(ChromeCommunicationError):
    """Tab is not in a healthy state"""
    def __init__(self, message: str, health_status: TabHealthStatus = None, operation_id: str = None):
        super().__init__(message, ErrorType.TAB_ERROR, 0, operation_id)
        self.health_status = health_status

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_operation_id() -> str:
    """Generate unique operation ID for tracking"""
    return f"op_{int(time.time() * 1000000)}"

def classify_exception(exception: Exception) -> ErrorType:
    """Classify exception type for retry strategy selection"""
    exception_str = str(exception).lower()
    
    if isinstance(exception, (requests.exceptions.ConnectionError, 
                             requests.exceptions.Timeout,
                             requests.exceptions.ConnectTimeout,
                             requests.exceptions.ReadTimeout)):
        return ErrorType.NETWORK_ERROR
    
    # Check websocket exceptions if available
    if WEBSOCKET_AVAILABLE:
        try:
            if isinstance(exception, (websocket.exceptions.ConnectionClosed,
                                     getattr(websocket.exceptions, 'ConnectionClosedError', Exception))):
                return ErrorType.NETWORK_ERROR
        except AttributeError:
            # Some websocket libraries might not have all exception types
            pass
    
    if any(keyword in exception_str for keyword in ['500', 'busy', 'overloaded', 'timeout']):
        return ErrorType.CHROME_BUSY
    
    if any(keyword in exception_str for keyword in ['tab', 'closed', 'navigation', 'frame']):
        return ErrorType.TAB_ERROR
    
    if isinstance(exception, JavaScriptExecutionError):
        return ErrorType.JAVASCRIPT_ERROR
        
    return ErrorType.UNKNOWN_ERROR

def get_backoff_time(error_type: ErrorType, attempt: int) -> float:
    """Get backoff time for retry strategy"""
    if error_type == ErrorType.NETWORK_ERROR:
        backoffs = BACKOFF_STRATEGIES["IMMEDIATE"]
    elif error_type == ErrorType.CHROME_BUSY:
        backoffs = BACKOFF_STRATEGIES["EXPONENTIAL"]  
    elif error_type == ErrorType.TAB_ERROR:
        backoffs = BACKOFF_STRATEGIES["LINEAR"]
    else:
        return 0  # No retry for unknown/JS errors
    
    if attempt < len(backoffs):
        return backoffs[attempt]
    else:
        return backoffs[-1] * 2  # Double last backoff for additional attempts

def validate_pychrome_response(result: dict, expected_type: str = None) -> dict:
    """
    Comprehensive validation of pychrome response
    
    Args:
        result: Raw response from tab.Runtime.evaluate()
        expected_type: Expected JavaScript type (optional)
        
    Returns:
        Dict with validation results and parsed value
    """
    if not result or not isinstance(result, dict):
        return {
            "status": ResponseStatus.VALIDATION_ERROR,
            "error": "Invalid response format",
            "retry_recommended": True
        }
    
    # Check for JavaScript execution errors
    if "exceptionDetails" in result:
        exception = result["exceptionDetails"]
        return {
            "status": ResponseStatus.JAVASCRIPT_ERROR,
            "error": f"JavaScript error: {exception.get('text', 'Unknown error')}",
            "retry_recommended": False,
            "exception_details": exception
        }
    
    # Check for missing result
    if "result" not in result:
        return {
            "status": ResponseStatus.VALIDATION_ERROR,
            "error": "Missing result in response",
            "retry_recommended": True
        }
    
    result_obj = result["result"]
    
    # Check for JavaScript errors without exceptionDetails
    if (result_obj.get("type") == "object" and 
        result_obj.get("subtype") == "error"):
        return {
            "status": ResponseStatus.JAVASCRIPT_ERROR,
            "error": f"JavaScript error: {result_obj.get('description', 'Unknown error')}",
            "retry_recommended": False,
            "js_error": result_obj.get("description")
        }
    
    # Validate expected type if specified
    if expected_type and result_obj.get("type") != expected_type:
        return {
            "status": ResponseStatus.VALIDATION_ERROR,
            "error": f"Expected {expected_type}, got {result_obj.get('type')}",
            "retry_recommended": False
        }
    
    # Check for undefined results
    if result_obj.get("type") == "undefined":
        return {
            "status": ResponseStatus.VALIDATION_ERROR,
            "error": "JavaScript returned undefined",
            "retry_recommended": False
        }
    
    return {
        "status": ResponseStatus.SUCCESS,
        "value": result_obj.get("value"),
        "js_type": result_obj.get("type"),
        "retry_recommended": False
    }

# ============================================================================
# STRUCTURED LOGGING SETUP
# ============================================================================

import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": getattr(record, 'module', record.filename),
            "function": getattr(record, 'funcName', None),
            "line": getattr(record, 'lineno', 0),
            "thread": getattr(record, 'thread', None),
            "process": getattr(record, 'process', None)
        }
        
        # Add extra context if available
        if hasattr(record, 'operation_id'):
            log_entry['operation_id'] = record.operation_id
        if hasattr(record, 'tab_info'):
            log_entry['tab_info'] = record.tab_info
        if hasattr(record, 'operation_type'):
            log_entry['operation_type'] = record.operation_type
        if hasattr(record, 'execution_time'):
            log_entry['execution_time'] = record.execution_time
        if hasattr(record, 'retry_count'):
            log_entry['retry_count'] = record.retry_count
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
            
        return json.dumps(log_entry, separators=(',', ':'))

class ChromeOperationLogger:
    """Specialized logger for Chrome operations with context tracking"""
    
    def __init__(self, base_logger: logging.Logger = None):
        # Create default logger if none provided
        if base_logger is None:
            base_logger = logging.getLogger('chrome_communication')
            if not base_logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                base_logger.addHandler(handler)
                base_logger.setLevel(logging.INFO)
        
        self.base_logger = base_logger
        self.operation_contexts = {}  # Track context per operation
    
    def start_operation(self, operation_id: str, operation_type: OperationType, 
                       description: str, tab_info: dict = None):
        """Log operation start with full context"""
        context = {
            "operation_id": operation_id,
            "operation_type": operation_type.value,
            "description": description,
            "start_time": time.time(),
            "tab_info": tab_info or {}
        }
        self.operation_contexts[operation_id] = context
        
        self.base_logger.info(
            f"🔄 CHROME_OP_START: {description}",
            extra={
                "operation_id": operation_id,
                "operation_type": operation_type.value,
                "tab_info": tab_info
            }
        )
    
    def log_retry(self, operation_id: str, retry_count: int, error_type: ErrorType, 
                  error_msg: str, backoff_time: float):
        """Log retry attempt with context"""
        self.base_logger.warning(
            f"🔁 CHROME_OP_RETRY: Attempt {retry_count} after {error_type.value}: {error_msg}",
            extra={
                "operation_id": operation_id,
                "retry_count": retry_count,
                "error_type": error_type.value,
                "backoff_time": backoff_time
            }
        )
    
    def log_success(self, operation_id: str, result_value: Any = None, 
                   execution_time: float = None):
        """Log successful operation completion"""
        context = self.operation_contexts.get(operation_id, {})
        start_time = context.get("start_time", time.time())
        total_time = execution_time or (time.time() - start_time)
        
        # Check for slow operations
        if total_time > PERFORMANCE_THRESHOLDS["very_slow_operation"]:
            log_level = "error"
            prefix = "🐌 CHROME_OP_VERY_SLOW"
        elif total_time > PERFORMANCE_THRESHOLDS["slow_operation"]:
            log_level = "warning"
            prefix = "⚠️ CHROME_OP_SLOW"
        else:
            log_level = "info"
            prefix = "✅ CHROME_OP_SUCCESS"
        
        log_msg = f"{prefix}: {context.get('description', 'Unknown')} completed in {total_time:.3f}s"
        
        getattr(self.base_logger, log_level)(
            log_msg,
            extra={
                "operation_id": operation_id,
                "execution_time": total_time,
                "operation_type": context.get("operation_type"),
                "result_type": type(result_value).__name__ if result_value is not None else None
            }
        )
        
        # Clean up context
        if operation_id in self.operation_contexts:
            del self.operation_contexts[operation_id]
    
    def log_failure(self, operation_id: str, error: Exception, error_type: ErrorType, 
                   retry_count: int = 0, execution_time: float = None):
        """Log operation failure with full context"""
        context = self.operation_contexts.get(operation_id, {})
        start_time = context.get("start_time", time.time())
        total_time = execution_time or (time.time() - start_time)
        
        self.base_logger.error(
            f"❌ CHROME_OP_FAILED: {context.get('description', 'Unknown')} - {error}",
            extra={
                "operation_id": operation_id,
                "error_type": error_type.value,
                "retry_count": retry_count,
                "execution_time": total_time,
                "operation_type": context.get("operation_type"),
                "error_message": str(error)
            }
        )
        
        # Clean up context
        if operation_id in self.operation_contexts:
            del self.operation_contexts[operation_id]
    
    def log_circuit_breaker(self, tab_id: str, action: str, failure_count: int = 0):
        """Log circuit breaker state changes"""
        self.base_logger.warning(
            f"🚨 CIRCUIT_BREAKER_{action}: Tab {tab_id} - failures: {failure_count}",
            extra={
                "tab_id": tab_id,
                "circuit_breaker_action": action,
                "failure_count": failure_count
            }
        )
    
    def log_tab_health(self, tab_id: str, health_status: TabHealthStatus):
        """Log tab health check results"""
        level = "info" if health_status.healthy else "warning"
        status = "HEALTHY" if health_status.healthy else "UNHEALTHY"
        
        getattr(self.base_logger, level)(
            f"🏥 TAB_HEALTH_{status}: {tab_id} - {health_status.url}",
            extra={
                "tab_id": tab_id,
                "tab_healthy": health_status.healthy,
                "tab_url": health_status.url,
                "functions_available": len(health_status.functions_available),
                "error_count": len(health_status.errors)
            }
        )

def setup_chrome_communication_logger(name: str = "chrome_communication") -> logging.Logger:
    """Set up structured logging for Chrome communication"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:  # Avoid duplicate handlers
        logger.setLevel(logging.DEBUG)
        
        # Console handler for immediate feedback (human readable)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler for detailed logging (structured JSON)
        file_handler = logging.FileHandler('logs/chrome_communication.log', mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        
        # Performance metrics handler
        perf_handler = logging.FileHandler('logs/chrome_performance.log', mode='a')
        perf_handler.setLevel(logging.WARNING)  # Only slow/failed operations
        perf_handler.setFormatter(StructuredFormatter())
        
        # Error-only handler for alerts
        error_handler = logging.FileHandler('logs/chrome_errors.log', mode='a')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.addHandler(perf_handler)
        logger.addHandler(error_handler)
    
    return logger

# Default logger instances
base_logger = setup_chrome_communication_logger()
operation_logger = ChromeOperationLogger(base_logger)

# ============================================================================
# TAB HEALTH VALIDATOR
# ============================================================================

class TabHealthValidator:
    """Validates Chrome tab health, connectivity, and function availability"""
    
    # Required JavaScript functions for different operation types
    REQUIRED_FUNCTIONS = {
        OperationType.CRITICAL: [
            'autoTrade', 'clickExitForSymbol', 'updateSymbol'
        ],
        OperationType.IMPORTANT: [
            'getAllAccountTableData', 'getTableData', 'updateUserColumnPhaseStatus'
        ],
        OperationType.NON_CRITICAL: [
            'getConsoleLogs', 'clearConsoleLogs'
        ]
    }
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.logger = base_logger
    
    def validate_tab_health(self, tab, operation_type: OperationType = OperationType.IMPORTANT) -> TabHealthStatus:
        """
        Comprehensive tab health validation
        
        Args:
            tab: pychrome tab object
            operation_type: Required function set based on operation criticality
            
        Returns:
            TabHealthStatus with detailed health information
        """
        health = TabHealthStatus(healthy=False)
        
        try:
            # Basic connectivity test
            if not self._test_basic_connectivity(tab, health):
                return health
            
            # Page state validation
            if not self._validate_page_state(tab, health, operation_type):
                return health
            
            # Function availability check
            if not self._validate_function_availability(tab, operation_type, health):
                return health
            
            # If we get here, tab is healthy
            health.healthy = True
            self.logger.debug(f"Tab health validation passed: {health.url}")
            
        except Exception as e:
            health.errors.append(f"Health validation exception: {str(e)}")
            self.logger.error(f"Tab health validation failed: {e}")
        
        return health
    
    def _test_basic_connectivity(self, tab, health: TabHealthStatus) -> bool:
        """Test basic tab connectivity"""
        try:
            # Test simple JavaScript execution
            result = tab.Runtime.evaluate(expression="1 + 1", timeout=self.timeout)
            
            if not result or result.get("result", {}).get("value") != 2:
                health.errors.append("Basic JavaScript execution failed")
                return False
            
            return True
            
        except Exception as e:
            health.errors.append(f"Basic connectivity failed: {str(e)}")
            return False
    
    def _validate_page_state(self, tab, health: TabHealthStatus, operation_type: OperationType = OperationType.IMPORTANT) -> bool:
        """Validate page is in correct state"""
        try:
            # Get comprehensive page state
            page_state_js = """
            (function() {
                try {
                    return {
                        url: window.location.href,
                        readyState: document.readyState,
                        tradovateLoaded: window.location.href.includes('tradovate.com'),
                        hasContent: document.body && document.body.children.length > 0,
                        timestamp: Date.now(),
                        userAgent: navigator.userAgent
                    };
                } catch(e) {
                    return {error: e.message};
                }
            })();
            """
            
            result = tab.Runtime.evaluate(expression=page_state_js, timeout=self.timeout)
            
            if not result or "exceptionDetails" in result:
                health.errors.append("Failed to get page state")
                return False
            
            page_data = result.get("result", {}).get("value", {})
            
            if "error" in page_data:
                health.errors.append(f"Page state error: {page_data['error']}")
                return False
            
            # Update health status with page data
            health.url = page_data.get("url", "")
            health.ready_state = page_data.get("readyState", "")
            health.tradovate_loaded = page_data.get("tradovateLoaded", False)
            
            # Validate requirements (stricter for CRITICAL operations)
            if not health.tradovate_loaded and operation_type in [OperationType.CRITICAL, OperationType.IMPORTANT]:
                health.errors.append("Not on Tradovate domain")
                return False
            
            # Page readiness check (relaxed for NON_CRITICAL operations)
            if health.ready_state != "complete" and operation_type in [OperationType.CRITICAL, OperationType.IMPORTANT]:
                health.errors.append(f"Page not ready: {health.ready_state}")
                return False
            
            # Content check (relaxed for NON_CRITICAL operations)
            if not page_data.get("hasContent", False) and operation_type in [OperationType.CRITICAL, OperationType.IMPORTANT]:
                health.errors.append("Page has no content")
                return False
            
            return True
            
        except Exception as e:
            health.errors.append(f"Page state validation failed: {str(e)}")
            return False
    
    def _validate_function_availability(self, tab, operation_type: OperationType, 
                                       health: TabHealthStatus) -> bool:
        """Validate required JavaScript functions are available"""
        try:
            # Get all required functions for this operation type
            required_functions = []
            for op_type in [OperationType.NON_CRITICAL, OperationType.IMPORTANT, OperationType.CRITICAL]:
                required_functions.extend(self.REQUIRED_FUNCTIONS.get(op_type, []))
                if op_type == operation_type:
                    break
            
            # Remove duplicates while preserving order
            required_functions = list(dict.fromkeys(required_functions))
            
            # Build JavaScript to check function availability
            function_check_js = f"""
            (function() {{
                const requiredFunctions = {json.dumps(required_functions)};
                const result = {{
                    availableFunctions: [],
                    missingFunctions: [],
                    functionTypes: {{}}
                }};
                
                requiredFunctions.forEach(funcName => {{
                    try {{
                        const func = window[funcName];
                        if (typeof func === 'function') {{
                            result.availableFunctions.push(funcName);
                            result.functionTypes[funcName] = 'function';
                        }} else if (func !== undefined) {{
                            result.functionTypes[funcName] = typeof func;
                            result.missingFunctions.push(funcName + ' (not a function)');
                        }} else {{
                            result.missingFunctions.push(funcName + ' (undefined)');
                        }}
                    }} catch(e) {{
                        result.missingFunctions.push(funcName + ' (error: ' + e.message + ')');
                    }}
                }});
                
                return result;
            }})();
            """
            
            result = tab.Runtime.evaluate(expression=function_check_js, timeout=self.timeout)
            
            if not result or "exceptionDetails" in result:
                health.errors.append("Failed to check function availability")
                return False
            
            func_data = result.get("result", {}).get("value", {})
            
            # Update health status
            health.functions_available = func_data.get("availableFunctions", [])
            missing_functions = func_data.get("missingFunctions", [])
            
            # Check if critical functions are missing (relaxed for NON_CRITICAL operations)
            critical_functions = self.REQUIRED_FUNCTIONS.get(operation_type, [])
            missing_critical = [f for f in critical_functions if f not in health.functions_available]
            
            if missing_critical and operation_type in [OperationType.CRITICAL, OperationType.IMPORTANT]:
                health.errors.append(f"Missing critical functions: {missing_critical}")
                return False
            
            # Log warnings for missing non-critical functions
            if missing_functions:
                self.logger.warning(f"Missing non-critical functions: {missing_functions}")
            
            return True
            
        except Exception as e:
            health.errors.append(f"Function availability check failed: {str(e)}")
            return False
    
    def quick_health_check(self, tab) -> bool:
        """Quick health check for basic connectivity"""
        try:
            result = tab.Runtime.evaluate(expression="typeof window", timeout=2.0)
            return result and result.get("result", {}).get("value") == "object"
        except:
            return False
    
    def get_tab_info(self, tab) -> dict:
        """Get basic tab information for logging"""
        try:
            result = tab.Runtime.evaluate(
                expression="({url: window.location.href, title: document.title})",
                timeout=2.0
            )
            if result and "result" in result:
                return result["result"].get("value", {})
        except:
            pass
        return {"url": "unknown", "title": "unknown"}

# ============================================================================
# OPERATION QUEUE FOR CONCURRENT SAFETY
# ============================================================================

class OperationQueue:
    """Thread-safe queue for tab operations to prevent conflicts"""
    
    def __init__(self, max_size: int = PERFORMANCE_THRESHOLDS["max_queue_size"]):
        self.queue = queue.Queue(maxsize=max_size)
        self.active_operations = 0
        self.lock = threading.Lock()
        self.max_concurrent = PERFORMANCE_THRESHOLDS["max_concurrent_ops"]
    
    def can_execute(self) -> bool:
        """Check if operation can be executed immediately"""
        with self.lock:
            return self.active_operations < self.max_concurrent
    
    def start_operation(self, operation_id: str) -> bool:
        """Mark operation as started"""
        with self.lock:
            if self.active_operations >= self.max_concurrent:
                return False
            self.active_operations += 1
            base_logger.debug(f"Started operation {operation_id}, active: {self.active_operations}")
            return True
    
    def finish_operation(self, operation_id: str):
        """Mark operation as finished"""
        with self.lock:
            self.active_operations = max(0, self.active_operations - 1)
            base_logger.debug(f"Finished operation {operation_id}, active: {self.active_operations}")

# ============================================================================
# RETRY STRATEGY CLASSES
# ============================================================================

class RetryStrategy:
    """Base class for retry strategies"""
    
    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts
    
    def should_retry(self, attempt: int, error: Exception, error_type: ErrorType) -> bool:
        """Determine if operation should be retried"""
        return attempt < self.max_attempts
    
    def get_backoff_time(self, attempt: int, error_type: ErrorType) -> float:
        """Get wait time before retry"""
        return 0.0
    
    def on_retry(self, attempt: int, error: Exception, operation_id: str):
        """Called before each retry attempt"""
        pass

class ImmediateRetryStrategy(RetryStrategy):
    """Immediate retry with minimal delay - for network errors"""
    
    def __init__(self, max_attempts: int = 3):
        super().__init__(max_attempts)
        self.backoff_times = [0.1, 0.2, 0.5]  # Very short delays
    
    def should_retry(self, attempt: int, error: Exception, error_type: ErrorType) -> bool:
        # Only retry network errors immediately
        return (attempt < self.max_attempts and 
                error_type == ErrorType.NETWORK_ERROR)
    
    def get_backoff_time(self, attempt: int, error_type: ErrorType) -> float:
        if attempt < len(self.backoff_times):
            return self.backoff_times[attempt]
        return self.backoff_times[-1]

class ExponentialBackoffStrategy(RetryStrategy):
    """Exponential backoff - for Chrome busy/overloaded scenarios"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
        super().__init__(max_attempts)
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def should_retry(self, attempt: int, error: Exception, error_type: ErrorType) -> bool:
        # Retry for Chrome busy and some unknown errors
        return (attempt < self.max_attempts and 
                error_type in [ErrorType.CHROME_BUSY, ErrorType.UNKNOWN_ERROR])
    
    def get_backoff_time(self, attempt: int, error_type: ErrorType) -> float:
        delay = self.base_delay * (2 ** attempt)  # 1s, 2s, 4s, 8s...
        return min(delay, self.max_delay)

class LinearBackoffStrategy(RetryStrategy):
    """Linear backoff - for tab recovery scenarios"""
    
    def __init__(self, max_attempts: int = 2, step_delay: float = 1.0):
        super().__init__(max_attempts)
        self.step_delay = step_delay
    
    def should_retry(self, attempt: int, error: Exception, error_type: ErrorType) -> bool:
        # Only retry tab errors with linear backoff
        return (attempt < self.max_attempts and 
                error_type == ErrorType.TAB_ERROR)
    
    def get_backoff_time(self, attempt: int, error_type: ErrorType) -> float:
        return self.step_delay * (attempt + 1)  # 1s, 2s, 3s...

class NoRetryStrategy(RetryStrategy):
    """No retry strategy - for JavaScript errors"""
    
    def __init__(self):
        super().__init__(max_attempts=0)
    
    def should_retry(self, attempt: int, error: Exception, error_type: ErrorType) -> bool:
        # Never retry JavaScript errors
        return False
    
    def get_backoff_time(self, attempt: int, error_type: ErrorType) -> float:
        return 0.0

class CircuitBreaker:
    """Circuit breaker pattern implementation for tab-level failure management"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0, 
                 half_open_limit: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_limit = half_open_limit
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_attempts = 0
        self.total_operations = 0
        self.success_count = 0
        
        self.lock = threading.Lock()
    
    def can_execute(self, operation_id: str) -> bool:
        """Check if operation can be executed based on circuit state"""
        with self.lock:
            self.total_operations += 1
            
            if self.state == CircuitState.CLOSED:
                return True
            
            elif self.state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if (self.last_failure_time and 
                    datetime.now() - self.last_failure_time >= timedelta(seconds=self.recovery_timeout)):
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_attempts = 0
                    operation_logger.log_circuit_breaker(
                        operation_id, "HALF_OPEN", self.failure_count
                    )
                    return True
                else:
                    return False
            
            elif self.state == CircuitState.HALF_OPEN:
                # Allow limited attempts in half-open state
                if self.half_open_attempts < self.half_open_limit:
                    self.half_open_attempts += 1
                    return True
                else:
                    return False
            
            return False
    
    def record_success(self, operation_id: str):
        """Record successful operation"""
        with self.lock:
            self.success_count += 1
            
            if self.state == CircuitState.HALF_OPEN:
                # Success in half-open state - close the circuit
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.half_open_attempts = 0
                operation_logger.log_circuit_breaker(
                    operation_id, "CLOSED_RECOVERY", 0
                )
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self, operation_id: str, error: Exception, error_type: ErrorType):
        """Record failed operation"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    operation_logger.log_circuit_breaker(
                        operation_id, "OPENED", self.failure_count
                    )
            
            elif self.state == CircuitState.HALF_OPEN:
                # Failure in half-open state - back to open
                self.state = CircuitState.OPEN
                operation_logger.log_circuit_breaker(
                    operation_id, "REOPENED", self.failure_count
                )
    
    def get_status(self) -> CircuitBreakerStatus:
        """Get current circuit breaker status"""
        with self.lock:
            success_rate = 0.0
            if self.total_operations > 0:
                success_rate = (self.success_count / self.total_operations) * 100
            
            return CircuitBreakerStatus(
                state=self.state,
                failure_count=self.failure_count,
                last_failure_time=self.last_failure_time,
                half_open_attempts=self.half_open_attempts,
                total_operations=self.total_operations,
                success_rate=success_rate
            )

class RetryStrategyFactory:
    """Factory for creating appropriate retry strategies based on error types"""
    
    @staticmethod
    def get_strategy(error_type: ErrorType, operation_type: OperationType) -> RetryStrategy:
        """Get appropriate retry strategy for error type and operation criticality"""
        
        if error_type == ErrorType.JAVASCRIPT_ERROR:
            return NoRetryStrategy()
        
        elif error_type == ErrorType.NETWORK_ERROR:
            max_attempts = RETRY_LIMITS.get(operation_type.value, 2)
            return ImmediateRetryStrategy(max_attempts=max_attempts)
        
        elif error_type == ErrorType.CHROME_BUSY:
            max_attempts = RETRY_LIMITS.get(operation_type.value, 2)
            return ExponentialBackoffStrategy(max_attempts=max_attempts)
        
        elif error_type == ErrorType.TAB_ERROR:
            max_attempts = min(2, RETRY_LIMITS.get(operation_type.value, 1))
            return LinearBackoffStrategy(max_attempts=max_attempts)
        
        else:  # UNKNOWN_ERROR
            max_attempts = RETRY_LIMITS.get(operation_type.value, 1)
            return ExponentialBackoffStrategy(max_attempts=max_attempts, base_delay=2.0)

# ============================================================================
# SAFE EVALUATE CORE IMPLEMENTATION
# ============================================================================

def safe_evaluate(tab, js_code: str, operation_type: OperationType = OperationType.IMPORTANT,
                 description: str = "", expected_type: str = None, 
                 timeout: float = None) -> OperationResult:
    """
    Safe wrapper for tab.Runtime.evaluate() with comprehensive validation and retry logic
    
    Args:
        tab: pychrome tab object
        js_code: JavaScript code to execute
        operation_type: Criticality level (CRITICAL, IMPORTANT, NON_CRITICAL)
        description: Human-readable description for logging
        expected_type: Expected JavaScript return type (optional)
        timeout: Custom timeout in seconds (optional)
        
    Returns:
        OperationResult with success status, value, and detailed error information
    """
    operation_id = generate_operation_id()
    start_time = time.time()
    
    # Get timeout based on operation type
    if timeout is None:
        timeout = OPERATION_TIMEOUTS.get(operation_type.value, 5.0)
    
    # Initialize result
    result = OperationResult(
        success=False,
        operation_id=operation_id,
        execution_time=0.0
    )
    
    # Get tab info for logging
    validator = TabHealthValidator()
    tab_info = validator.get_tab_info(tab)
    
    # Start operation logging
    operation_logger.start_operation(operation_id, operation_type, description, tab_info)
    
    try:
        # Validate tab health before execution
        health_status = validator.validate_tab_health(tab, operation_type)
        if not health_status.healthy:
            result.error = f"Tab health validation failed: {'; '.join(health_status.errors)}"
            result.error_type = ErrorType.TAB_ERROR
            operation_logger.log_failure(operation_id, Exception(result.error), ErrorType.TAB_ERROR)
            return result
        
        # Execute with retry logic
        retry_count = 0
        max_retries = RETRY_LIMITS.get(operation_type.value, 2)
        
        while retry_count <= max_retries:
            try:
                # Log the actual JavaScript being executed (truncated for security)
                js_preview = js_code[:100] + "..." if len(js_code) > 100 else js_code
                base_logger.debug(f"Executing JS: {js_preview}", extra={
                    "operation_id": operation_id,
                    "retry_count": retry_count
                })
                
                # Execute the JavaScript with timeout
                execute_start = time.time()
                raw_result = tab.Runtime.evaluate(expression=js_code, timeout=timeout)
                execute_time = time.time() - execute_start
                
                # Validate the response
                validation = validate_pychrome_response(raw_result, expected_type)
                
                if validation["status"] == ResponseStatus.SUCCESS:
                    # Success path
                    result.success = True
                    result.value = validation["value"]
                    result.execution_time = time.time() - start_time
                    result.retry_count = retry_count
                    
                    operation_logger.log_success(operation_id, result.value, result.execution_time)
                    return result
                
                elif validation["status"] == ResponseStatus.JAVASCRIPT_ERROR:
                    # JavaScript error - no retry
                    result.error = validation["error"]
                    result.error_type = ErrorType.JAVASCRIPT_ERROR
                    result.execution_time = time.time() - start_time
                    result.retry_count = retry_count
                    
                    js_error = JavaScriptExecutionError(
                        result.error, 
                        validation.get("exception_details", {}),
                        operation_id
                    )
                    operation_logger.log_failure(operation_id, js_error, ErrorType.JAVASCRIPT_ERROR, retry_count)
                    return result
                
                else:
                    # Other validation error - may retry
                    error_msg = validation["error"]
                    if not validation.get("retry_recommended", False):
                        result.error = error_msg
                        result.error_type = ErrorType.UNKNOWN_ERROR
                        result.execution_time = time.time() - start_time
                        result.retry_count = retry_count
                        
                        operation_logger.log_failure(operation_id, Exception(error_msg), ErrorType.UNKNOWN_ERROR, retry_count)
                        return result
                    
                    # Will retry - continue to retry logic below
                    raise ChromeCommunicationError(error_msg, ErrorType.UNKNOWN_ERROR, retry_count, operation_id)
                
            except Exception as e:
                # Classify the exception
                error_type = classify_exception(e)
                retry_count += 1
                
                # Check if we should retry
                strategy = RetryStrategyFactory.get_strategy(error_type, operation_type)
                
                if retry_count > max_retries or not strategy.should_retry(retry_count - 1, e, error_type):
                    # No more retries - final failure
                    result.error = str(e)
                    result.error_type = error_type
                    result.execution_time = time.time() - start_time
                    result.retry_count = retry_count - 1
                    
                    operation_logger.log_failure(operation_id, e, error_type, retry_count - 1)
                    return result
                
                # Calculate backoff time and wait
                backoff_time = strategy.get_backoff_time(retry_count - 1, error_type)
                
                operation_logger.log_retry(operation_id, retry_count, error_type, str(e), backoff_time)
                
                if backoff_time > 0:
                    time.sleep(backoff_time)
                
                # Continue to next retry attempt
                continue
        
        # If we exit the loop without returning, we've exhausted retries
        result.error = f"Exhausted {max_retries} retry attempts"
        result.error_type = ErrorType.UNKNOWN_ERROR
        result.execution_time = time.time() - start_time
        result.retry_count = max_retries
        
        operation_logger.log_failure(operation_id, Exception(result.error), ErrorType.UNKNOWN_ERROR, max_retries)
        return result
        
    except Exception as e:
        # Unexpected error in safe_evaluate itself
        result.error = f"safe_evaluate internal error: {str(e)}"
        result.error_type = ErrorType.UNKNOWN_ERROR
        result.execution_time = time.time() - start_time
        
        base_logger.error(f"safe_evaluate internal error: {e}", extra={
            "operation_id": operation_id,
            "error_message": str(e)
        })
        
        return result

# ============================================================================
# CHROME COMMUNICATION MANAGER
# ============================================================================

class ChromeCommunicationManager:
    """
    Central manager for Chrome communication with integrated safety features
    
    Coordinates:
    - Per-tab circuit breakers
    - Operation queues for concurrent safety
    - Health monitoring
    - Centralized logging and metrics
    """
    
    def __init__(self):
        self.tab_circuit_breakers = {}  # tab_id -> CircuitBreaker
        self.tab_operation_queues = {}  # tab_id -> OperationQueue
        self.tab_health_cache = {}      # tab_id -> (TabHealthStatus, timestamp)
        self.tab_references = {}        # tab_id -> tab object
        self.health_cache_ttl = 30.0    # seconds
        
        self.validator = TabHealthValidator()
        self.lock = threading.Lock()
        
        # Performance metrics
        self.metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "circuit_breaker_trips": 0,
            "average_execution_time": 0.0
        }
        
        base_logger.info("ChromeCommunicationManager initialized")
    
    def register_tab(self, tab_id: str, tab) -> bool:
        """
        Register a tab for managed communication
        
        Args:
            tab_id: Unique identifier for the tab
            tab: pychrome tab object
            
        Returns:
            True if registration successful
        """
        with self.lock:
            try:
                # Store tab reference
                self.tab_references[tab_id] = tab
                
                # Create circuit breaker for this tab
                if tab_id not in self.tab_circuit_breakers:
                    self.tab_circuit_breakers[tab_id] = CircuitBreaker(
                        failure_threshold=CIRCUIT_BREAKER_CONFIG["failure_threshold"],
                        recovery_timeout=CIRCUIT_BREAKER_CONFIG["recovery_timeout"],
                        half_open_limit=CIRCUIT_BREAKER_CONFIG["half_open_limit"]
                    )
                
                # Create operation queue for this tab
                if tab_id not in self.tab_operation_queues:
                    self.tab_operation_queues[tab_id] = OperationQueue()
                
                # Validate tab health
                health_status = self.validator.validate_tab_health(tab)
                self.tab_health_cache[tab_id] = (health_status, time.time())
                
                operation_logger.log_tab_health(tab_id, health_status)
                
                base_logger.info(f"Tab registered: {tab_id} - healthy: {health_status.healthy}")
                return health_status.healthy
                
            except Exception as e:
                base_logger.error(f"Failed to register tab {tab_id}: {e}")
                return False
    
    def execute_operation(self, tab_id: str, tab, js_code: str, 
                         operation_type: OperationType = OperationType.IMPORTANT,
                         description: str = "", expected_type: str = None,
                         timeout: float = None) -> OperationResult:
        """
        Execute JavaScript operation with full safety features
        
        Args:
            tab_id: Unique identifier for the tab
            tab: pychrome tab object
            js_code: JavaScript code to execute
            operation_type: Criticality level
            description: Human-readable description
            expected_type: Expected JavaScript return type
            timeout: Custom timeout in seconds
            
        Returns:
            OperationResult with execution details
        """
        operation_id = generate_operation_id()
        
        # Update metrics
        self.metrics["total_operations"] += 1
        
        try:
            # Check circuit breaker
            circuit_breaker = self.tab_circuit_breakers.get(tab_id)
            if circuit_breaker and not circuit_breaker.can_execute(operation_id):
                self.metrics["circuit_breaker_trips"] += 1
                return OperationResult(
                    success=False,
                    error="Circuit breaker is open",
                    error_type=ErrorType.UNKNOWN_ERROR,
                    operation_id=operation_id
                )
            
            # Check operation queue capacity
            operation_queue = self.tab_operation_queues.get(tab_id)
            if operation_queue and not operation_queue.start_operation(operation_id):
                return OperationResult(
                    success=False,
                    error="Operation queue full - too many concurrent operations",
                    error_type=ErrorType.UNKNOWN_ERROR,
                    operation_id=operation_id
                )
            
            try:
                # Execute the operation
                result = safe_evaluate(
                    tab=tab,
                    js_code=js_code,
                    operation_type=operation_type,
                    description=description,
                    expected_type=expected_type,
                    timeout=timeout
                )
                
                # Update circuit breaker
                if circuit_breaker:
                    if result.success:
                        circuit_breaker.record_success(operation_id)
                        self.metrics["successful_operations"] += 1
                    else:
                        circuit_breaker.record_failure(operation_id, Exception(result.error), result.error_type)
                        self.metrics["failed_operations"] += 1
                
                # Update performance metrics
                if result.execution_time > 0:
                    current_avg = self.metrics["average_execution_time"]
                    total_ops = self.metrics["total_operations"]
                    self.metrics["average_execution_time"] = (
                        (current_avg * (total_ops - 1) + result.execution_time) / total_ops
                    )
                
                return result
                
            finally:
                # Always finish operation in queue
                if operation_queue:
                    operation_queue.finish_operation(operation_id)
        
        except Exception as e:
            self.metrics["failed_operations"] += 1
            base_logger.error(f"Manager execution error for {tab_id}: {e}")
            return OperationResult(
                success=False,
                error=f"Manager error: {str(e)}",
                error_type=ErrorType.UNKNOWN_ERROR,
                operation_id=operation_id
            )
    
    def get_tab_status(self, tab_id: str) -> dict:
        """Get comprehensive status for a tab"""
        with self.lock:
            status = {
                "tab_id": tab_id,
                "circuit_breaker": None,
                "operation_queue": None,
                "health_status": None
            }
            
            # Circuit breaker status
            if tab_id in self.tab_circuit_breakers:
                cb_status = self.tab_circuit_breakers[tab_id].get_status()
                status["circuit_breaker"] = {
                    "state": cb_status.state.value,
                    "failure_count": cb_status.failure_count,
                    "success_rate": cb_status.success_rate
                }
            
            # Operation queue status
            if tab_id in self.tab_operation_queues:
                queue = self.tab_operation_queues[tab_id]
                status["operation_queue"] = {
                    "active_operations": queue.active_operations,
                    "max_concurrent": queue.max_concurrent
                }
            
            # Health status (cached)
            if tab_id in self.tab_health_cache:
                health, timestamp = self.tab_health_cache[tab_id]
                age = time.time() - timestamp
                status["health_status"] = {
                    "healthy": health.healthy,
                    "url": health.url,
                    "functions_available": len(health.functions_available),
                    "errors": health.errors,
                    "cache_age_seconds": age,
                    "stale": age > self.health_cache_ttl
                }
            
            return status
    
    def get_global_metrics(self) -> dict:
        """Get global performance metrics"""
        return self.metrics.copy()
    
    def get_safe_evaluator(self, tab_id: str):
        """Get a safe evaluator function bound to a specific tab"""
        def safe_evaluator(js_code: str, operation_type: OperationType = OperationType.IMPORTANT,
                          description: str = "", expected_type: str = None,
                          timeout: float = None) -> OperationResult:
            """Safe evaluator bound to this tab"""
            if tab_id not in self.tab_references:
                raise ChromeCommunicationError(f"Tab {tab_id} not registered")
            
            tab = self.tab_references[tab_id]  # Get tab from stored references
            return safe_evaluate(tab, js_code, operation_type, description, expected_type, timeout)
        
        return safe_evaluator
    
    def get_tab_health(self, tab_id: str) -> TabHealthStatus:
        """Get current tab health status"""
        if tab_id in self.tab_health_cache:
            health, timestamp = self.tab_health_cache[tab_id]
            # Return cached health if still fresh
            if time.time() - timestamp < self.health_cache_ttl:
                return health
        
        # Return None if no health data available
        return None
    
    def get_performance_stats(self, tab_id: str) -> dict:
        """Get performance statistics for a specific tab"""
        if tab_id not in self.tab_circuit_breakers:
            return {}
        
        # Get tab-specific metrics
        tab_stats = {
            "tab_id": tab_id,
            "circuit_breaker_state": self.tab_circuit_breakers[tab_id].get_status().state.value,
            "operations_count": 0,
            "avg_execution_time": 0.0,
            "error_rate": 0.0,
            "last_operation": None
        }
        
        # Add global metrics
        global_metrics = self.get_global_metrics()
        tab_stats.update(global_metrics)
        
        return tab_stats

# Default global manager instance
default_manager = ChromeCommunicationManager()

# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Create logs directory if it doesn't exist
import os
os.makedirs('logs', exist_ok=True)

base_logger.info("Chrome Communication Framework initialized")
base_logger.debug(f"Configuration: {OPERATION_TIMEOUTS}")
base_logger.debug(f"Retry limits: {RETRY_LIMITS}")
base_logger.debug(f"Circuit breaker config: {CIRCUIT_BREAKER_CONFIG}")

# Export main logger for external use
logger = base_logger
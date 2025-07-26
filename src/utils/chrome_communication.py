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
import websocket.exceptions

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
    
    if isinstance(exception, (websocket.exceptions.ConnectionClosed,
                             websocket.exceptions.ConnectionClosedError)):
        return ErrorType.NETWORK_ERROR
    
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
    
    def __init__(self, base_logger: logging.Logger):
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
            if not self._validate_page_state(tab, health):
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
    
    def _validate_page_state(self, tab, health: TabHealthStatus) -> bool:
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
            
            # Validate requirements
            if not health.tradovate_loaded:
                health.errors.append("Not on Tradovate domain")
                return False
            
            if health.ready_state != "complete":
                health.errors.append(f"Page not ready: {health.ready_state}")
                return False
            
            if not page_data.get("hasContent", False):
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
            
            # Check if critical functions are missing
            critical_functions = self.REQUIRED_FUNCTIONS.get(operation_type, [])
            missing_critical = [f for f in critical_functions if f not in health.functions_available]
            
            if missing_critical:
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
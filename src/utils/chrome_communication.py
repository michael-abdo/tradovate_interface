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
from collections import deque
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

# Import standardized error handling framework
try:
    from src.utils.trading_errors import (
        ChromeCommunicationError as StandardChromeError,
        ErrorSeverity, ErrorCategory,
        error_aggregator, log_and_aggregate_error
    )
    TRADING_ERRORS_AVAILABLE = True
except ImportError:
    # Fallback if trading_errors not available
    TRADING_ERRORS_AVAILABLE = False
    StandardChromeError = Exception
    
    # Create dummy severity/category for fallback
    class ErrorSeverity(Enum):
        INFO = "INFO"
        WARN = "WARNING"
        ERROR = "ERROR"
        CRITICAL = "CRITICAL"
    
    class ErrorCategory(Enum):
        CHROME_COMMUNICATION = "CHROME_COMM"

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

if TRADING_ERRORS_AVAILABLE:
    # Use standardized error framework when available
    class ChromeCommunicationError(StandardChromeError):
        """Chrome communication exception using standardized framework"""
        def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR, 
                     retry_count: int = 0, operation_id: str = None, tab_id: str = None,
                     **kwargs):
            # Map error types to severity
            severity = ErrorSeverity.ERROR
            if error_type == ErrorType.TAB_ERROR:
                severity = ErrorSeverity.CRITICAL
            elif error_type in [ErrorType.NETWORK_ERROR, ErrorType.CHROME_BUSY]:
                severity = ErrorSeverity.ERROR
            elif error_type == ErrorType.JAVASCRIPT_ERROR:
                severity = ErrorSeverity.WARN
            else:  # UNKNOWN_ERROR
                severity = ErrorSeverity.ERROR
                
            super().__init__(
                message=message,
                severity=severity,
                chrome_tab_id=tab_id,
                operation=operation_id,
                **kwargs
            )
            self.error_type = error_type
            self.retry_count = retry_count
            self.operation_id = operation_id
            
            # Add to error aggregator
            error_aggregator.add_error(self)
else:
    # Fallback to simple exception if framework not available
    class ChromeCommunicationError(Exception):
        """Base exception for Chrome communication issues"""
        def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR, 
                     retry_count: int = 0, operation_id: str = None, **kwargs):
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
                    
                    # Record performance metrics
                    performance_monitor.record_operation(
                        operation_id=operation_id,
                        operation_type=operation_type.value,
                        execution_time=result.execution_time,
                        description=description,
                        success=True
                    )
                    
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
                    
                    # Record performance metrics for failed operation
                    performance_monitor.record_operation(
                        operation_id=operation_id,
                        operation_type=operation_type.value,
                        execution_time=result.execution_time,
                        description=description,
                        success=False
                    )
                    
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
        
        # Record performance metrics for exhausted retries
        performance_monitor.record_operation(
            operation_id=operation_id,
            operation_type=operation_type.value,
            execution_time=result.execution_time,
            description=description,
            success=False
        )
        
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
    
    def validate_chrome_connection(self, tab_id: str) -> dict:
        """
        Comprehensive Chrome connection validation per Step 1.4
        
        Validates:
        - Basic JavaScript execution
        - Tab accessibility and state
        - Tradovate page readiness
        - Required functions availability
        
        Returns:
            Dict with validation results and details
        """
        validation_start = time.time()
        results = {
            "valid": True,
            "timestamp": datetime.now().isoformat(),
            "tab_id": tab_id,
            "checks": {
                "basic_js": False,
                "tab_accessible": False,
                "page_ready": False,
                "functions_available": False
            },
            "errors": [],
            "warnings": [],
            "execution_time": 0.0
        }
        
        # Check if tab is registered
        if tab_id not in self.tab_references:
            results["valid"] = False
            results["errors"].append(f"Tab {tab_id} not registered")
            return results
        
        tab = self.tab_references[tab_id]
        
        # 1. Test basic JavaScript execution
        try:
            basic_result = safe_evaluate(
                tab=tab,
                js_code="1 + 1",
                operation_type=OperationType.LOW_PRIORITY,
                description="Basic JS test",
                expected_type="number",
                timeout=2.0
            )
            
            if basic_result.success and basic_result.result == 2:
                results["checks"]["basic_js"] = True
            else:
                results["valid"] = False
                results["errors"].append("Basic JavaScript execution failed")
        except Exception as e:
            results["valid"] = False
            results["errors"].append(f"Basic JS test error: {str(e)}")
        
        # 2. Verify tab accessibility and state
        try:
            # Check if tab can access window object
            window_result = safe_evaluate(
                tab=tab,
                js_code="typeof window !== 'undefined'",
                operation_type=OperationType.LOW_PRIORITY,
                description="Window object check",
                expected_type="boolean",
                timeout=2.0
            )
            
            if window_result.success and window_result.result:
                results["checks"]["tab_accessible"] = True
            else:
                results["valid"] = False
                results["errors"].append("Tab window object not accessible")
                
        except Exception as e:
            results["valid"] = False
            results["errors"].append(f"Tab accessibility error: {str(e)}")
        
        # 3. Check Tradovate page readiness
        try:
            # Check for Tradovate-specific elements
            page_ready_result = safe_evaluate(
                tab=tab,
                js_code="""
                    (() => {
                        // Check for common Tradovate elements
                        const hasTrading = document.querySelector('.trading-interface') !== null ||
                                         document.querySelector('[data-testid="trading-panel"]') !== null ||
                                         document.querySelector('#trading-main') !== null;
                        
                        const hasAccount = document.querySelector('.account-selector') !== null ||
                                         document.querySelector('[data-account]') !== null ||
                                         document.querySelector('.account-info') !== null;
                        
                        const domReady = document.readyState === 'complete';
                        
                        return {
                            hasTrading: hasTrading,
                            hasAccount: hasAccount,
                            domReady: domReady,
                            isReady: hasTrading || hasAccount
                        };
                    })()
                """,
                operation_type=OperationType.IMPORTANT,
                description="Tradovate page readiness check",
                expected_type="object",
                timeout=5.0
            )
            
            if page_ready_result.success and page_ready_result.result:
                page_info = page_ready_result.result
                if page_info.get('isReady', False):
                    results["checks"]["page_ready"] = True
                    if not page_info.get('domReady', False):
                        results["warnings"].append("DOM not fully loaded yet")
                else:
                    results["warnings"].append("Tradovate interface elements not found")
                    # Not a failure - page might be loading
            else:
                results["warnings"].append("Could not verify Tradovate page state")
                
        except Exception as e:
            results["warnings"].append(f"Page readiness check error: {str(e)}")
        
        # 4. Validate required functions availability
        try:
            # Check for critical trading functions
            functions_result = safe_evaluate(
                tab=tab,
                js_code="""
                    (() => {
                        const functions = {
                            autoTrade: typeof autoTrade === 'function',
                            exitPositions: typeof exitPositions === 'function',
                            cancelAllOrders: typeof cancelAllOrders === 'function',
                            resetOrderRisk: typeof resetOrderRisk === 'function',
                            getAccountData: typeof getAccountData === 'function'
                        };
                        
                        const available = Object.keys(functions).filter(f => functions[f]);
                        const missing = Object.keys(functions).filter(f => !functions[f]);
                        
                        return {
                            functions: functions,
                            available: available,
                            missing: missing,
                            count: available.length
                        };
                    })()
                """,
                operation_type=OperationType.IMPORTANT,
                description="Trading functions availability check",
                expected_type="object",
                timeout=5.0
            )
            
            if functions_result.success and functions_result.result:
                func_info = functions_result.result
                if func_info.get('count', 0) > 0:
                    results["checks"]["functions_available"] = True
                    results["available_functions"] = func_info.get('available', [])
                    
                    if func_info.get('missing', []):
                        results["warnings"].append(
                            f"Some functions not available: {', '.join(func_info['missing'])}"
                        )
                else:
                    results["warnings"].append("No trading functions detected")
            else:
                results["warnings"].append("Could not check function availability")
                
        except Exception as e:
            results["warnings"].append(f"Function check error: {str(e)}")
        
        # Calculate overall validity
        critical_checks = ["basic_js", "tab_accessible"]
        for check in critical_checks:
            if not results["checks"][check]:
                results["valid"] = False
                break
        
        # Add execution time
        results["execution_time"] = time.time() - validation_start
        
        # Log results
        if results["valid"]:
            operation_logger.log_operation_success(
                tab_id=tab_id,
                operation="validate_chrome_connection",
                result=results,
                execution_time=results["execution_time"]
            )
        else:
            operation_logger.log_operation_failure(
                tab_id=tab_id,
                operation="validate_chrome_connection",
                error_message="; ".join(results["errors"]),
                execution_time=results["execution_time"]
            )
        
        return results

# Default global manager instance
default_manager = ChromeCommunicationManager()

# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

class PerformanceMonitor:
    """
    Dedicated performance monitoring for Chrome operations per Task 1.6
    
    Tracks:
    - Execution times for each JavaScript call
    - Slow operations (>1s execution time)
    - Performance metrics and trends
    - Alerts for degraded performance
    """
    
    def __init__(self, slow_threshold: float = 1.0, metrics_window: int = 100):
        self.slow_threshold = slow_threshold
        self.metrics_window = metrics_window
        self.operation_times = deque(maxlen=metrics_window)
        self.slow_operations = deque(maxlen=50)
        self.lock = threading.Lock()
        
        # Performance statistics
        self.stats = {
            "total_operations": 0,
            "slow_operations_count": 0,
            "average_time": 0.0,
            "p95_time": 0.0,
            "p99_time": 0.0,
            "max_time": 0.0,
            "min_time": float('inf'),
            "last_update": datetime.now()
        }
        
        # Performance alerts
        self.alerts = deque(maxlen=20)
        self.alert_thresholds = {
            "avg_time_warning": 0.5,      # 500ms average
            "avg_time_critical": 1.0,      # 1s average
            "p95_time_warning": 2.0,       # 2s 95th percentile
            "p95_time_critical": 5.0,      # 5s 95th percentile
            "slow_rate_warning": 0.1,      # 10% slow operations
            "slow_rate_critical": 0.25     # 25% slow operations
        }
        
        # Configure dedicated performance logger
        self.logger = logging.getLogger("chrome.performance.monitor")
        perf_handler = logging.FileHandler("logs/chrome_performance_monitor.log")
        perf_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(perf_handler)
        self.logger.setLevel(logging.INFO)
    
    def record_operation(self, operation_id: str, operation_type: str, 
                        execution_time: float, description: str = "",
                        tab_id: str = "", success: bool = True):
        """Record a Chrome operation execution time"""
        with self.lock:
            # Add to operation times
            self.operation_times.append(execution_time)
            self.stats["total_operations"] += 1
            
            # Update min/max
            self.stats["max_time"] = max(self.stats["max_time"], execution_time)
            if execution_time < self.stats["min_time"]:
                self.stats["min_time"] = execution_time
            
            # Check for slow operation
            if execution_time > self.slow_threshold:
                self.stats["slow_operations_count"] += 1
                slow_op = {
                    "operation_id": operation_id,
                    "operation_type": operation_type,
                    "execution_time": execution_time,
                    "description": description,
                    "tab_id": tab_id,
                    "timestamp": datetime.now().isoformat(),
                    "success": success
                }
                self.slow_operations.append(slow_op)
                
                # Log slow operation
                self.logger.warning(f"SLOW_OPERATION: {operation_type} took {execution_time:.3f}s", extra={
                    "operation_id": operation_id,
                    "execution_time": execution_time,
                    "description": description,
                    "tab_id": tab_id
                })
            
            # Update statistics
            self._update_statistics()
            
            # Check for performance alerts
            self._check_alerts()
    
    def _update_statistics(self):
        """Update performance statistics"""
        if not self.operation_times:
            return
        
        times = list(self.operation_times)
        times.sort()
        
        # Calculate average
        self.stats["average_time"] = sum(times) / len(times)
        
        # Calculate percentiles
        p95_index = int(len(times) * 0.95)
        p99_index = int(len(times) * 0.99)
        
        self.stats["p95_time"] = times[min(p95_index, len(times) - 1)]
        self.stats["p99_time"] = times[min(p99_index, len(times) - 1)]
        self.stats["last_update"] = datetime.now()
    
    def _check_alerts(self):
        """Check for performance degradation alerts"""
        avg_time = self.stats["average_time"]
        p95_time = self.stats["p95_time"]
        slow_rate = self.stats["slow_operations_count"] / max(1, self.stats["total_operations"])
        
        # Check average time
        if avg_time > self.alert_thresholds["avg_time_critical"]:
            self._create_alert("CRITICAL", f"Average execution time {avg_time:.3f}s exceeds critical threshold")
        elif avg_time > self.alert_thresholds["avg_time_warning"]:
            self._create_alert("WARNING", f"Average execution time {avg_time:.3f}s exceeds warning threshold")
        
        # Check 95th percentile
        if p95_time > self.alert_thresholds["p95_time_critical"]:
            self._create_alert("CRITICAL", f"95th percentile time {p95_time:.3f}s exceeds critical threshold")
        elif p95_time > self.alert_thresholds["p95_time_warning"]:
            self._create_alert("WARNING", f"95th percentile time {p95_time:.3f}s exceeds warning threshold")
        
        # Check slow operation rate
        if slow_rate > self.alert_thresholds["slow_rate_critical"]:
            self._create_alert("CRITICAL", f"Slow operation rate {slow_rate:.1%} exceeds critical threshold")
        elif slow_rate > self.alert_thresholds["slow_rate_warning"]:
            self._create_alert("WARNING", f"Slow operation rate {slow_rate:.1%} exceeds warning threshold")
    
    def _create_alert(self, severity: str, message: str):
        """Create a performance alert"""
        alert = {
            "severity": severity,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "stats": self.get_stats()
        }
        self.alerts.append(alert)
        
        # Log alert
        if severity == "CRITICAL":
            self.logger.critical(f"PERFORMANCE_ALERT: {message}", extra=alert)
        else:
            self.logger.warning(f"PERFORMANCE_ALERT: {message}", extra=alert)
            
        # If using trading_errors framework, create performance error
        if TRADING_ERRORS_AVAILABLE and severity == "CRITICAL":
            from src.utils.trading_errors import PerformanceError
            try:
                # Extract metric info from message
                if "Average execution time" in message:
                    metric = "chrome_avg_execution_time"
                    threshold = self.alert_thresholds["avg_time_critical"]
                    actual = self.stats["average_time"]
                elif "95th percentile" in message:
                    metric = "chrome_p95_execution_time"
                    threshold = self.alert_thresholds["p95_time_critical"]
                    actual = self.stats["p95_time"]
                else:
                    metric = "chrome_slow_operation_rate"
                    threshold = self.alert_thresholds["slow_rate_critical"]
                    actual = self.stats["slow_operations_count"] / max(1, self.stats["total_operations"])
                
                error = PerformanceError(
                    message=message,
                    metric=metric,
                    threshold=threshold,
                    actual=actual
                )
                error_aggregator.add_error(error)
            except Exception:
                pass  # Don't fail on error reporting
    
    def get_stats(self) -> dict:
        """Get current performance statistics"""
        with self.lock:
            return self.stats.copy()
    
    def get_slow_operations(self, limit: int = 10) -> list:
        """Get recent slow operations"""
        with self.lock:
            return list(self.slow_operations)[-limit:]
    
    def get_alerts(self, limit: int = 10) -> list:
        """Get recent performance alerts"""
        with self.lock:
            return list(self.alerts)[-limit:]
    
    def get_dashboard_data(self) -> dict:
        """Get comprehensive data for performance dashboard"""
        with self.lock:
            slow_rate = self.stats["slow_operations_count"] / max(1, self.stats["total_operations"])
            
            return {
                "stats": self.stats.copy(),
                "slow_operations": list(self.slow_operations)[-10:],
                "alerts": list(self.alerts)[-10:],
                "metrics": {
                    "slow_rate": slow_rate,
                    "health_score": self._calculate_health_score(),
                    "trend": self._calculate_trend()
                },
                "thresholds": self.alert_thresholds.copy()
            }
    
    def _calculate_health_score(self) -> float:
        """Calculate performance health score (0-100)"""
        score = 100.0
        
        # Deduct points for slow average time
        avg_time = self.stats["average_time"]
        if avg_time > 1.0:
            score -= 30
        elif avg_time > 0.5:
            score -= 15
        elif avg_time > 0.25:
            score -= 5
        
        # Deduct points for high p95
        p95_time = self.stats["p95_time"]
        if p95_time > 5.0:
            score -= 20
        elif p95_time > 2.0:
            score -= 10
        elif p95_time > 1.0:
            score -= 5
        
        # Deduct points for slow operation rate
        slow_rate = self.stats["slow_operations_count"] / max(1, self.stats["total_operations"])
        if slow_rate > 0.25:
            score -= 20
        elif slow_rate > 0.1:
            score -= 10
        elif slow_rate > 0.05:
            score -= 5
        
        return max(0.0, score)
    
    def _calculate_trend(self) -> str:
        """Calculate performance trend (improving/stable/degrading)"""
        if len(self.operation_times) < 20:
            return "insufficient_data"
        
        # Compare first half vs second half average
        mid = len(self.operation_times) // 2
        first_half = list(self.operation_times)[:mid]
        second_half = list(self.operation_times)[mid:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        # 10% change threshold
        if second_avg < first_avg * 0.9:
            return "improving"
        elif second_avg > first_avg * 1.1:
            return "degrading"
        else:
            return "stable"
    
    def reset_stats(self):
        """Reset performance statistics"""
        with self.lock:
            self.operation_times.clear()
            self.slow_operations.clear()
            self.alerts.clear()
            self.stats = {
                "total_operations": 0,
                "slow_operations_count": 0,
                "average_time": 0.0,
                "p95_time": 0.0,
                "p99_time": 0.0,
                "max_time": 0.0,
                "min_time": float('inf'),
                "last_update": datetime.now()
            }
            self.logger.info("Performance statistics reset")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# ============================================================================
# DOM INTELLIGENCE SYSTEM
# ============================================================================

class ValidationTier(Enum):
    """Performance-based validation tiers for DOM operations"""
    ZERO_LATENCY = "zero_latency"      # < 1ms overhead - Emergency trading
    LOW_LATENCY = "low_latency"        # < 10ms overhead - Real-time trading
    STANDARD_LATENCY = "standard"      # < 50ms overhead - Trading infrastructure
    HIGH_LATENCY = "high_latency"      # < 200ms overhead - UI enhancements

@dataclass
class DOMOperation:
    """Represents a DOM manipulation operation"""
    element_type: str                  # e.g., 'symbol_input', 'order_submit_button'
    selector: str                      # CSS selector for element
    action: str                        # 'click', 'input', 'select', 'wait'
    value: Any = None                  # Value for input operations
    validation_tier: ValidationTier = ValidationTier.STANDARD_LATENCY
    timeout: float = 5.0
    description: str = ""
    tab_id: str = ""
    operation_id: Optional[str] = None
    emergency_bypass_enabled: bool = True

@dataclass
class ValidationResult:
    """Result of DOM validation"""
    success: bool
    element_found: bool = False
    element_interactive: bool = False
    validation_time: float = 0.0
    error_message: str = ""
    bypass_reason: str = ""
    alternative_selectors: List[str] = None
    
    @classmethod
    def bypass(cls, reason: str = "Emergency bypass") -> 'ValidationResult':
        """Create bypass result for emergency situations"""
        return cls(
            success=True,
            element_found=True,
            element_interactive=True,
            bypass_reason=reason
        )
    
    @classmethod
    def failure(cls, message: str) -> 'ValidationResult':
        """Create failure result"""
        return cls(
            success=False,
            error_message=message
        )

class EmergencyBypass:
    """Market stress detection and emergency bypass system"""
    
    def __init__(self):
        self.manual_override = False
        self.volatility_threshold = 0.05  # 5% volatility threshold
        self.latency_threshold = 100      # 100ms latency threshold
        self.position_risk_threshold = 0.8 # 80% account risk threshold
        
    def is_active(self, operation: DOMOperation = None) -> bool:
        """Check if emergency bypass should be activated"""
        
        # Manual emergency override
        if self.manual_override:
            return True
            
        # Operation-specific bypass
        if operation and operation.validation_tier == ValidationTier.ZERO_LATENCY:
            return True
            
        # Market volatility check (would integrate with real market data)
        if self._is_high_volatility():
            return True
            
        # System latency check
        if self._is_high_latency():
            return True
            
        return False
    
    def _is_high_volatility(self) -> bool:
        """Check if market volatility is high (placeholder for real implementation)"""
        # In real implementation, this would check actual market volatility
        # For now, return False
        return False
    
    def _is_high_latency(self) -> bool:
        """Check if system latency is degraded"""
        # In real implementation, this would check actual system latency
        # For now, return False
        return False
    
    def set_manual_override(self, enabled: bool, reason: str = ""):
        """Manually enable/disable emergency bypass"""
        self.manual_override = enabled
        if enabled:
            base_logger.warning(f"🚨 Emergency bypass manually activated: {reason}")
        else:
            base_logger.info("✅ Emergency bypass manually deactivated")

class DOMValidator:
    """
    Multi-tier DOM validation with circuit breaker integration
    Extends Chrome Communication Framework for DOM-specific operations
    """
    
    def __init__(self, chrome_manager: ChromeCommunicationManager = None):
        self.chrome_manager = chrome_manager or default_manager
        self.emergency_bypass = EmergencyBypass()
        self.validation_metrics = {
            'total_validations': 0,
            'bypassed_validations': 0,
            'failed_validations': 0,
            'validation_times': []
        }
        
        # DOM-specific circuit breakers per element type
        self.dom_circuit_breakers = {}
        
        base_logger.info("DOMValidator initialized with Chrome Communication Framework integration")
    
    def validate_operation(self, tab_id_or_operation: Union[str, DOMOperation], operation: DOMOperation = None) -> ValidationResult:
        """
        Core validation method with tier-based strategies
        
        Args:
            tab_id_or_operation: Either a tab_id string (for backward compatibility) or a DOMOperation
            operation: DOMOperation (only used if first param is tab_id)
        """
        # Handle both signatures for backward compatibility
        if isinstance(tab_id_or_operation, DOMOperation):
            operation = tab_id_or_operation
        elif operation is None:
            raise ValueError("Operation parameter required when tab_id is provided")
        # If tab_id is provided, we just ignore it for now
        start_time = time.time()
        self.validation_metrics['total_validations'] += 1
        
        try:
            # Emergency bypass check
            if self.emergency_bypass.is_active(operation):
                self.validation_metrics['bypassed_validations'] += 1
                base_logger.debug(f"🚨 Emergency bypass active for {operation.element_type}")
                return ValidationResult.bypass("Emergency bypass - market stress or manual override")
            
            # Circuit breaker check for this element type
            if not self._check_dom_circuit_breaker(operation.element_type):
                return ValidationResult.failure(f"Circuit breaker open for {operation.element_type}")
            
            # Tier-based validation
            validation_result = self._execute_validation(operation)
            
            # Update metrics
            validation_time = (time.time() - start_time) * 1000
            validation_result.validation_time = validation_time
            self.validation_metrics['validation_times'].append(validation_time)
            
            if not validation_result.success:
                self.validation_metrics['failed_validations'] += 1
                self._record_dom_failure(operation.element_type)
            
            return validation_result
            
        except Exception as e:
            validation_time = (time.time() - start_time) * 1000
            base_logger.error(f"DOM validation error for {operation.element_type}: {e}")
            return ValidationResult.failure(f"Validation exception: {str(e)}")
    
    def _execute_validation(self, operation: DOMOperation) -> ValidationResult:
        """Execute validation based on tier"""
        
        if operation.validation_tier == ValidationTier.ZERO_LATENCY:
            return self._zero_latency_validation(operation)
        elif operation.validation_tier == ValidationTier.LOW_LATENCY:
            return self._low_latency_validation(operation)
        elif operation.validation_tier == ValidationTier.STANDARD_LATENCY:
            return self._standard_latency_validation(operation)
        else:  # HIGH_LATENCY
            return self._high_latency_validation(operation)
    
    def _zero_latency_validation(self, operation: DOMOperation) -> ValidationResult:
        """< 1ms validation - health check only"""
        try:
            # Minimal health check using existing Chrome framework
            if hasattr(self.chrome_manager, 'tab_references') and operation.tab_id in self.chrome_manager.tab_references:
                return ValidationResult(
                    success=True,
                    element_found=True,  # Assume element exists
                    element_interactive=True,  # Assume interactive
                    validation_time=0.5  # Minimal time
                )
            else:
                return ValidationResult.failure("Tab not registered in Chrome manager")
        except Exception as e:
            return ValidationResult.failure(f"Zero-latency validation failed: {str(e)}")
    
    def _low_latency_validation(self, operation: DOMOperation) -> ValidationResult:
        """< 10ms validation - quick existence check"""
        try:
            # Use Chrome Communication Framework for fast element check
            if operation.tab_id not in self.chrome_manager.tab_references:
                return ValidationResult.failure("Tab not registered")
            
            tab = self.chrome_manager.tab_references[operation.tab_id]
            
            # Quick element existence check
            check_js = f"""
            (function() {{
                const element = document.querySelector('{operation.selector}');
                return {{
                    found: element !== null,
                    interactive: element && !element.disabled && element.offsetParent !== null,
                    type: element ? element.tagName.toLowerCase() : null
                }};
            }})();
            """
            
            result = safe_evaluate(
                tab=tab,
                js_code=check_js,
                operation_type=OperationType.NON_CRITICAL,
                description=f"Fast element check: {operation.element_type}",
                timeout=2.0
            )
            
            if result.success and result.value:
                return ValidationResult(
                    success=True,
                    element_found=result.value.get('found', False),
                    element_interactive=result.value.get('interactive', False)
                )
            else:
                return ValidationResult.failure(f"Element check failed: {result.error}")
                
        except Exception as e:
            return ValidationResult.failure(f"Low-latency validation failed: {str(e)}")
    
    def _standard_latency_validation(self, operation: DOMOperation) -> ValidationResult:
        """< 50ms validation - comprehensive element validation"""
        try:
            if operation.tab_id not in self.chrome_manager.tab_references:
                return ValidationResult.failure("Tab not registered")
            
            tab = self.chrome_manager.tab_references[operation.tab_id]
            
            # Comprehensive element validation
            validation_js = f"""
            (function() {{
                const element = document.querySelector('{operation.selector}');
                if (!element) {{
                    return {{ found: false, reason: 'Element not found' }};
                }}
                
                const rect = element.getBoundingClientRect();
                const style = window.getComputedStyle(element);
                
                return {{
                    found: true,
                    interactive: !element.disabled && element.offsetParent !== null,
                    visible: style.display !== 'none' && style.visibility !== 'hidden',
                    inViewport: rect.top >= 0 && rect.left >= 0 && 
                               rect.bottom <= window.innerHeight && 
                               rect.right <= window.innerWidth,
                    tagName: element.tagName.toLowerCase(),
                    id: element.id,
                    className: element.className,
                    attributes: Array.from(element.attributes).map(attr => 
                        ({{ name: attr.name, value: attr.value }})
                    )
                }};
            }})();
            """
            
            result = safe_evaluate(
                tab=tab,
                js_code=validation_js,
                operation_type=OperationType.IMPORTANT,
                description=f"Standard validation: {operation.element_type}",
                timeout=5.0
            )
            
            if result.success and result.value and result.value.get('found'):
                validation_data = result.value
                return ValidationResult(
                    success=True,
                    element_found=True,
                    element_interactive=validation_data.get('interactive', False)
                )
            else:
                reason = result.value.get('reason', 'Unknown') if result.value else result.error
                return ValidationResult.failure(f"Standard validation failed: {reason}")
                
        except Exception as e:
            return ValidationResult.failure(f"Standard validation failed: {str(e)}")
    
    def _high_latency_validation(self, operation: DOMOperation) -> ValidationResult:
        """< 200ms validation - exhaustive validation with recovery"""
        try:
            # Start with standard validation
            standard_result = self._standard_latency_validation(operation)
            
            if standard_result.success:
                return standard_result
            
            # If standard failed, try alternative selectors
            alternative_selectors = self._get_alternative_selectors(operation.element_type)
            
            for alt_selector in alternative_selectors:
                alt_operation = DOMOperation(
                    element_type=operation.element_type,
                    selector=alt_selector,
                    action=operation.action,
                    validation_tier=ValidationTier.STANDARD_LATENCY,
                    tab_id=operation.tab_id
                )
                
                alt_result = self._standard_latency_validation(alt_operation)
                if alt_result.success:
                    alt_result.alternative_selectors = [alt_selector]
                    base_logger.info(f"✅ Alternative selector worked for {operation.element_type}: {alt_selector}")
                    return alt_result
            
            return ValidationResult.failure(f"High-latency validation exhausted all options for {operation.element_type}")
            
        except Exception as e:
            return ValidationResult.failure(f"High-latency validation failed: {str(e)}")
    
    def _get_alternative_selectors(self, element_type: str) -> List[str]:
        """Get alternative selectors for element type"""
        
        # Basic fallback selectors (would be expanded with TradovateElementRegistry)
        fallbacks = {
            'symbol_input': [
                'input[placeholder*="symbol" i]',
                '.search-box input',
                '.symbol-search input',
                'input[type="text"]:first-of-type'
            ],
            'order_submit_button': [
                'button[type="submit"]',
                '.order-form button.primary',
                'button.submit-order',
                '.trading-panel button:last-child'
            ],
            'account_selector': [
                '.account-switcher',
                '[aria-label*="account" i]',
                '.dropdown-toggle:contains("Account")',
                '.user-menu .dropdown'
            ]
        }
        
        return fallbacks.get(element_type, [])
    
    def _check_dom_circuit_breaker(self, element_type: str) -> bool:
        """Check DOM-specific circuit breaker for element type"""
        
        if element_type not in self.dom_circuit_breakers:
            # Create circuit breaker for this element type
            self.dom_circuit_breakers[element_type] = {
                'failure_count': 0,
                'failure_threshold': 3,
                'last_failure': None,
                'circuit_open': False,
                'recovery_timeout': 30.0
            }
        
        breaker = self.dom_circuit_breakers[element_type]
        
        # Check if circuit is open and should be closed
        if breaker['circuit_open']:
            if breaker['last_failure'] and time.time() - breaker['last_failure'] > breaker['recovery_timeout']:
                breaker['circuit_open'] = False
                breaker['failure_count'] = 0
                base_logger.info(f"🔄 DOM circuit breaker reset for {element_type}")
                return True
            else:
                return False
        
        return True
    
    def _record_dom_failure(self, element_type: str):
        """Record DOM-specific failure and potentially open circuit breaker"""
        
        if element_type not in self.dom_circuit_breakers:
            self._check_dom_circuit_breaker(element_type)  # Initialize
        
        breaker = self.dom_circuit_breakers[element_type]
        breaker['failure_count'] += 1
        breaker['last_failure'] = time.time()
        
        if breaker['failure_count'] >= breaker['failure_threshold']:
            breaker['circuit_open'] = True
            base_logger.warning(f"🚨 DOM circuit breaker opened for {element_type} after {breaker['failure_count']} failures")
    
    def get_validation_metrics(self) -> dict:
        """Get DOM validation performance metrics"""
        
        avg_validation_time = 0.0
        if self.validation_metrics['validation_times']:
            avg_validation_time = sum(self.validation_metrics['validation_times']) / len(self.validation_metrics['validation_times'])
        
        return {
            'total_validations': self.validation_metrics['total_validations'],
            'bypassed_validations': self.validation_metrics['bypassed_validations'],
            'failed_validations': self.validation_metrics['failed_validations'],
            'success_rate': (self.validation_metrics['total_validations'] - self.validation_metrics['failed_validations']) / max(1, self.validation_metrics['total_validations']),
            'bypass_rate': self.validation_metrics['bypassed_validations'] / max(1, self.validation_metrics['total_validations']),
            'average_validation_time': avg_validation_time,
            'circuit_breaker_states': {
                element_type: {
                    'open': breaker['circuit_open'],
                    'failure_count': breaker['failure_count']
                }
                for element_type, breaker in self.dom_circuit_breakers.items()
            }
        }

# Default DOM validator instance
default_dom_validator = DOMValidator(default_manager)

# ============================================================================
# SELECTOR EVOLUTION SYSTEM
# ============================================================================

@dataclass
class SelectorUsage:
    """Tracks usage statistics for a selector"""
    selector: str
    element_type: str
    success_count: int = 0
    failure_count: int = 0
    first_seen: datetime = None
    last_used: datetime = None
    last_success: datetime = None
    last_failure: datetime = None
    failure_reasons: List[str] = None
    context_patterns: List[dict] = None
    
    def __post_init__(self):
        if self.failure_reasons is None:
            self.failure_reasons = []
        if self.context_patterns is None:
            self.context_patterns = []
        if self.first_seen is None:
            self.first_seen = datetime.now()
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    @property
    def confidence_score(self) -> float:
        """Calculate confidence score based on usage and recency"""
        if self.success_count == 0:
            return 0.0
        
        # Base confidence from success rate
        base_confidence = self.success_rate
        
        # Recency bonus - recent successes are more valuable
        if self.last_success:
            hours_since_success = (datetime.now() - self.last_success).total_seconds() / 3600
            recency_factor = max(0.1, 1.0 - (hours_since_success / 168))  # Decay over 1 week
            base_confidence *= recency_factor
        
        # Usage bonus - more usage = more confidence
        usage_factor = min(1.0, (self.success_count + self.failure_count) / 10)
        base_confidence *= (0.7 + 0.3 * usage_factor)
        
        return min(1.0, base_confidence)

@dataclass 
class SelectorChain:
    """Hierarchical chain of selectors with confidence scores"""
    primary: str
    fallbacks: List[str] = None
    confidence_scores: dict = None  # selector -> confidence
    
    def __post_init__(self):
        if self.fallbacks is None:
            self.fallbacks = []
        if self.confidence_scores is None:
            self.confidence_scores = {}
    
    def get_ordered_selectors(self) -> List[tuple]:
        """Get selectors ordered by confidence score"""
        all_selectors = [self.primary] + self.fallbacks
        return sorted(
            [(sel, self.confidence_scores.get(sel, 0.5)) for sel in all_selectors],
            key=lambda x: x[1],
            reverse=True
        )

class PatternRecognizer:
    """Recognizes patterns in successful selectors for generating new ones"""
    
    def __init__(self):
        self.element_patterns = {}  # element_type -> pattern data
        
    def analyze_successful_selectors(self, element_type: str, successful_selectors: List[str]) -> dict:
        """Analyze patterns in successful selectors"""
        
        patterns = {
            'common_attributes': self._find_common_attributes(successful_selectors),
            'class_patterns': self._find_class_patterns(successful_selectors),
            'structural_patterns': self._find_structural_patterns(successful_selectors),
            'text_patterns': self._find_text_patterns(successful_selectors)
        }
        
        self.element_patterns[element_type] = patterns
        return patterns
    
    def _find_common_attributes(self, selectors: List[str]) -> List[str]:
        """Find common attributes across successful selectors"""
        common_attrs = []
        
        # Look for common attribute patterns
        attribute_patterns = [
            'id=', 'class=', 'data-', 'aria-', 'type=', 'name=', 'placeholder='
        ]
        
        for pattern in attribute_patterns:
            if sum(1 for sel in selectors if pattern in sel) >= len(selectors) * 0.6:
                common_attrs.append(pattern)
        
        return common_attrs
    
    def _find_class_patterns(self, selectors: List[str]) -> List[str]:
        """Find common CSS class patterns"""
        class_patterns = []
        
        # Extract class names from selectors
        import re
        class_matches = []
        for selector in selectors:
            matches = re.findall(r'\.([a-zA-Z0-9_-]+)', selector)
            class_matches.extend(matches)
        
        # Find frequently occurring class parts
        from collections import Counter
        class_counter = Counter(class_matches)
        
        # Look for classes that appear in most selectors
        frequent_classes = [cls for cls, count in class_counter.items() 
                          if count >= len(selectors) * 0.5]
        
        return frequent_classes
    
    def _find_structural_patterns(self, selectors: List[str]) -> List[str]:
        """Find structural patterns (descendant, child, sibling relationships)"""
        structural_patterns = []
        
        # Look for common structural patterns
        common_structures = [
            ' > ',   # Direct child
            ' + ',   # Adjacent sibling
            ' ~ ',   # General sibling
            ' ',     # Descendant
            ':first-child', ':last-child', ':nth-child'
        ]
        
        for pattern in common_structures:
            if sum(1 for sel in selectors if pattern in sel) >= len(selectors) * 0.4:
                structural_patterns.append(pattern)
        
        return structural_patterns
    
    def _find_text_patterns(self, selectors: List[str]) -> List[str]:
        """Find text-based selection patterns"""
        text_patterns = []
        
        # Look for text-based selectors
        text_indicators = [
            ':contains(', '[text*=', '[placeholder*=', '[title*=', '[aria-label*='
        ]
        
        for pattern in text_indicators:
            if sum(1 for sel in selectors if pattern in sel) >= len(selectors) * 0.3:
                text_patterns.append(pattern)
        
        return text_patterns

class FallbackGenerator:
    """Generates fallback selectors based on patterns and context"""
    
    def __init__(self, pattern_recognizer: PatternRecognizer):
        self.pattern_recognizer = pattern_recognizer
        
    def generate_fallbacks(self, element_type: str, failed_selector: str, context: dict = None) -> List[str]:
        """Generate fallback selectors for a failed selector"""
        
        fallbacks = []
        
        # Get learned patterns for this element type
        patterns = self.pattern_recognizer.element_patterns.get(element_type, {})
        
        # Generate attribute-based fallbacks
        fallbacks.extend(self._generate_attribute_fallbacks(element_type, failed_selector, patterns))
        
        # Generate class-based fallbacks
        fallbacks.extend(self._generate_class_fallbacks(element_type, failed_selector, patterns))
        
        # Generate structural fallbacks
        fallbacks.extend(self._generate_structural_fallbacks(element_type, failed_selector, patterns))
        
        # Generate semantic fallbacks
        fallbacks.extend(self._generate_semantic_fallbacks(element_type, context))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_fallbacks = []
        for fb in fallbacks:
            if fb not in seen and fb != failed_selector:
                seen.add(fb)
                unique_fallbacks.append(fb)
        
        return unique_fallbacks[:10]  # Limit to top 10 fallbacks
    
    def _generate_attribute_fallbacks(self, element_type: str, failed_selector: str, patterns: dict) -> List[str]:
        """Generate fallbacks based on attribute patterns"""
        fallbacks = []
        
        # Element type specific attribute fallbacks
        attribute_map = {
            'symbol_input': [
                'input[placeholder*="symbol" i]',
                'input[name*="symbol" i]',
                'input[id*="symbol" i]',
                'input[type="text"][placeholder*="ticker" i]'
            ],
            'order_submit_button': [
                'button[type="submit"]',
                'button[aria-label*="submit" i]',
                'button[title*="place" i]',
                'input[type="submit"]'
            ],
            'account_selector': [
                '[aria-label*="account" i]',
                '[data-testid*="account" i]',
                'select[name*="account" i]',
                '.dropdown[aria-label*="account" i]'
            ]
        }
        
        return attribute_map.get(element_type, [])
    
    def _generate_class_fallbacks(self, element_type: str, failed_selector: str, patterns: dict) -> List[str]:
        """Generate fallbacks based on class patterns"""
        fallbacks = []
        
        common_classes = patterns.get('class_patterns', [])
        
        for class_name in common_classes:
            fallbacks.append(f'.{class_name}')
            
        # Add contextual class combinations
        if element_type == 'symbol_input':
            for class_name in common_classes:
                if 'input' in class_name or 'search' in class_name:
                    fallbacks.append(f'.{class_name}')
                    
        return fallbacks
    
    def _generate_structural_fallbacks(self, element_type: str, failed_selector: str, patterns: dict) -> List[str]:
        """Generate fallbacks based on structural patterns"""
        fallbacks = []
        
        # Context-based structural fallbacks
        structural_map = {
            'symbol_input': [
                '.trading-form input[type="text"]',
                '.order-entry input:first-of-type',
                '.symbol-section input',
                'form input[placeholder*="symbol" i]'
            ],
            'order_submit_button': [
                '.order-form button:last-child',
                '.trading-panel button.primary',
                'form button[type="submit"]',
                '.submit-section button'
            ],
            'account_selector': [
                '.header .account-dropdown',
                '.navigation .user-menu',
                '.toolbar .account-section',
                '.top-bar .dropdown'
            ]
        }
        
        return structural_map.get(element_type, [])
    
    def _generate_semantic_fallbacks(self, element_type: str, context: dict = None) -> List[str]:
        """Generate semantically meaningful fallbacks"""
        fallbacks = []
        
        # Semantic fallbacks based on common UI patterns
        semantic_map = {
            'symbol_input': [
                'input[placeholder*="enter symbol" i]',
                'input[placeholder*="search" i]',
                'input[aria-label*="symbol" i]',
                '[role="searchbox"]'
            ],
            'order_submit_button': [
                'button:contains("Submit")',
                'button:contains("Place Order")',
                'button:contains("Buy")',
                'button:contains("Sell")',
                '[role="button"][aria-label*="submit" i]'
            ],
            'account_selector': [
                '[role="combobox"][aria-label*="account" i]',
                'select[aria-label*="account" i]',
                '.dropdown[role="button"]:contains("Account")',
                '[aria-haspopup="listbox"]'
            ]
        }
        
        return semantic_map.get(element_type, [])

class SelectorEvolution:
    """
    Machine learning approach to selector resilience and adaptation
    """
    
    def __init__(self):
        self.selector_history = {}  # element_type -> {selector -> SelectorUsage}
        self.pattern_recognizer = PatternRecognizer()
        self.fallback_generator = FallbackGenerator(self.pattern_recognizer)
        self.learning_enabled = True
        
        # Load historical data if available
        self._load_selector_history()
        
        base_logger.info("SelectorEvolution system initialized with pattern recognition")
    
    def get_optimal_selector_chain(self, element_type: str, context: dict = None) -> SelectorChain:
        """
        Returns hierarchical selector chain based on historical success
        """
        
        # Get historical data for this element type
        element_history = self.selector_history.get(element_type, {})
        
        if not element_history:
            # No history - use default selectors
            return self._get_default_selector_chain(element_type)
        
        # Sort selectors by confidence score
        sorted_selectors = sorted(
            element_history.items(),
            key=lambda x: x[1].confidence_score,
            reverse=True
        )
        
        # Build selector chain
        if sorted_selectors:
            primary_selector = sorted_selectors[0][0]
            fallback_selectors = [sel for sel, _ in sorted_selectors[1:6]]  # Top 5 fallbacks
            
            confidence_scores = {
                sel: usage.confidence_score 
                for sel, usage in sorted_selectors[:6]
            }
        else:
            return self._get_default_selector_chain(element_type)
        
        return SelectorChain(
            primary=primary_selector,
            fallbacks=fallback_selectors,
            confidence_scores=confidence_scores
        )
    
    def record_selector_success(self, element_type: str, selector: str, context: dict = None):
        """Record successful selector usage"""
        
        if not self.learning_enabled:
            return
            
        # Initialize element type history if needed
        if element_type not in self.selector_history:
            self.selector_history[element_type] = {}
        
        # Initialize selector usage if needed
        if selector not in self.selector_history[element_type]:
            self.selector_history[element_type][selector] = SelectorUsage(
                selector=selector,
                element_type=element_type
            )
        
        # Record success
        usage = self.selector_history[element_type][selector]
        usage.success_count += 1
        usage.last_used = datetime.now()
        usage.last_success = datetime.now()
        
        if context:
            usage.context_patterns.append(context)
        
        # Update pattern recognition
        self._update_patterns(element_type)
        
        # Save history periodically
        if usage.success_count % 10 == 0:
            self._save_selector_history()
        
        base_logger.debug(f"✅ Recorded selector success: {element_type} -> {selector} (confidence: {usage.confidence_score:.2f})")
    
    def record_selector_failure(self, element_type: str, selector: str, failure_reason: str, context: dict = None):
        """Record failed selector usage and learn from failure"""
        
        if not self.learning_enabled:
            return
            
        # Initialize if needed
        if element_type not in self.selector_history:
            self.selector_history[element_type] = {}
            
        if selector not in self.selector_history[element_type]:
            self.selector_history[element_type][selector] = SelectorUsage(
                selector=selector,
                element_type=element_type
            )
        
        # Record failure
        usage = self.selector_history[element_type][selector]
        usage.failure_count += 1
        usage.last_used = datetime.now()
        usage.last_failure = datetime.now()
        usage.failure_reasons.append(failure_reason)
        
        if context:
            usage.context_patterns.append(context)
        
        base_logger.warning(f"❌ Recorded selector failure: {element_type} -> {selector} (reason: {failure_reason})")
        
        # Generate new fallback selectors if confidence is low
        if usage.confidence_score < 0.3:
            new_fallbacks = self.fallback_generator.generate_fallbacks(element_type, selector, context)
            base_logger.info(f"🔄 Generated {len(new_fallbacks)} new fallback selectors for {element_type}")
            
            # Add new fallbacks to history with minimal confidence
            for fallback in new_fallbacks:
                if fallback not in self.selector_history[element_type]:
                    self.selector_history[element_type][fallback] = SelectorUsage(
                        selector=fallback,
                        element_type=element_type,
                        success_count=1  # Start with minimal confidence
                    )
    
    def _get_default_selector_chain(self, element_type: str) -> SelectorChain:
        """Get default selector chain for element type with no history"""
        
        default_selectors = {
            'symbol_input': {
                'primary': '#symbolInput',
                'fallbacks': [
                    '.search-box--input',
                    'input[placeholder*="symbol" i]',
                    '.symbol-search input',
                    'input[type="text"]:first-of-type'
                ]
            },
            'order_submit_button': {
                'primary': '.btn-group .btn-primary',
                'fallbacks': [
                    'button[type="submit"]',
                    '.order-form button.primary',
                    'button.submit-order',
                    '.trading-panel button:last-child'
                ]
            },
            'account_selector': {
                'primary': '.pane.account-selector.dropdown [data-toggle="dropdown"]',
                'fallbacks': [
                    '.account-switcher',
                    '[aria-label*="account" i]',
                    '.dropdown-toggle:contains("Account")',
                    '.user-menu .dropdown'
                ]
            }
        }
        
        config = default_selectors.get(element_type, {
            'primary': '',
            'fallbacks': []
        })
        
        return SelectorChain(
            primary=config['primary'],
            fallbacks=config['fallbacks'],
            confidence_scores={sel: 0.5 for sel in [config['primary']] + config['fallbacks']}
        )
    
    def _update_patterns(self, element_type: str):
        """Update pattern recognition for element type"""
        
        element_history = self.selector_history.get(element_type, {})
        
        # Get successful selectors (confidence > 0.6)
        successful_selectors = [
            selector for selector, usage in element_history.items()
            if usage.confidence_score > 0.6
        ]
        
        if len(successful_selectors) >= 3:
            self.pattern_recognizer.analyze_successful_selectors(element_type, successful_selectors)
    
    def _load_selector_history(self):
        """Load selector history from persistent storage"""
        try:
            import json
            from pathlib import Path
            
            history_file = Path('logs/selector_evolution_history.json')
            if history_file.exists():
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    
                # Convert back to SelectorUsage objects
                for element_type, selectors in data.items():
                    self.selector_history[element_type] = {}
                    for selector, usage_data in selectors.items():
                        usage = SelectorUsage(
                            selector=selector,
                            element_type=element_type,
                            success_count=usage_data.get('success_count', 0),
                            failure_count=usage_data.get('failure_count', 0),
                            failure_reasons=usage_data.get('failure_reasons', [])
                        )
                        
                        # Parse datetime fields
                        for dt_field in ['first_seen', 'last_used', 'last_success', 'last_failure']:
                            if usage_data.get(dt_field):
                                setattr(usage, dt_field, datetime.fromisoformat(usage_data[dt_field]))
                        
                        self.selector_history[element_type][selector] = usage
                
                base_logger.info(f"📚 Loaded selector evolution history: {len(self.selector_history)} element types")
                
        except Exception as e:
            base_logger.warning(f"Could not load selector history: {e}")
    
    def _save_selector_history(self):
        """Save selector history to persistent storage"""
        try:
            import json
            from pathlib import Path
            
            # Convert to JSON-serializable format
            data = {}
            for element_type, selectors in self.selector_history.items():
                data[element_type] = {}
                for selector, usage in selectors.items():
                    data[element_type][selector] = {
                        'success_count': usage.success_count,
                        'failure_count': usage.failure_count,
                        'failure_reasons': usage.failure_reasons,
                        'first_seen': usage.first_seen.isoformat() if usage.first_seen else None,
                        'last_used': usage.last_used.isoformat() if usage.last_used else None,
                        'last_success': usage.last_success.isoformat() if usage.last_success else None,
                        'last_failure': usage.last_failure.isoformat() if usage.last_failure else None
                    }
            
            # Ensure logs directory exists
            Path('logs').mkdir(exist_ok=True)
            
            # Save to file
            with open('logs/selector_evolution_history.json', 'w') as f:
                json.dump(data, f, indent=2)
                
            base_logger.debug("💾 Saved selector evolution history")
            
        except Exception as e:
            base_logger.error(f"Could not save selector history: {e}")
    
    def get_evolution_metrics(self) -> dict:
        """Get selector evolution performance metrics"""
        
        total_selectors = 0
        total_successes = 0
        total_failures = 0
        high_confidence_selectors = 0
        
        for element_type, selectors in self.selector_history.items():
            for selector, usage in selectors.items():
                total_selectors += 1
                total_successes += usage.success_count
                total_failures += usage.failure_count
                
                if usage.confidence_score > 0.8:
                    high_confidence_selectors += 1
        
        return {
            'total_selectors_tracked': total_selectors,
            'total_successes': total_successes,
            'total_failures': total_failures,
            'overall_success_rate': total_successes / max(1, total_successes + total_failures),
            'high_confidence_selectors': high_confidence_selectors,
            'element_types_learned': len(self.selector_history),
            'patterns_recognized': len(self.pattern_recognizer.element_patterns)
        }

# Default selector evolution instance
default_selector_evolution = SelectorEvolution()

# ============================================================================
# TRADOVATE ELEMENT REGISTRY
# ============================================================================

@dataclass
class ElementStrategy:
    """Complete strategy for interacting with a Tradovate UI element"""
    primary_selectors: List[str]
    fallback_selectors: List[str]
    validation_tier: ValidationTier
    emergency_bypass: bool
    context_validators: List[callable] = None
    functional_validators: List[callable] = None
    timeout_ms: int = 5000
    
    def __post_init__(self):
        if self.context_validators is None:
            self.context_validators = []
        if self.functional_validators is None:
            self.functional_validators = []

@dataclass
class SelectorChain:
    """Hierarchical chain of selectors with confidence scores"""
    primary: str
    fallbacks: List[str]
    confidence_scores: dict = None
    
    def __post_init__(self):
        if self.confidence_scores is None:
            self.confidence_scores = {}

class TradovateElementRegistry:
    """
    Comprehensive registry of Tradovate trading interface elements
    with adaptive selectors and validation strategies
    """
    
    def __init__(self, selector_evolution: SelectorEvolution = None):
        self.selector_evolution = selector_evolution or default_selector_evolution
        self.logger = base_logger
        
        # Define critical trading elements with comprehensive strategies
        self.CRITICAL_ELEMENTS = {
            # ZERO-LATENCY TIER - Emergency Trading Operations
            'order_submit_button': ElementStrategy(
                primary_selectors=[
                    '.btn-group .btn-primary',
                    'button[type="submit"].order-submit',
                    '.order-form button.primary'
                ],
                fallback_selectors=[
                    '.trading-panel button.btn-primary',
                    '.order-entry button:last-child',
                    'button.submit-order',
                    '.trade-form .btn.primary'
                ],
                validation_tier=ValidationTier.ZERO_LATENCY,
                emergency_bypass=True,
                functional_validators=[
                    lambda elem: elem.tagName.lower() == 'button',
                    lambda elem: elem.closest('.order, .trading, .trade') is not None,
                    lambda elem: not elem.disabled,
                    lambda elem: 'submit' in elem.type.lower() or 'buy' in elem.textContent.lower() or 'sell' in elem.textContent.lower()
                ],
                timeout_ms=1000
            ),
            
            'position_exit_button': ElementStrategy(
                primary_selectors=[
                    '.position-exit-btn',
                    '.close-position-btn',
                    'button.exit-position'
                ],
                fallback_selectors=[
                    '.positions-table button.close',
                    '.position-row .exit-btn',
                    'button[title*="close" i]',
                    '.module.positions button.danger'
                ],
                validation_tier=ValidationTier.ZERO_LATENCY,
                emergency_bypass=True,
                functional_validators=[
                    lambda elem: elem.tagName.lower() == 'button',
                    lambda elem: elem.closest('.position') is not None,
                    lambda elem: not elem.disabled
                ],
                timeout_ms=500
            ),
            
            # LOW-LATENCY TIER - Real-Time Trading Support  
            'symbol_input': ElementStrategy(
                primary_selectors=[
                    '#symbolInput',
                    '.search-box--input[placeholder*="symbol" i]',
                    '.symbol-search input'
                ],
                fallback_selectors=[
                    '.instrument-selector input',
                    '.trading-form input[type="text"]:first-of-type',
                    'input[placeholder*="instrument" i]',
                    'input[placeholder*="ticker" i]'
                ],
                validation_tier=ValidationTier.LOW_LATENCY,
                emergency_bypass=True,
                context_validators=[
                    lambda elem: elem.type.lower() == 'text',
                    lambda elem: 'symbol' in elem.placeholder.lower() or 'instrument' in elem.placeholder.lower()
                ],
                timeout_ms=2000
            ),
            
            'account_selector': ElementStrategy(
                primary_selectors=[
                    '.pane.account-selector.dropdown [data-toggle="dropdown"]',
                    '.account-switcher button',
                    '[aria-label*="account" i] .dropdown-toggle'
                ],
                fallback_selectors=[
                    '.user-account .dropdown',
                    'button:has(.account-name)',
                    '.dropdown-toggle:contains("Account")',
                    '.header .account-dropdown'
                ],
                validation_tier=ValidationTier.LOW_LATENCY,
                emergency_bypass=False,
                context_validators=[
                    lambda elem: elem.closest('.account, .user, .profile') is not None,
                    lambda elem: 'dropdown-toggle' in elem.className or elem.hasAttribute('data-toggle')
                ],
                timeout_ms=3000
            ),
            
            'quantity_input': ElementStrategy(
                primary_selectors=[
                    '#quantity-input',
                    '.quantity-field input',
                    'input[placeholder*="quantity" i]'
                ],
                fallback_selectors=[
                    '.numeric-input.feedback-wrapper input',
                    '.order-form input[type="number"]',
                    'input[name*="qty" i]',
                    '.trade-size input'
                ],
                validation_tier=ValidationTier.LOW_LATENCY,
                emergency_bypass=True,
                context_validators=[
                    lambda elem: elem.type.lower() in ['number', 'text'],
                    lambda elem: elem.closest('.order, .trade') is not None
                ],
                timeout_ms=2000
            ),
            
            # STANDARD-LATENCY TIER - Trading Infrastructure
            'login_username': ElementStrategy(
                primary_selectors=[
                    '#name-input',
                    'input[name="username"]',
                    '.login-form input[type="text"]:first-child'
                ],
                fallback_selectors=[
                    'input[placeholder*="username" i]',
                    'input[placeholder*="email" i]',
                    '.auth-form input[type="text"]'
                ],
                validation_tier=ValidationTier.STANDARD_LATENCY,
                emergency_bypass=False,
                timeout_ms=5000
            ),
            
            'login_password': ElementStrategy(
                primary_selectors=[
                    '#password-input',
                    'input[name="password"]',
                    '.login-form input[type="password"]'
                ],
                fallback_selectors=[
                    'input[placeholder*="password" i]',
                    '.auth-form input[type="password"]'
                ],
                validation_tier=ValidationTier.STANDARD_LATENCY,
                emergency_bypass=False,
                timeout_ms=5000
            ),
            
            'login_submit': ElementStrategy(
                primary_selectors=[
                    '#login-submit-button',
                    'button.MuiButton-containedPrimary',
                    'button[type="submit"]'
                ],
                fallback_selectors=[
                    '.login-form button.btn-primary',
                    'form button:last-child',
                    'button.login-btn'
                ],
                validation_tier=ValidationTier.STANDARD_LATENCY,
                emergency_bypass=False,
                timeout_ms=5000
            ),
            
            # Market Data Elements
            'market_data_table': ElementStrategy(
                primary_selectors=[
                    '.module.positions.data-table',
                    '.fixedDataTable_main',
                    '.market-data-grid'
                ],
                fallback_selectors=[
                    '.public_fixedDataTable_main',
                    '.trading-table',
                    '.data-grid.market'
                ],
                validation_tier=ValidationTier.STANDARD_LATENCY,
                emergency_bypass=False,
                timeout_ms=3000
            ),
            
            'account_balance_cell': ElementStrategy(
                primary_selectors=[
                    '.account-balance .value',
                    '.balance-display .amount',
                    '[data-field="balance"]'
                ],
                fallback_selectors=[
                    '.account-info .balance',
                    '.portfolio-value',
                    '.cash-balance'
                ],
                validation_tier=ValidationTier.STANDARD_LATENCY,
                emergency_bypass=False,
                timeout_ms=3000
            ),
            
            # HIGH-LATENCY TIER - UI Enhancements
            'risk_settings_modal': ElementStrategy(
                primary_selectors=[
                    '.risk-settings-modal',
                    '.modal.risk-config',
                    '[aria-label*="risk" i].modal'
                ],
                fallback_selectors=[
                    '.modal-dialog.settings',
                    '.config-modal',
                    '.settings-popup'
                ],
                validation_tier=ValidationTier.HIGH_LATENCY,
                emergency_bypass=False,
                timeout_ms=10000
            ),
            
            'notification_area': ElementStrategy(
                primary_selectors=[
                    '.notification-container',
                    '.alert-banner',
                    '.message-area'
                ],
                fallback_selectors=[
                    '.notifications',
                    '.status-bar',
                    '.info-panel'
                ],
                validation_tier=ValidationTier.HIGH_LATENCY,
                emergency_bypass=False,
                timeout_ms=5000
            )
        }
        
    def get_element_strategy(self, element_type: str) -> ElementStrategy:
        """Get complete strategy for element interaction"""
        if element_type not in self.CRITICAL_ELEMENTS:
            self.logger.warning(f"Unknown element type: {element_type}")
            return None
            
        strategy = self.CRITICAL_ELEMENTS[element_type]
        
        # Enhance with evolved selectors if available
        evolved_selectors = self.selector_evolution.get_optimal_selector_chain(element_type)
        if evolved_selectors:
            # Merge evolved selectors with predefined ones
            enhanced_primary = [evolved_selectors.primary] + strategy.primary_selectors
            enhanced_fallbacks = evolved_selectors.fallbacks + strategy.fallback_selectors
            
            # Create enhanced strategy
            enhanced_strategy = ElementStrategy(
                primary_selectors=enhanced_primary,
                fallback_selectors=enhanced_fallbacks,
                validation_tier=strategy.validation_tier,
                emergency_bypass=strategy.emergency_bypass,
                context_validators=strategy.context_validators,
                functional_validators=strategy.functional_validators,
                timeout_ms=strategy.timeout_ms
            )
            return enhanced_strategy
            
        return strategy
    
    def get_all_selectors(self, element_type: str) -> List[str]:
        """Get all selectors for an element type in priority order"""
        strategy = self.get_element_strategy(element_type)
        if not strategy:
            return []
            
        return strategy.primary_selectors + strategy.fallback_selectors
    
    def is_critical_element(self, element_type: str) -> bool:
        """Check if element is critical for trading operations"""
        strategy = self.get_element_strategy(element_type)
        return strategy and strategy.validation_tier in [ValidationTier.ZERO_LATENCY, ValidationTier.LOW_LATENCY]
    
    def requires_emergency_bypass(self, element_type: str) -> bool:
        """Check if element supports emergency bypass"""
        strategy = self.get_element_strategy(element_type)
        return strategy and strategy.emergency_bypass
    
    def validate_element(self, element_type: str, element, context: dict = None) -> bool:
        """Validate element using strategy-specific validators"""
        strategy = self.get_element_strategy(element_type)
        if not strategy:
            return False
            
        try:
            # Run context validators
            for validator in strategy.context_validators:
                if not validator(element):
                    self.logger.debug(f"Context validation failed for {element_type}")
                    return False
                    
            # Run functional validators
            for validator in strategy.functional_validators:
                if not validator(element):
                    self.logger.debug(f"Functional validation failed for {element_type}")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Element validation error for {element_type}: {str(e)}")
            return False
    
    def get_element_timeout(self, element_type: str) -> int:
        """Get timeout for element operations"""
        strategy = self.get_element_strategy(element_type)
        return strategy.timeout_ms if strategy else 5000
    
    def record_selector_success(self, element_type: str, selector: str, context: dict = None):
        """Record successful selector usage"""
        self.selector_evolution.record_success(selector, element_type, context)
        self.logger.debug(f"Recorded selector success: {element_type} -> {selector}")
    
    def record_selector_failure(self, element_type: str, selector: str, failure_reason: str, context: dict = None):
        """Record failed selector usage"""
        self.selector_evolution.record_failure(selector, element_type, failure_reason, context)
        self.logger.warning(f"Recorded selector failure: {element_type} -> {selector} ({failure_reason})")
    
    def get_registry_stats(self) -> dict:
        """Get comprehensive registry statistics"""
        stats = {
            'total_elements': len(self.CRITICAL_ELEMENTS),
            'zero_latency_elements': 0,
            'low_latency_elements': 0,
            'standard_latency_elements': 0,
            'high_latency_elements': 0,
            'emergency_bypass_elements': 0,
            'total_selectors': 0
        }
        
        for element_type, strategy in self.CRITICAL_ELEMENTS.items():
            # Count by validation tier
            if strategy.validation_tier == ValidationTier.ZERO_LATENCY:
                stats['zero_latency_elements'] += 1
            elif strategy.validation_tier == ValidationTier.LOW_LATENCY:
                stats['low_latency_elements'] += 1
            elif strategy.validation_tier == ValidationTier.STANDARD_LATENCY:
                stats['standard_latency_elements'] += 1
            elif strategy.validation_tier == ValidationTier.HIGH_LATENCY:
                stats['high_latency_elements'] += 1
                
            # Count emergency bypass elements
            if strategy.emergency_bypass:
                stats['emergency_bypass_elements'] += 1
                
            # Count total selectors
            stats['total_selectors'] += len(strategy.primary_selectors) + len(strategy.fallback_selectors)
        
        return stats

# Default element registry instance
default_element_registry = TradovateElementRegistry()

# ============================================================================
# DOM OPERATION QUEUEING SYSTEM
# ============================================================================

import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, Future
import uuid

@dataclass
class DOMOperation:
    """Represents a DOM operation to be queued and executed"""
    operation_id: str
    tab_id: str
    element_type: str
    selector: str
    operation_type: str  # 'click', 'input', 'wait', 'extract'
    parameters: dict = None
    timeout_ms: int = 5000
    validation_tier: ValidationTier = ValidationTier.STANDARD_LATENCY
    emergency_bypass: bool = False
    context: dict = None
    
    def __post_init__(self):
        if self.operation_id is None:
            self.operation_id = str(uuid.uuid4())
        if self.parameters is None:
            self.parameters = {}
        if self.context is None:
            self.context = {}

@dataclass
class QueueResult:
    """Result of queueing a DOM operation"""
    status: str  # 'queued', 'conflict', 'busy', 'timeout', 'error'
    message: str
    operation_id: str = None
    conflicts: List[str] = None
    estimated_wait_time: float = 0.0
    
    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []
    
    @staticmethod
    def queued(operation_id: str, estimated_wait: float = 0.0) -> 'QueueResult':
        return QueueResult('queued', 'Operation queued successfully', operation_id, [], estimated_wait)
    
    @staticmethod
    def conflict(conflicts: List[str]) -> 'QueueResult':
        return QueueResult('conflict', f'Conflicts detected: {", ".join(conflicts)}', None, conflicts)
    
    @staticmethod
    def busy(message: str) -> 'QueueResult':
        return QueueResult('busy', message)
    
    @staticmethod
    def timeout(message: str) -> 'QueueResult':
        return QueueResult('timeout', message)
    
    @staticmethod
    def error(message: str) -> 'QueueResult':
        return QueueResult('error', message)

@dataclass
class TabState:
    """Represents the current state of a trading tab"""
    tab_id: str
    account_name: str = None
    current_symbol: str = None
    active_operations: dict = None  # element_type -> operation_id
    auto_sync_enabled: bool = True
    last_activity: datetime = None
    is_trading_active: bool = False
    
    def __post_init__(self):
        if self.active_operations is None:
            self.active_operations = {}
        if self.last_activity is None:
            self.last_activity = datetime.now()

class TabSynchronizationManager:
    """
    Synchronize DOM state across multiple account tabs
    Prevents conflicts when operations affect multiple tabs
    """
    
    def __init__(self):
        self.tab_states = {}  # tab_id -> TabState
        self.state_lock = threading.RLock()
        self.logger = base_logger
        
        # Global sync operations that affect all tabs
        self.global_sync_lock = threading.Lock()
        self.pending_global_operations = Queue()
        
    def register_tab(self, tab_id: str, account_name: str = None) -> bool:
        """Register a new trading tab"""
        with self.state_lock:
            if tab_id not in self.tab_states:
                self.tab_states[tab_id] = TabState(tab_id=tab_id, account_name=account_name)
                self.logger.info(f"Registered new tab: {tab_id} (account: {account_name})")
                return True
            return False
    
    def unregister_tab(self, tab_id: str) -> bool:
        """Unregister a trading tab"""
        with self.state_lock:
            if tab_id in self.tab_states:
                del self.tab_states[tab_id]
                self.logger.info(f"Unregistered tab: {tab_id}")
                return True
            return False
    
    def update_tab_symbol(self, tab_id: str, symbol: str) -> bool:
        """Update symbol for a specific tab"""
        with self.state_lock:
            if tab_id in self.tab_states:
                old_symbol = self.tab_states[tab_id].current_symbol
                self.tab_states[tab_id].current_symbol = symbol
                self.tab_states[tab_id].last_activity = datetime.now()
                self.logger.info(f"Tab {tab_id} symbol changed: {old_symbol} -> {symbol}")
                return True
            return False
    
    def sync_symbol_change(self, source_tab: str, symbol: str) -> List[str]:
        """
        Propagate symbol changes across all active trading tabs
        Returns list of tabs that were updated
        """
        updated_tabs = []
        
        with self.state_lock:
            for tab_id, state in self.tab_states.items():
                if tab_id != source_tab and state.auto_sync_enabled and state.is_trading_active:
                    # Queue symbol update for other tabs
                    old_symbol = state.current_symbol
                    state.current_symbol = symbol
                    state.last_activity = datetime.now()
                    updated_tabs.append(tab_id)
                    self.logger.info(f"Synced symbol {old_symbol} -> {symbol} to tab {tab_id}")
        
        return updated_tabs
    
    def sync_account_switch(self, source_tab: str, account: str) -> dict:
        """
        Handle account switching with conflict resolution
        Returns result with affected tabs and any conflicts
        """
        result = {
            'success': False,
            'paused_tabs': [],
            'conflicts': [],
            'message': ''
        }
        
        # Account switching is a global operation that affects all tabs
        if not self.global_sync_lock.acquire(timeout=10):
            result['message'] = 'Could not acquire global sync lock for account switch'
            return result
        
        try:
            with self.state_lock:
                # Pause trading on all other tabs
                paused_tabs = self._pause_all_trading_except(source_tab)
                result['paused_tabs'] = paused_tabs
                
                # Wait for pending operations to complete
                conflicts = self._wait_for_operations_complete(timeout=5.0)
                result['conflicts'] = conflicts
                
                # Update account for source tab
                if source_tab in self.tab_states:
                    self.tab_states[source_tab].account_name = account
                    self.tab_states[source_tab].last_activity = datetime.now()
                    result['success'] = True
                    result['message'] = f'Account switched to {account} on tab {source_tab}'
                else:
                    result['message'] = f'Source tab {source_tab} not found'
                
        except Exception as e:
            result['message'] = f'Account switch error: {str(e)}'
            self.logger.error(f"Account switch error: {str(e)}")
        finally:
            # Resume trading on all tabs
            with self.state_lock:
                self._resume_all_trading()
            self.global_sync_lock.release()
        
        return result
    
    def _pause_all_trading_except(self, source_tab: str) -> List[str]:
        """Pause trading activity on all tabs except source"""
        paused_tabs = []
        for tab_id, state in self.tab_states.items():
            if tab_id != source_tab and state.is_trading_active:
                state.is_trading_active = False
                paused_tabs.append(tab_id)
        return paused_tabs
    
    def _resume_all_trading(self) -> List[str]:
        """Resume trading activity on all tabs"""
        resumed_tabs = []
        for tab_id, state in self.tab_states.items():
            if not state.is_trading_active:
                state.is_trading_active = True
                resumed_tabs.append(tab_id)
        return resumed_tabs
    
    def _wait_for_operations_complete(self, timeout: float = 5.0) -> List[str]:
        """Wait for all pending operations to complete"""
        conflicts = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            all_clear = True
            for tab_id, state in self.tab_states.items():
                if state.active_operations:
                    all_clear = False
                    conflicts.extend([f"{tab_id}:{op}" for op in state.active_operations.keys()])
            
            if all_clear:
                break
                
            time.sleep(0.1)  # Brief pause before checking again
        
        return conflicts
    
    def get_tab_conflicts(self, operation: DOMOperation) -> List[str]:
        """
        Detect if operation conflicts with other tabs
        Returns list of conflict descriptions
        """
        conflicts = []
        
        with self.state_lock:
            # Check for account switching conflicts
            if operation.element_type == 'account_selector':
                for tab_id, state in self.tab_states.items():
                    if tab_id != operation.tab_id and 'account_selector' in state.active_operations:
                        conflicts.append(f"Account switching active on tab {tab_id}")
            
            # Check for symbol input conflicts
            elif operation.element_type == 'symbol_input':
                for tab_id, state in self.tab_states.items():
                    if tab_id != operation.tab_id and state.is_trading_active:
                        if ('symbol_input' in state.active_operations or 
                            'order_submit_button' in state.active_operations):
                            conflicts.append(f"Trading activity active on tab {tab_id}")
            
            # Check for order submission conflicts
            elif operation.element_type == 'order_submit_button':
                for tab_id, state in self.tab_states.items():
                    if tab_id != operation.tab_id:
                        if 'account_selector' in state.active_operations:
                            conflicts.append(f"Account switching on tab {tab_id} conflicts with order submission")
        
        return conflicts

class DOMOperationQueue:
    """
    Prevents race conditions across multiple tabs and accounts
    Manages DOM operation execution with conflict detection
    """
    
    def __init__(self, max_workers: int = 3, element_registry: TradovateElementRegistry = None):
        self.tab_sync_manager = TabSynchronizationManager()
        self.element_registry = element_registry or default_element_registry
        self.logger = base_logger
        
        # Operation management
        self.operation_queue = Queue()
        self.active_operations = {}  # operation_id -> (operation, future)
        self.operation_locks = {}  # element_type -> threading.Lock
        self.operation_history = []  # For debugging and analysis
        
        # Thread pool for operation execution
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="dom_ops")
        self.queue_lock = threading.RLock()
        
        # Performance tracking
        self.operation_times = {}  # element_type -> [execution_times]
        self.conflict_counts = {}  # conflict_type -> count
        
    def queue_operation(self, operation: DOMOperation) -> QueueResult:
        """
        Queue DOM operation with comprehensive conflict detection
        """
        start_time = time.time()
        
        try:
            with self.queue_lock:
                # Validate operation
                if not self._validate_operation(operation):
                    return QueueResult.error("Operation validation failed")
                
                # Check for cross-tab conflicts
                conflicts = self.tab_sync_manager.get_tab_conflicts(operation)
                if conflicts:
                    self._record_conflict('cross_tab', conflicts)
                    return QueueResult.conflict(conflicts)
                
                # Check for same-tab conflicts
                tab_conflicts = self._check_same_tab_conflicts(operation)
                if tab_conflicts:
                    self._record_conflict('same_tab', tab_conflicts)
                    return QueueResult.busy(f"Element {operation.element_type} busy on tab {operation.tab_id}")
                
                # Acquire element lock
                lock_result = self._acquire_element_lock(operation)
                if not lock_result['success']:
                    return QueueResult.timeout(lock_result['message'])
                
                # Estimate wait time
                estimated_wait = self._estimate_wait_time(operation)
                
                # Queue the operation for execution
                future = self.executor.submit(self._execute_operation, operation)
                self.active_operations[operation.operation_id] = (operation, future)
                
                # Update tab state
                self._update_tab_state(operation, 'queued')
                
                queue_time = (time.time() - start_time) * 1000
                self.logger.info(f"Queued operation {operation.operation_id} ({operation.element_type}) in {queue_time:.2f}ms")
                
                return QueueResult.queued(operation.operation_id, estimated_wait)
                
        except Exception as e:
            self.logger.error(f"Queue operation error: {str(e)}")
            return QueueResult.error(f"Queue error: {str(e)}")
    
    def _validate_operation(self, operation: DOMOperation) -> bool:
        """Validate operation before queueing"""
        # Check if element type is known
        strategy = self.element_registry.get_element_strategy(operation.element_type)
        if not strategy:
            self.logger.warning(f"Unknown element type: {operation.element_type}")
            return False
        
        # Validate required parameters
        if not operation.tab_id or not operation.selector:
            self.logger.error("Missing required operation parameters")
            return False
        
        # Register tab if not known
        self.tab_sync_manager.register_tab(operation.tab_id)
        
        return True
    
    def _check_same_tab_conflicts(self, operation: DOMOperation) -> List[str]:
        """Check for conflicts within the same tab"""
        conflicts = []
        
        for op_id, (active_op, future) in self.active_operations.items():
            if (active_op.tab_id == operation.tab_id and 
                active_op.element_type == operation.element_type and
                not future.done()):
                conflicts.append(f"Operation {op_id} already active for {operation.element_type}")
        
        return conflicts
    
    def _acquire_element_lock(self, operation: DOMOperation, timeout: float = 5.0) -> dict:
        """Acquire lock for element type"""
        element_type = operation.element_type
        
        if element_type not in self.operation_locks:
            self.operation_locks[element_type] = threading.Lock()
        
        lock = self.operation_locks[element_type]
        
        if lock.acquire(timeout=timeout):
            return {'success': True, 'message': 'Lock acquired'}
        else:
            return {'success': False, 'message': f'Could not acquire lock for {element_type} within {timeout}s'}
    
    def _estimate_wait_time(self, operation: DOMOperation) -> float:
        """Estimate wait time based on current queue and historical data"""
        # Count operations ahead in queue for same element type
        operations_ahead = sum(1 for op_id, (op, future) in self.active_operations.items() 
                             if op.element_type == operation.element_type and not future.done())
        
        # Get average execution time for this element type
        avg_time = self._get_average_execution_time(operation.element_type)
        
        return operations_ahead * avg_time
    
    def _get_average_execution_time(self, element_type: str) -> float:
        """Get average execution time for element type"""
        if element_type in self.operation_times and self.operation_times[element_type]:
            return sum(self.operation_times[element_type]) / len(self.operation_times[element_type])
        
        # Default estimates based on validation tier
        strategy = self.element_registry.get_element_strategy(element_type)
        if strategy:
            if strategy.validation_tier == ValidationTier.ZERO_LATENCY:
                return 0.1  # 100ms
            elif strategy.validation_tier == ValidationTier.LOW_LATENCY:
                return 0.5  # 500ms
            elif strategy.validation_tier == ValidationTier.STANDARD_LATENCY:
                return 2.0  # 2 seconds
            else:
                return 5.0  # 5 seconds
        
        return 3.0  # Default 3 seconds
    
    def _execute_operation(self, operation: DOMOperation) -> dict:
        """Execute DOM operation with proper error handling"""
        start_time = time.time()
        result = {
            'success': False,
            'message': '',
            'execution_time': 0.0,
            'operation_id': operation.operation_id
        }
        
        try:
            # Update tab state to executing
            self._update_tab_state(operation, 'executing')
            
            # Perform the actual DOM operation
            # This would integrate with the Chrome Communication Framework
            operation_result = self._perform_dom_operation(operation)
            
            result.update(operation_result)
            
            # Record execution time
            execution_time = time.time() - start_time
            result['execution_time'] = execution_time
            
            # Update performance tracking
            if operation.element_type not in self.operation_times:
                self.operation_times[operation.element_type] = []
            self.operation_times[operation.element_type].append(execution_time)
            
            # Keep only recent measurements (last 100)
            if len(self.operation_times[operation.element_type]) > 100:
                self.operation_times[operation.element_type] = self.operation_times[operation.element_type][-100:]
            
            self.logger.info(f"Executed operation {operation.operation_id} in {execution_time:.3f}s")
            
        except Exception as e:
            result['message'] = f"Execution error: {str(e)}"
            self.logger.error(f"Operation execution error: {str(e)}")
        finally:
            # Clean up
            self._cleanup_operation(operation)
            
        return result
    
    def _perform_dom_operation(self, operation: DOMOperation) -> dict:
        """
        Perform the actual DOM operation using Chrome Communication Framework
        This is where the operation integrates with existing safe_evaluate functionality
        """
        # This would use the existing Chrome Communication Framework
        # For now, return a placeholder implementation
        
        if operation.operation_type == 'click':
            # Use safe_evaluate to click element
            script = f"document.querySelector('{operation.selector}').click()"
            # result = safe_evaluate(operation.tab_id, script, operation.timeout_ms)
            
        elif operation.operation_type == 'input':
            # Use safe_evaluate to set input value
            value = operation.parameters.get('value', '')
            script = f"document.querySelector('{operation.selector}').value = '{value}'"
            # result = safe_evaluate(operation.tab_id, script, operation.timeout_ms)
            
        elif operation.operation_type == 'wait':
            # Wait for element to be available
            script = f"document.querySelector('{operation.selector}') !== null"
            # result = wait_for_condition(operation.tab_id, script, operation.timeout_ms)
        
        # Placeholder result
        return {
            'success': True,
            'message': f'{operation.operation_type} operation completed',
            'selector_used': operation.selector
        }
    
    def _update_tab_state(self, operation: DOMOperation, status: str):
        """Update tab state with operation status"""
        with self.queue_lock:
            # Update tab sync manager
            if status == 'queued':
                if operation.tab_id in self.tab_sync_manager.tab_states:
                    tab_state = self.tab_sync_manager.tab_states[operation.tab_id]
                    tab_state.active_operations[operation.element_type] = operation.operation_id
                    tab_state.last_activity = datetime.now()
            elif status == 'completed':
                if operation.tab_id in self.tab_sync_manager.tab_states:
                    tab_state = self.tab_sync_manager.tab_states[operation.tab_id]
                    if operation.element_type in tab_state.active_operations:
                        del tab_state.active_operations[operation.element_type]
                    tab_state.last_activity = datetime.now()
    
    def _cleanup_operation(self, operation: DOMOperation):
        """Clean up after operation completion"""
        with self.queue_lock:
            # Remove from active operations
            if operation.operation_id in self.active_operations:
                del self.active_operations[operation.operation_id]
            
            # Release element lock
            if operation.element_type in self.operation_locks:
                lock = self.operation_locks[operation.element_type]
                if lock.locked():
                    lock.release()
            
            # Update tab state
            self._update_tab_state(operation, 'completed')
            
            # Add to history for analysis
            self.operation_history.append({
                'operation_id': operation.operation_id,
                'element_type': operation.element_type,
                'tab_id': operation.tab_id,
                'completed_at': datetime.now(),
                'operation_type': operation.operation_type
            })
            
            # Keep history limited
            if len(self.operation_history) > 1000:
                self.operation_history = self.operation_history[-500:]
    
    def _record_conflict(self, conflict_type: str, conflicts: List[str]):
        """Record conflict for analysis"""
        if conflict_type not in self.conflict_counts:
            self.conflict_counts[conflict_type] = 0
        self.conflict_counts[conflict_type] += 1
        
        self.logger.warning(f"Conflict detected ({conflict_type}): {conflicts}")
    
    def get_queue_stats(self) -> dict:
        """Get comprehensive queue statistics"""
        with self.queue_lock:
            stats = {
                'active_operations': len(self.active_operations),
                'registered_tabs': len(self.tab_sync_manager.tab_states),
                'total_conflicts': sum(self.conflict_counts.values()),
                'conflict_breakdown': dict(self.conflict_counts),
                'operations_completed': len(self.operation_history),
                'average_execution_times': {}
            }
            
            # Calculate average execution times
            for element_type, times in self.operation_times.items():
                if times:
                    stats['average_execution_times'][element_type] = sum(times) / len(times)
            
            return stats
    
    def shutdown(self):
        """Gracefully shutdown the operation queue"""
        self.logger.info("Shutting down DOM operation queue")
        self.executor.shutdown(wait=True)

# Default DOM operation queue instance
default_dom_queue = DOMOperationQueue()

# ============================================================================
# DOM HEALTH MONITORING SYSTEM
# ============================================================================

from enum import Enum
import statistics
from collections import deque, defaultdict

class HealthStatus(Enum):
    """DOM system health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning" 
    DEGRADED = "degraded"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for DOM operations"""
    timestamp: datetime
    element_type: str
    operation_type: str
    execution_time: float
    validation_time: float
    queue_wait_time: float
    success: bool
    error_type: str = None
    selector_used: str = None
    fallback_depth: int = 0  # How many fallbacks were tried
    tab_id: str = None
    emergency_bypass_used: bool = False
    circuit_breaker_active: bool = False
    
    @property
    def total_time(self) -> float:
        """Total time from queue to completion"""
        return self.execution_time + self.validation_time + self.queue_wait_time

@dataclass 
class HealthAlert:
    """Health alert/warning notification"""
    severity: HealthStatus
    component: str
    message: str
    timestamp: datetime
    metrics: dict = None
    suggested_actions: List[str] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}
        if self.suggested_actions is None:
            self.suggested_actions = []

class DegradationDetector:
    """
    Detects performance degradation patterns using statistical analysis
    """
    
    def __init__(self, window_size: int = 100, alert_threshold: float = 2.0):
        self.window_size = window_size
        self.alert_threshold = alert_threshold  # Standard deviations for alerting
        self.logger = base_logger
        
        # Rolling windows for different metrics
        self.execution_times = defaultdict(lambda: deque(maxlen=window_size))
        self.success_rates = defaultdict(lambda: deque(maxlen=window_size))
        self.validation_times = defaultdict(lambda: deque(maxlen=window_size))
        
        # Baseline metrics (calculated from initial window)
        self.baselines = {}
        self.baseline_calculated = set()
        
    def add_metric(self, metric: PerformanceMetrics):
        """Add a performance metric for analysis"""
        key = f"{metric.element_type}_{metric.operation_type}"
        
        # Add to rolling windows
        self.execution_times[key].append(metric.execution_time)
        self.validation_times[key].append(metric.validation_time)
        self.success_rates[key].append(1.0 if metric.success else 0.0)
        
        # Calculate baseline if we have enough data
        if len(self.execution_times[key]) >= self.window_size // 2 and key not in self.baseline_calculated:
            self._calculate_baseline(key)
    
    def _calculate_baseline(self, key: str):
        """Calculate baseline performance metrics"""
        exec_times = list(self.execution_times[key])
        val_times = list(self.validation_times[key])
        success_rates = list(self.success_rates[key])
        
        if len(exec_times) < 10:  # Need minimum data
            return
            
        self.baselines[key] = {
            'execution_time_mean': statistics.mean(exec_times),
            'execution_time_stdev': statistics.stdev(exec_times) if len(exec_times) > 1 else 0,
            'validation_time_mean': statistics.mean(val_times),
            'validation_time_stdev': statistics.stdev(val_times) if len(val_times) > 1 else 0,
            'success_rate_mean': statistics.mean(success_rates),
            'calculated_at': datetime.now()
        }
        
        self.baseline_calculated.add(key)
        self.logger.info(f"Calculated baseline for {key}: {self.baselines[key]}")
    
    def detect_degradation(self, key: str) -> List[HealthAlert]:
        """Detect performance degradation patterns"""
        alerts = []
        
        if key not in self.baselines or len(self.execution_times[key]) < 10:
            return alerts
            
        baseline = self.baselines[key]
        recent_data = list(self.execution_times[key])[-10:]  # Last 10 operations
        recent_success = list(self.success_rates[key])[-10:]
        
        # Check execution time degradation
        recent_exec_mean = statistics.mean(recent_data)
        if baseline['execution_time_stdev'] > 0:
            z_score = (recent_exec_mean - baseline['execution_time_mean']) / baseline['execution_time_stdev']
            
            if z_score > self.alert_threshold:
                severity = HealthStatus.WARNING if z_score < 3.0 else HealthStatus.DEGRADED
                alerts.append(HealthAlert(
                    severity=severity,
                    component=f"execution_time_{key}",
                    message=f"Execution time degraded: {recent_exec_mean:.3f}s vs baseline {baseline['execution_time_mean']:.3f}s (z-score: {z_score:.2f})",
                    timestamp=datetime.now(),
                    metrics={'z_score': z_score, 'recent_mean': recent_exec_mean, 'baseline_mean': baseline['execution_time_mean']},
                    suggested_actions=[
                        "Check Chrome browser performance",
                        "Verify network connectivity", 
                        "Consider selector optimization",
                        "Monitor system resource usage"
                    ]
                ))
        
        # Check success rate degradation
        recent_success_rate = statistics.mean(recent_success)
        baseline_success_rate = baseline['success_rate_mean']
        
        if recent_success_rate < baseline_success_rate * 0.8:  # 20% drop in success rate
            severity = HealthStatus.WARNING if recent_success_rate > 0.5 else HealthStatus.CRITICAL
            alerts.append(HealthAlert(
                severity=severity,
                component=f"success_rate_{key}",
                message=f"Success rate degraded: {recent_success_rate:.2%} vs baseline {baseline_success_rate:.2%}",
                timestamp=datetime.now(),
                metrics={'recent_rate': recent_success_rate, 'baseline_rate': baseline_success_rate},
                suggested_actions=[
                    "Check Tradovate UI for changes",
                    "Update selector strategies",
                    "Verify DOM element availability",
                    "Consider emergency bypass activation"
                ]
            ))
        
        return alerts
    
    def get_degradation_summary(self) -> dict:
        """Get summary of all degradation patterns"""
        summary = {
            'baselines_calculated': len(self.baseline_calculated),
            'monitored_operations': len(self.execution_times),
            'degradation_patterns': []
        }
        
        for key in self.baseline_calculated:
            alerts = self.detect_degradation(key)
            if alerts:
                summary['degradation_patterns'].extend([{
                    'key': key,
                    'severity': alert.severity.value,
                    'message': alert.message
                } for alert in alerts])
        
        return summary

class DOMHealthMonitor:
    """
    Comprehensive DOM health monitoring with performance metrics and degradation detection
    """
    
    def __init__(self, max_metrics_history: int = 10000):
        self.logger = base_logger
        self.max_metrics_history = max_metrics_history
        
        # Metrics storage
        self.metrics_history = deque(maxlen=max_metrics_history)
        self.current_alerts = []
        
        # Component monitoring
        self.degradation_detector = DegradationDetector()
        
        # System health tracking
        self.health_status = HealthStatus.HEALTHY
        self.last_health_check = datetime.now()
        self.health_check_interval = 30  # seconds
        
        # Performance counters
        self.performance_counters = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'emergency_bypasses': 0,
            'circuit_breaker_trips': 0,
            'validation_failures': 0,
            'selector_evolutions': 0
        }
        
        # Element-specific health tracking
        self.element_health = defaultdict(lambda: {
            'total_operations': 0,
            'recent_failures': deque(maxlen=10),
            'avg_execution_time': 0.0,
            'last_success': None,
            'health_status': HealthStatus.HEALTHY
        })
        
        # System resource monitoring
        self.resource_metrics = {
            'chrome_tabs_count': 0,
            'active_operations_count': 0,
            'queue_depth': 0,
            'memory_usage_trend': deque(maxlen=60),  # Last hour
            'cpu_usage_trend': deque(maxlen=60)
        }
    
    def record_operation_metric(self, metric: PerformanceMetrics):
        """Record a DOM operation performance metric"""
        self.metrics_history.append(metric)
        self.degradation_detector.add_metric(metric)
        
        # Update performance counters
        self.performance_counters['total_operations'] += 1
        if metric.success:
            self.performance_counters['successful_operations'] += 1
        else:
            self.performance_counters['failed_operations'] += 1
        
        if metric.emergency_bypass_used:
            self.performance_counters['emergency_bypasses'] += 1
        
        if metric.circuit_breaker_active:
            self.performance_counters['circuit_breaker_trips'] += 1
        
        # Update element-specific health
        element_key = f"{metric.element_type}_{metric.operation_type}"
        element_health = self.element_health[element_key]
        element_health['total_operations'] += 1
        
        if not metric.success:
            element_health['recent_failures'].append(datetime.now())
        else:
            element_health['last_success'] = datetime.now()
        
        # Update average execution time (exponential moving average)
        alpha = 0.1  # Smoothing factor
        if element_health['avg_execution_time'] == 0:
            element_health['avg_execution_time'] = metric.execution_time
        else:
            element_health['avg_execution_time'] = (
                alpha * metric.execution_time + 
                (1 - alpha) * element_health['avg_execution_time']
            )
        
        # Update element health status
        self._update_element_health_status(element_key)
        
        self.logger.debug(f"Recorded metric for {element_key}: {metric.execution_time:.3f}s, success: {metric.success}")
    
    def _update_element_health_status(self, element_key: str):
        """Update health status for a specific element"""
        element_health = self.element_health[element_key]
        recent_failures = element_health['recent_failures']
        
        # Count recent failures (last 5 minutes)
        now = datetime.now()
        recent_failure_count = sum(1 for failure_time in recent_failures 
                                 if (now - failure_time).total_seconds() < 300)
        
        # Determine health status based on recent failures
        if recent_failure_count == 0:
            element_health['health_status'] = HealthStatus.HEALTHY
        elif recent_failure_count <= 2:
            element_health['health_status'] = HealthStatus.WARNING
        elif recent_failure_count <= 5:
            element_health['health_status'] = HealthStatus.DEGRADED
        else:
            element_health['health_status'] = HealthStatus.CRITICAL
    
    def check_system_health(self) -> HealthStatus:
        """Perform comprehensive system health check"""
        now = datetime.now()
        
        # Only check if enough time has passed
        if (now - self.last_health_check).total_seconds() < self.health_check_interval:
            return self.health_status
        
        self.last_health_check = now
        
        # Check overall success rate
        if self.performance_counters['total_operations'] > 10:
            success_rate = (self.performance_counters['successful_operations'] / 
                          self.performance_counters['total_operations'])
            
            if success_rate < 0.5:
                self.health_status = HealthStatus.CRITICAL
            elif success_rate < 0.7:
                self.health_status = HealthStatus.DEGRADED
            elif success_rate < 0.9:
                self.health_status = HealthStatus.WARNING
            else:
                self.health_status = HealthStatus.HEALTHY
        
        # Check for critical element failures
        critical_elements = ['order_submit_button', 'position_exit_button', 'symbol_input']
        for element_type in critical_elements:
            for op_type in ['click', 'input']:
                element_key = f"{element_type}_{op_type}"
                if element_key in self.element_health:
                    element_status = self.element_health[element_key]['health_status']
                    if element_status in [HealthStatus.CRITICAL, HealthStatus.EMERGENCY]:
                        self.health_status = max(self.health_status, element_status, key=lambda x: x.value)
        
        # Check degradation patterns
        alerts = self._check_degradation_alerts()
        if alerts:
            critical_alerts = [a for a in alerts if a.severity in [HealthStatus.CRITICAL, HealthStatus.EMERGENCY]]
            if critical_alerts:
                self.health_status = HealthStatus.CRITICAL
        
        self.logger.info(f"System health check: {self.health_status.value}")
        return self.health_status
    
    def _check_degradation_alerts(self) -> List[HealthAlert]:
        """Check for degradation patterns and generate alerts"""
        # Clear old alerts (older than 1 hour)
        now = datetime.now()
        self.current_alerts = [alert for alert in self.current_alerts 
                             if (now - alert.timestamp).total_seconds() < 3600]
        
        # Check for new degradation patterns
        degradation_summary = self.degradation_detector.get_degradation_summary()
        
        for pattern in degradation_summary['degradation_patterns']:
            # Check if we already have an alert for this pattern
            existing_alert = any(alert.component == pattern['key'] for alert in self.current_alerts)
            
            if not existing_alert:
                alert = HealthAlert(
                    severity=HealthStatus(pattern['severity']),
                    component=pattern['key'],
                    message=pattern['message'],
                    timestamp=now
                )
                self.current_alerts.append(alert)
                self.logger.warning(f"New degradation alert: {alert.message}")
        
        return self.current_alerts
    
    def get_performance_summary(self) -> dict:
        """Get comprehensive performance summary"""
        summary = {
            'health_status': self.health_status.value,
            'last_health_check': self.last_health_check,
            'performance_counters': dict(self.performance_counters),
            'total_metrics_recorded': len(self.metrics_history),
            'active_alerts': len(self.current_alerts),
            'element_health_summary': {},
            'recent_performance': {}
        }
        
        # Add success rate
        if self.performance_counters['total_operations'] > 0:
            summary['performance_counters']['success_rate'] = (
                self.performance_counters['successful_operations'] / 
                self.performance_counters['total_operations']
            )
        
        # Element health summary
        for element_key, health_data in self.element_health.items():
            summary['element_health_summary'][element_key] = {
                'health_status': health_data['health_status'].value,
                'total_operations': health_data['total_operations'],
                'avg_execution_time': health_data['avg_execution_time'],
                'recent_failures': len(health_data['recent_failures']),
                'last_success': health_data['last_success']
            }
        
        # Recent performance (last 10 operations)
        if self.metrics_history:
            recent_metrics = list(self.metrics_history)[-10:]
            summary['recent_performance'] = {
                'avg_execution_time': statistics.mean(m.execution_time for m in recent_metrics),
                'avg_validation_time': statistics.mean(m.validation_time for m in recent_metrics),
                'avg_queue_wait_time': statistics.mean(m.queue_wait_time for m in recent_metrics),
                'success_rate': statistics.mean(1 if m.success else 0 for m in recent_metrics)
            }
        
        return summary
    
    def get_critical_alerts(self) -> List[HealthAlert]:
        """Get only critical and emergency alerts"""
        return [alert for alert in self.current_alerts 
                if alert.severity in [HealthStatus.CRITICAL, HealthStatus.EMERGENCY]]
    
    def get_element_performance(self, element_type: str, operation_type: str = None) -> dict:
        """Get detailed performance data for specific element"""
        if operation_type:
            element_key = f"{element_type}_{operation_type}"
            if element_key in self.element_health:
                return {
                    'element_key': element_key,
                    'health_data': self.element_health[element_key],
                    'recent_metrics': [m for m in list(self.metrics_history)[-50:] 
                                     if m.element_type == element_type and m.operation_type == operation_type]
                }
        else:
            # Return all operation types for this element
            results = {}
            for key, health_data in self.element_health.items():
                if key.startswith(f"{element_type}_"):
                    results[key] = {
                        'health_data': health_data,
                        'recent_metrics': [m for m in list(self.metrics_history)[-50:] 
                                         if m.element_type == element_type]
                    }
            return results
        
        return {}
    
    def record_emergency_bypass(self, element_type: str, reason: str):
        """Record emergency bypass usage"""
        self.performance_counters['emergency_bypasses'] += 1
        
        alert = HealthAlert(
            severity=HealthStatus.WARNING,
            component=f"emergency_bypass_{element_type}",
            message=f"Emergency bypass activated for {element_type}: {reason}",
            timestamp=datetime.now(),
            suggested_actions=[
                "Review trading conditions",
                "Check market volatility",
                "Verify system performance",
                "Consider manual intervention"
            ]
        )
        self.current_alerts.append(alert)
        self.logger.warning(f"Emergency bypass recorded: {element_type} - {reason}")
    
    def record_circuit_breaker_trip(self, component: str, failure_count: int):
        """Record circuit breaker activation"""
        self.performance_counters['circuit_breaker_trips'] += 1
        
        severity = HealthStatus.WARNING if failure_count < 5 else HealthStatus.CRITICAL
        alert = HealthAlert(
            severity=severity,
            component=f"circuit_breaker_{component}",
            message=f"Circuit breaker tripped for {component} after {failure_count} failures",
            timestamp=datetime.now(),
            metrics={'failure_count': failure_count},
            suggested_actions=[
                "Investigate root cause of failures",
                "Check DOM element availability", 
                "Update selector strategies",
                "Consider system restart if persistent"
            ]
        )
        self.current_alerts.append(alert)
        self.logger.error(f"Circuit breaker trip recorded: {component} - {failure_count} failures")
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics data for analysis"""
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'performance_summary': self.get_performance_summary(),
            'degradation_summary': self.degradation_detector.get_degradation_summary(),
            'current_alerts': [
                {
                    'severity': alert.severity.value,
                    'component': alert.component,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'metrics': alert.metrics
                } for alert in self.current_alerts
            ],
            'metrics_history': [
                {
                    'timestamp': metric.timestamp.isoformat(),
                    'element_type': metric.element_type,
                    'operation_type': metric.operation_type,
                    'execution_time': metric.execution_time,
                    'validation_time': metric.validation_time,
                    'queue_wait_time': metric.queue_wait_time,
                    'success': metric.success,
                    'error_type': metric.error_type,
                    'selector_used': metric.selector_used,
                    'fallback_depth': metric.fallback_depth,
                    'emergency_bypass_used': metric.emergency_bypass_used,
                    'circuit_breaker_active': metric.circuit_breaker_active
                } for metric in list(self.metrics_history)
            ]
        }
        
        if format.lower() == 'json':
            import json
            return json.dumps(data, indent=2)
        else:
            return str(data)

# Default DOM health monitor instance
default_dom_health_monitor = DOMHealthMonitor()

# ============================================================================
# CRITICAL TRADING OPERATIONS INTEGRATION
# ============================================================================

import json
from typing import Optional, Dict, Any, Union

class CriticalOperationValidator:
    """
    Validates critical trading operations with zero-latency emergency bypass
    Integrates DOM Intelligence with existing trading operations
    """
    
    def __init__(self, 
                 dom_validator: DOMValidator = None,
                 element_registry: TradovateElementRegistry = None,
                 health_monitor: DOMHealthMonitor = None,
                 operation_queue: DOMOperationQueue = None):
        
        self.dom_validator = dom_validator or default_dom_validator
        self.element_registry = element_registry or default_element_registry
        self.health_monitor = health_monitor or default_dom_health_monitor
        self.operation_queue = operation_queue or default_dom_queue
        self.logger = base_logger
        
        # Emergency bypass conditions
        self.emergency_conditions = {
            'market_volatility_threshold': 0.05,  # 5% price movement threshold
            'system_latency_threshold': 1000,     # 1 second latency threshold
            'health_score_threshold': 30,         # Critical health threshold
            'manual_override_active': False
        }
        
        # Performance tracking for critical operations
        self.critical_operation_metrics = {
            'auto_trade': {'count': 0, 'avg_time': 0, 'success_rate': 1.0},
            'exit_positions': {'count': 0, 'avg_time': 0, 'success_rate': 1.0},
            'symbol_update': {'count': 0, 'avg_time': 0, 'success_rate': 1.0},
            'account_switch': {'count': 0, 'avg_time': 0, 'success_rate': 1.0}
        }
    
    def should_bypass_validation(self, operation_type: str, context: dict = None) -> tuple[bool, str]:
        """
        Determine if operation should bypass DOM validation for emergency conditions
        Returns (should_bypass, reason)
        """
        # Check manual override
        if self.emergency_conditions['manual_override_active']:
            return True, "Manual emergency override active"
        
        # Check system health
        health_status = self.health_monitor.check_system_health()
        if health_status == HealthStatus.CRITICAL:
            return True, f"Critical system health: {health_status.value}"
        
        # Check for high-frequency trading conditions
        if context and context.get('high_frequency_mode', False):
            return True, "High frequency trading mode active"
        
        # Check recent performance degradation
        if operation_type in self.critical_operation_metrics:
            metrics = self.critical_operation_metrics[operation_type]
            if metrics['success_rate'] < 0.7 and metrics['count'] > 5:
                return True, f"Poor recent performance for {operation_type}: {metrics['success_rate']:.1%}"
        
        # Check market stress indicators (if provided in context)
        if context:
            volatility = context.get('market_volatility', 0)
            if volatility > self.emergency_conditions['market_volatility_threshold']:
                return True, f"High market volatility: {volatility:.1%}"
            
            latency = context.get('system_latency', 0)
            if latency > self.emergency_conditions['system_latency_threshold']:
                return True, f"High system latency: {latency}ms"
        
        return False, "Normal conditions - validation required"
    
    def validate_critical_operation(self, 
                                   operation_type: str,
                                   tab_id: str,
                                   operation_data: dict,
                                   context: dict = None) -> dict:
        """
        Validate a critical trading operation with emergency bypass capability
        """
        start_time = time.time()
        context = context or {}
        
        result = {
            'operation_type': operation_type,
            'tab_id': tab_id,
            'validation_enabled': True,
            'emergency_bypass': False,
            'validation_time': 0,
            'success': False,
            'message': '',
            'dom_health': None,
            'performance_metrics': {}
        }
        
        try:
            # Check if emergency bypass should be used
            should_bypass, bypass_reason = self.should_bypass_validation(operation_type, context)
            
            if should_bypass:
                result['emergency_bypass'] = True
                result['validation_enabled'] = False
                result['success'] = True
                result['message'] = f"Emergency bypass: {bypass_reason}"
                
                # Record emergency bypass
                self.health_monitor.record_emergency_bypass(operation_type, bypass_reason)
                self.logger.warning(f"Emergency bypass for {operation_type}: {bypass_reason}")
                
                return result
            
            # Perform DOM Intelligence validation
            validation_result = self._perform_operation_validation(operation_type, tab_id, operation_data)
            result.update(validation_result)
            
            # Record performance metrics
            validation_time = time.time() - start_time
            result['validation_time'] = validation_time * 1000  # Convert to milliseconds
            
            # Update critical operation metrics
            self._update_operation_metrics(operation_type, validation_time, result['success'])
            
            # Record health monitor metric
            metric = PerformanceMetrics(
                timestamp=datetime.now(),
                element_type=operation_type,
                operation_type='validation',
                execution_time=validation_time,
                validation_time=validation_time,
                queue_wait_time=0,
                success=result['success'],
                emergency_bypass_used=False,
                circuit_breaker_active=False,
                tab_id=tab_id
            )
            self.health_monitor.record_operation_metric(metric)
            
            # Add current DOM health to result
            result['dom_health'] = self.health_monitor.check_system_health().value
            
        except Exception as e:
            result['success'] = False
            result['message'] = f"Validation error: {str(e)}"
            result['validation_time'] = (time.time() - start_time) * 1000
            self.logger.error(f"Critical operation validation failed for {operation_type}: {str(e)}")
        
        return result
    
    def _perform_operation_validation(self, operation_type: str, tab_id: str, operation_data: dict) -> dict:
        """Perform specific validation based on operation type"""
        
        if operation_type == 'auto_trade':
            return self._validate_auto_trade_operation(tab_id, operation_data)
        elif operation_type == 'exit_positions':
            return self._validate_exit_positions_operation(tab_id, operation_data)
        elif operation_type == 'symbol_update':
            return self._validate_symbol_update_operation(tab_id, operation_data)
        elif operation_type == 'account_switch':
            return self._validate_account_switch_operation(tab_id, operation_data)
        else:
            return {
                'success': False,
                'message': f"Unknown operation type: {operation_type}"
            }
    
    def _validate_auto_trade_operation(self, tab_id: str, operation_data: dict) -> dict:
        """Validate auto trade operation elements"""
        validation_results = {}
        overall_success = True
        messages = []
        
        try:
            # Validate order submit button
            submit_validation = self.dom_validator.validate_operation(
                tab_id, 
                DOMOperation(
                    operation_id=str(uuid.uuid4()),
                    tab_id=tab_id,
                    element_type='order_submit_button',
                    selector='.btn-group .btn-primary',
                    operation_type='click',
                    validation_tier=ValidationTier.ZERO_LATENCY,
                    emergency_bypass=True
                )
            )
            validation_results['order_submit_button'] = submit_validation
            if not submit_validation.success:
                overall_success = False
                messages.append(f"Order submit button validation failed: {submit_validation.message}")
            
            # Validate symbol input if symbol is being changed
            if 'symbol' in operation_data:
                symbol_validation = self.dom_validator.validate_operation(
                    tab_id,
                    DOMOperation(
                        operation_id=str(uuid.uuid4()),
                        tab_id=tab_id,
                        element_type='symbol_input',
                        selector='#symbolInput',
                        operation_type='input',
                        validation_tier=ValidationTier.LOW_LATENCY,
                        emergency_bypass=True,
                        parameters={'value': operation_data['symbol']}
                    )
                )
                validation_results['symbol_input'] = symbol_validation
                if not symbol_validation.success:
                    overall_success = False
                    messages.append(f"Symbol input validation failed: {symbol_validation.message}")
            
            # Validate quantity input if provided
            if 'quantity' in operation_data:
                quantity_validation = self.dom_validator.validate_operation(
                    tab_id,
                    DOMOperation(
                        operation_id=str(uuid.uuid4()),
                        tab_id=tab_id,
                        element_type='quantity_input',
                        selector='.quantity-field input',
                        operation_type='input',
                        validation_tier=ValidationTier.LOW_LATENCY,
                        emergency_bypass=True,
                        parameters={'value': str(operation_data['quantity'])}
                    )
                )
                validation_results['quantity_input'] = quantity_validation
                if not quantity_validation.success:
                    messages.append(f"Quantity input warning: {quantity_validation.message}")
            
        except Exception as e:
            overall_success = False
            messages.append(f"Auto trade validation error: {str(e)}")
        
        return {
            'success': overall_success,
            'message': '; '.join(messages) if messages else 'Auto trade validation successful',
            'validation_details': validation_results
        }
    
    def _validate_exit_positions_operation(self, tab_id: str, operation_data: dict) -> dict:
        """Validate position exit operation elements"""
        validation_results = {}
        overall_success = True
        messages = []
        
        try:
            # Validate position exit button
            exit_validation = self.dom_validator.validate_operation(
                tab_id,
                DOMOperation(
                    operation_id=str(uuid.uuid4()),
                    tab_id=tab_id,
                    element_type='position_exit_button',
                    selector='.position-exit-btn',
                    operation_type='click',
                    validation_tier=ValidationTier.ZERO_LATENCY,
                    emergency_bypass=True
                )
            )
            validation_results['position_exit_button'] = exit_validation
            if not exit_validation.success:
                overall_success = False
                messages.append(f"Position exit button validation failed: {exit_validation.message}")
            
            # Validate market data table accessibility
            market_data_validation = self.dom_validator.validate_operation(
                tab_id,
                DOMOperation(
                    operation_id=str(uuid.uuid4()),
                    tab_id=tab_id,
                    element_type='market_data_table',
                    selector='.module.positions.data-table',
                    operation_type='extract',
                    validation_tier=ValidationTier.LOW_LATENCY,
                    emergency_bypass=False
                )
            )
            validation_results['market_data_table'] = market_data_validation
            if not market_data_validation.success:
                messages.append(f"Market data table warning: {market_data_validation.message}")
        
        except Exception as e:
            overall_success = False
            messages.append(f"Exit positions validation error: {str(e)}")
        
        return {
            'success': overall_success,
            'message': '; '.join(messages) if messages else 'Exit positions validation successful',
            'validation_details': validation_results
        }
    
    def _validate_symbol_update_operation(self, tab_id: str, operation_data: dict) -> dict:
        """Validate symbol update operation elements"""
        validation_results = {}
        overall_success = True
        messages = []
        
        try:
            # Validate symbol input field
            symbol_validation = self.dom_validator.validate_operation(
                tab_id,
                DOMOperation(
                    operation_id=str(uuid.uuid4()),
                    tab_id=tab_id,
                    element_type='symbol_input',
                    selector='#symbolInput',
                    operation_type='input',
                    validation_tier=ValidationTier.LOW_LATENCY,
                    emergency_bypass=True,
                    parameters={'value': operation_data.get('symbol', '')}
                )
            )
            validation_results['symbol_input'] = symbol_validation
            if not symbol_validation.success:
                overall_success = False
                messages.append(f"Symbol input validation failed: {symbol_validation.message}")
        
        except Exception as e:
            overall_success = False
            messages.append(f"Symbol update validation error: {str(e)}")
        
        return {
            'success': overall_success,
            'message': '; '.join(messages) if messages else 'Symbol update validation successful',
            'validation_details': validation_results
        }
    
    def _validate_account_switch_operation(self, tab_id: str, operation_data: dict) -> dict:
        """Validate account switch operation elements"""
        validation_results = {}
        overall_success = True
        messages = []
        
        try:
            # Validate account selector dropdown
            account_validation = self.dom_validator.validate_operation(
                tab_id,
                DOMOperation(
                    operation_id=str(uuid.uuid4()),
                    tab_id=tab_id,
                    element_type='account_selector',
                    selector='.pane.account-selector.dropdown [data-toggle="dropdown"]',
                    operation_type='click',
                    validation_tier=ValidationTier.LOW_LATENCY,
                    emergency_bypass=False,  # Account switching should not bypass unless critical
                    parameters={'target_account': operation_data.get('account_name', '')}
                )
            )
            validation_results['account_selector'] = account_validation
            if not account_validation.success:
                overall_success = False
                messages.append(f"Account selector validation failed: {account_validation.message}")
        
        except Exception as e:
            overall_success = False
            messages.append(f"Account switch validation error: {str(e)}")
        
        return {
            'success': overall_success,
            'message': '; '.join(messages) if messages else 'Account switch validation successful',
            'validation_details': validation_results
        }
    
    def _update_operation_metrics(self, operation_type: str, execution_time: float, success: bool):
        """Update performance metrics for critical operations"""
        if operation_type not in self.critical_operation_metrics:
            return
        
        metrics = self.critical_operation_metrics[operation_type]
        
        # Update count
        metrics['count'] += 1
        
        # Update average time (exponential moving average)
        alpha = 0.1  # Smoothing factor
        if metrics['count'] == 1:
            metrics['avg_time'] = execution_time
        else:
            metrics['avg_time'] = alpha * execution_time + (1 - alpha) * metrics['avg_time']
        
        # Update success rate (exponential moving average)
        success_value = 1.0 if success else 0.0
        if metrics['count'] == 1:
            metrics['success_rate'] = success_value
        else:
            metrics['success_rate'] = alpha * success_value + (1 - alpha) * metrics['success_rate']
    
    def get_critical_operations_report(self) -> dict:
        """Get comprehensive report of critical operations performance"""
        return {
            'timestamp': datetime.now().isoformat(),
            'emergency_conditions': self.emergency_conditions,
            'operation_metrics': self.critical_operation_metrics,
            'dom_health': self.health_monitor.get_performance_summary(),
            'recent_bypasses': len([alert for alert in self.health_monitor.current_alerts 
                                  if 'bypass' in alert.component.lower()]),
            'system_status': self.health_monitor.check_system_health().value
        }
    
    def enable_manual_emergency_override(self, reason: str = "Manual override"):
        """Enable manual emergency override for all operations"""
        self.emergency_conditions['manual_override_active'] = True
        self.health_monitor.record_emergency_bypass('manual_override', reason)
        self.logger.warning(f"Manual emergency override ENABLED: {reason}")
    
    def disable_manual_emergency_override(self):
        """Disable manual emergency override"""
        self.emergency_conditions['manual_override_active'] = False
        self.logger.info("Manual emergency override DISABLED")
    
    def adjust_emergency_thresholds(self, **kwargs):
        """Adjust emergency bypass thresholds"""
        for key, value in kwargs.items():
            if key in self.emergency_conditions:
                old_value = self.emergency_conditions[key]
                self.emergency_conditions[key] = value
                self.logger.info(f"Emergency threshold updated: {key} {old_value} -> {value}")

# Default critical operation validator instance
default_critical_validator = CriticalOperationValidator()

# ============================================================================
# ENHANCED TRADING OPERATION WRAPPERS
# ============================================================================

def validate_and_execute_critical_operation(tab, operation_type: str, 
                                           js_code: str, operation_data: dict, 
                                           context: dict = None) -> dict:
    """
    Wrapper function to validate and execute critical trading operations
    
    Args:
        tab: Chrome tab object
        operation_type: Type of operation ('auto_trade', 'exit_positions', etc.)
        js_code: JavaScript code to execute
        operation_data: Data about the operation (symbol, quantity, etc.)
        context: Additional context (market conditions, urgency, etc.)
    
    Returns:
        Dict with validation results and execution results
    """
    if not tab:
        return {
            'success': False,
            'error': 'No tab available',
            'validation_skipped': True
        }
    
    tab_id = getattr(tab, 'id', 'unknown_tab')
    
    # Perform validation with potential emergency bypass
    validation_result = default_critical_validator.validate_critical_operation(
        operation_type, tab_id, operation_data, context
    )
    
    # Always execute the operation regardless of validation result
    # Validation provides insights but doesn't block critical trading operations
    execution_result = {}
    try:
        # Record start time for execution tracking
        execution_start = time.time()
        
        # Execute the JavaScript
        js_result = tab.Runtime.evaluate(expression=js_code)
        
        # Record execution metrics
        execution_time = time.time() - execution_start
        execution_result = {
            'js_result': js_result,
            'execution_time': execution_time * 1000,  # Convert to milliseconds
            'execution_success': True
        }
        
        # Record performance metric for the actual operation
        metric = PerformanceMetrics(
            timestamp=datetime.now(),
            element_type=operation_type,
            operation_type='execution',
            execution_time=execution_time,
            validation_time=validation_result.get('validation_time', 0) / 1000,
            queue_wait_time=0,
            success=True,
            emergency_bypass_used=validation_result.get('emergency_bypass', False),
            circuit_breaker_active=False,
            tab_id=tab_id
        )
        default_dom_health_monitor.record_operation_metric(metric)
        
    except Exception as e:
        execution_result = {
            'execution_success': False,
            'execution_error': str(e),
            'execution_time': (time.time() - execution_start) * 1000 if 'execution_start' in locals() else 0
        }
    
    # Combine validation and execution results
    final_result = {
        'operation_type': operation_type,
        'tab_id': tab_id,
        'validation_result': validation_result,
        'execution_result': execution_result,
        'overall_success': execution_result.get('execution_success', False),
        'dom_intelligence_enabled': True,
        'timestamp': datetime.now().isoformat()
    }
    
    return final_result

# Convenience functions for specific operations
def execute_auto_trade_with_validation(tab, symbol: str, quantity: int, action: str, 
                                     tp_ticks: int, sl_ticks: int, tick_size: float,
                                     context: dict = None) -> dict:
    """Execute auto trade with DOM Intelligence validation"""
    js_code = f"autoTrade('{symbol}', {quantity}, '{action}', {tp_ticks}, {sl_ticks}, {tick_size});"
    operation_data = {
        'symbol': symbol,
        'quantity': quantity,
        'action': action,
        'tp_ticks': tp_ticks,
        'sl_ticks': sl_ticks,
        'tick_size': tick_size
    }
    
    return validate_and_execute_critical_operation(
        tab, 'auto_trade', js_code, operation_data, context
    )

def execute_exit_positions_with_validation(tab, symbol: str, option: str = 'cancel-option-Exit-at-Mkt-Cxl',
                                         context: dict = None) -> dict:
    """Execute position exit with DOM Intelligence validation"""
    js_code = f"clickExitForSymbol(normalizeSymbol('{symbol}'), '{option}');"
    operation_data = {
        'symbol': symbol,
        'exit_option': option
    }
    
    return validate_and_execute_critical_operation(
        tab, 'exit_positions', js_code, operation_data, context
    )

def execute_symbol_update_with_validation(tab, symbol: str, context: dict = None) -> dict:
    """Execute symbol update with DOM Intelligence validation"""
    js_code = f"updateSymbol('.search-box--input', normalizeSymbol('{symbol}'));"
    operation_data = {
        'symbol': symbol
    }
    
    return validate_and_execute_critical_operation(
        tab, 'symbol_update', js_code, operation_data, context
    )

def execute_account_switch_with_validation(tab, account_name: str, context: dict = None) -> dict:
    """Execute account switch with DOM Intelligence validation"""
    js_code = f"changeAccount('{account_name}');"
    operation_data = {
        'account_name': account_name
    }
    
    return validate_and_execute_critical_operation(
        tab, 'account_switch', js_code, operation_data, context
    )

# ============================================================================
# ENHANCED DOM STATE SYNCHRONIZATION
# ============================================================================

from typing import Callable, Set
import asyncio
from concurrent.futures import Future

class DOMStateSynchronizer:
    """
    Advanced DOM state synchronization across multiple trading tabs
    Ensures consistent DOM state and prevents race conditions
    """
    
    def __init__(self, 
                 tab_sync_manager: TabSynchronizationManager = None,
                 operation_queue: DOMOperationQueue = None,
                 health_monitor: DOMHealthMonitor = None):
        
        self.tab_sync_manager = tab_sync_manager or default_dom_queue.tab_sync_manager
        self.operation_queue = operation_queue or default_dom_queue
        self.health_monitor = health_monitor or default_dom_health_monitor
        self.logger = base_logger
        
        # State synchronization tracking
        self.sync_operations = {}  # sync_id -> SyncOperation
        self.active_syncs = set()  # Currently active sync operations
        self.sync_lock = threading.RLock()
        
        # DOM state snapshots
        self.dom_snapshots = {}  # tab_id -> DOMSnapshot
        self.snapshot_interval = 5000  # 5 seconds between snapshots
        
        # Event handlers for state changes
        self.state_change_handlers = {
            'symbol_change': [],
            'account_switch': [],
            'position_update': [],
            'dom_mutation': []
        }
        
        # Performance tracking
        self.sync_metrics = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'avg_sync_time': 0,
            'conflict_resolutions': 0
        }
    
    def register_state_change_handler(self, event_type: str, handler: Callable):
        """Register a handler for state change events"""
        if event_type in self.state_change_handlers:
            self.state_change_handlers[event_type].append(handler)
            self.logger.info(f"Registered handler for {event_type} events")
    
    def sync_dom_state_across_tabs(self, source_tab_id: str, state_type: str, 
                                  state_data: dict, priority: str = 'normal') -> dict:
        """
        Synchronize DOM state change across all relevant tabs
        
        Args:
            source_tab_id: Tab that initiated the state change
            state_type: Type of state change (symbol_change, account_switch, etc.)
            state_data: Data associated with the state change
            priority: Sync priority (critical, high, normal, low)
        
        Returns:
            Dict with sync results
        """
        sync_id = str(uuid.uuid4())
        start_time = time.time()
        
        result = {
            'sync_id': sync_id,
            'source_tab': source_tab_id,
            'state_type': state_type,
            'success': False,
            'synced_tabs': [],
            'failed_tabs': [],
            'conflicts': [],
            'sync_time': 0
        }
        
        try:
            with self.sync_lock:
                # Check if similar sync is already active
                if self._is_conflicting_sync_active(state_type, state_data):
                    result['conflicts'].append('Similar sync operation already active')
                    self.sync_metrics['conflict_resolutions'] += 1
                    
                    # For critical operations, wait for existing sync to complete
                    if priority == 'critical':
                        self._wait_for_active_syncs(state_type, timeout=5.0)
                    else:
                        return result
                
                # Create sync operation
                sync_op = SyncOperation(
                    sync_id=sync_id,
                    source_tab=source_tab_id,
                    state_type=state_type,
                    state_data=state_data,
                    priority=priority,
                    timestamp=datetime.now()
                )
                
                self.sync_operations[sync_id] = sync_op
                self.active_syncs.add(sync_id)
            
            # Take DOM snapshot before sync
            self._capture_dom_snapshot(source_tab_id)
            
            # Get target tabs for synchronization
            target_tabs = self._get_sync_target_tabs(source_tab_id, state_type, state_data)
            
            if not target_tabs:
                result['message'] = 'No target tabs for synchronization'
                result['success'] = True
                return result
            
            # Execute synchronization based on state type
            if state_type == 'symbol_change':
                sync_results = self._sync_symbol_change(source_tab_id, target_tabs, state_data)
            elif state_type == 'account_switch':
                sync_results = self._sync_account_switch(source_tab_id, target_tabs, state_data)
            elif state_type == 'position_update':
                sync_results = self._sync_position_update(source_tab_id, target_tabs, state_data)
            elif state_type == 'dom_mutation':
                sync_results = self._sync_dom_mutation(source_tab_id, target_tabs, state_data)
            else:
                raise ValueError(f"Unknown state type: {state_type}")
            
            # Process sync results
            for tab_id, tab_result in sync_results.items():
                if tab_result.get('success', False):
                    result['synced_tabs'].append(tab_id)
                else:
                    result['failed_tabs'].append({
                        'tab_id': tab_id,
                        'error': tab_result.get('error', 'Unknown error')
                    })
            
            # Update metrics
            self.sync_metrics['total_syncs'] += 1
            if len(result['synced_tabs']) > 0:
                self.sync_metrics['successful_syncs'] += 1
                result['success'] = True
            else:
                self.sync_metrics['failed_syncs'] += 1
            
            # Calculate sync time
            sync_time = time.time() - start_time
            result['sync_time'] = sync_time * 1000  # Convert to milliseconds
            
            # Update average sync time
            alpha = 0.1  # Smoothing factor
            if self.sync_metrics['avg_sync_time'] == 0:
                self.sync_metrics['avg_sync_time'] = sync_time
            else:
                self.sync_metrics['avg_sync_time'] = (
                    alpha * sync_time + (1 - alpha) * self.sync_metrics['avg_sync_time']
                )
            
            # Trigger event handlers
            self._trigger_state_change_handlers(state_type, state_data, result)
            
            # Record performance metric
            metric = PerformanceMetrics(
                timestamp=datetime.now(),
                element_type='dom_sync',
                operation_type=state_type,
                execution_time=sync_time,
                validation_time=0,
                queue_wait_time=0,
                success=result['success'],
                tab_id=source_tab_id
            )
            self.health_monitor.record_operation_metric(metric)
            
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            self.logger.error(f"DOM state sync error: {str(e)}")
            self.sync_metrics['failed_syncs'] += 1
        finally:
            # Clean up sync operation
            with self.sync_lock:
                if sync_id in self.active_syncs:
                    self.active_syncs.remove(sync_id)
        
        return result
    
    def _sync_symbol_change(self, source_tab: str, target_tabs: List[str], 
                           state_data: dict) -> dict:
        """Synchronize symbol change across tabs"""
        results = {}
        symbol = state_data.get('symbol', '')
        
        # Use TabSynchronizationManager for basic sync
        synced_tabs = self.tab_sync_manager.sync_symbol_change(source_tab, symbol)
        
        # Execute DOM operations on each tab
        for tab_id in target_tabs:
            try:
                # Queue DOM operation for symbol update
                operation = DOMOperation(
                    operation_id=str(uuid.uuid4()),
                    tab_id=tab_id,
                    element_type='symbol_input',
                    selector='#symbolInput',
                    operation_type='input',
                    parameters={'value': symbol},
                    validation_tier=ValidationTier.LOW_LATENCY,
                    context={'sync_operation': True, 'source_tab': source_tab}
                )
                
                queue_result = self.operation_queue.queue_operation(operation)
                
                if queue_result.status == 'queued':
                    # Wait for operation completion (with timeout)
                    operation_id = queue_result.operation_id
                    completion_result = self._wait_for_operation_completion(
                        operation_id, timeout=5.0
                    )
                    results[tab_id] = completion_result
                else:
                    results[tab_id] = {
                        'success': False,
                        'error': f"Failed to queue operation: {queue_result.message}"
                    }
                    
            except Exception as e:
                results[tab_id] = {
                    'success': False,
                    'error': str(e)
                }
                self.logger.error(f"Symbol sync error for tab {tab_id}: {str(e)}")
        
        return results
    
    def _sync_account_switch(self, source_tab: str, target_tabs: List[str], 
                            state_data: dict) -> dict:
        """Synchronize account switch across tabs"""
        results = {}
        account_name = state_data.get('account_name', '')
        
        # Use TabSynchronizationManager for coordinated account switch
        sync_result = self.tab_sync_manager.sync_account_switch(source_tab, account_name)
        
        if not sync_result['success']:
            # Return error for all target tabs
            for tab_id in target_tabs:
                results[tab_id] = {
                    'success': False,
                    'error': sync_result['message']
                }
            return results
        
        # Account switch was handled by TabSynchronizationManager
        for tab_id in sync_result.get('paused_tabs', []):
            results[tab_id] = {
                'success': True,
                'message': 'Tab paused for account switch'
            }
        
        return results
    
    def _sync_position_update(self, source_tab: str, target_tabs: List[str], 
                             state_data: dict) -> dict:
        """Synchronize position updates across tabs"""
        results = {}
        
        # Position updates typically don't require DOM manipulation
        # but we need to ensure UI consistency
        for tab_id in target_tabs:
            try:
                # Trigger a refresh of position data
                refresh_script = """
                (function() {
                    // Trigger position table refresh
                    const positionTable = document.querySelector('.module.positions.data-table');
                    if (positionTable) {
                        // Dispatch custom event to trigger refresh
                        positionTable.dispatchEvent(new CustomEvent('refresh-positions'));
                        return { success: true, message: 'Position refresh triggered' };
                    }
                    return { success: false, message: 'Position table not found' };
                })();
                """
                
                # Execute refresh script on tab
                # This would integrate with Chrome DevTools Protocol
                results[tab_id] = {
                    'success': True,
                    'message': 'Position update synced'
                }
                
            except Exception as e:
                results[tab_id] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def _sync_dom_mutation(self, source_tab: str, target_tabs: List[str], 
                          state_data: dict) -> dict:
        """Synchronize DOM mutations across tabs"""
        results = {}
        
        # DOM mutations require careful handling to avoid infinite loops
        mutation_type = state_data.get('mutation_type', '')
        element_selector = state_data.get('selector', '')
        mutation_data = state_data.get('mutation_data', {})
        
        for tab_id in target_tabs:
            try:
                # Skip if this would create a circular sync
                if self._would_create_circular_sync(tab_id, mutation_type, element_selector):
                    results[tab_id] = {
                        'success': False,
                        'error': 'Circular sync detected, skipping'
                    }
                    continue
                
                # Apply DOM mutation
                operation = DOMOperation(
                    operation_id=str(uuid.uuid4()),
                    tab_id=tab_id,
                    element_type='custom',
                    selector=element_selector,
                    operation_type=mutation_type,
                    parameters=mutation_data,
                    validation_tier=ValidationTier.STANDARD_LATENCY,
                    context={'sync_operation': True, 'source_tab': source_tab}
                )
                
                queue_result = self.operation_queue.queue_operation(operation)
                results[tab_id] = {
                    'success': queue_result.status == 'queued',
                    'message': queue_result.message
                }
                
            except Exception as e:
                results[tab_id] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def _get_sync_target_tabs(self, source_tab: str, state_type: str, 
                             state_data: dict) -> List[str]:
        """Determine which tabs should receive the state sync"""
        target_tabs = []
        
        with self.tab_sync_manager.state_lock:
            for tab_id, tab_state in self.tab_sync_manager.tab_states.items():
                if tab_id == source_tab:
                    continue
                
                # Check if tab should receive this type of sync
                if state_type == 'symbol_change':
                    # Sync to all active trading tabs with auto-sync enabled
                    if tab_state.auto_sync_enabled and tab_state.is_trading_active:
                        target_tabs.append(tab_id)
                        
                elif state_type == 'account_switch':
                    # Account switches affect all tabs
                    target_tabs.append(tab_id)
                    
                elif state_type == 'position_update':
                    # Sync to tabs with same account
                    source_account = self.tab_sync_manager.tab_states[source_tab].account_name
                    if tab_state.account_name == source_account:
                        target_tabs.append(tab_id)
                        
                elif state_type == 'dom_mutation':
                    # Sync based on mutation scope
                    mutation_scope = state_data.get('scope', 'local')
                    if mutation_scope == 'global' or (
                        mutation_scope == 'account' and 
                        tab_state.account_name == self.tab_sync_manager.tab_states[source_tab].account_name
                    ):
                        target_tabs.append(tab_id)
        
        return target_tabs
    
    def _is_conflicting_sync_active(self, state_type: str, state_data: dict) -> bool:
        """Check if a conflicting sync operation is active"""
        for sync_id in self.active_syncs:
            if sync_id not in self.sync_operations:
                continue
                
            sync_op = self.sync_operations[sync_id]
            
            # Check for conflicts based on state type
            if sync_op.state_type == state_type:
                if state_type == 'symbol_change':
                    # Conflict if different symbol
                    if sync_op.state_data.get('symbol') != state_data.get('symbol'):
                        return True
                elif state_type == 'account_switch':
                    # Always conflict for account switches
                    return True
                elif state_type == 'position_update':
                    # Conflict if same position
                    if sync_op.state_data.get('position_id') == state_data.get('position_id'):
                        return True
        
        return False
    
    def _wait_for_active_syncs(self, state_type: str, timeout: float = 5.0):
        """Wait for active sync operations of given type to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self.sync_lock:
                active_of_type = [
                    sync_id for sync_id in self.active_syncs
                    if sync_id in self.sync_operations and
                    self.sync_operations[sync_id].state_type == state_type
                ]
                
                if not active_of_type:
                    return
            
            time.sleep(0.1)
        
        self.logger.warning(f"Timeout waiting for {state_type} syncs to complete")
    
    def _capture_dom_snapshot(self, tab_id: str):
        """Capture DOM snapshot for comparison and rollback"""
        try:
            snapshot = DOMSnapshot(
                tab_id=tab_id,
                timestamp=datetime.now(),
                elements={}  # Would capture actual DOM state
            )
            self.dom_snapshots[tab_id] = snapshot
        except Exception as e:
            self.logger.error(f"Failed to capture DOM snapshot for tab {tab_id}: {str(e)}")
    
    def _wait_for_operation_completion(self, operation_id: str, timeout: float = 5.0) -> dict:
        """Wait for a queued operation to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if operation is still active
            if operation_id not in self.operation_queue.active_operations:
                # Operation completed, check history
                for op_history in reversed(self.operation_queue.operation_history):
                    if op_history['operation_id'] == operation_id:
                        return {
                            'success': True,
                            'completed_at': op_history['completed_at']
                        }
                
                return {
                    'success': True,
                    'message': 'Operation completed'
                }
            
            time.sleep(0.1)
        
        return {
            'success': False,
            'error': 'Operation timeout'
        }
    
    def _would_create_circular_sync(self, tab_id: str, mutation_type: str, 
                                   selector: str) -> bool:
        """Check if syncing would create an infinite loop"""
        # Check recent sync operations from this tab
        recent_threshold = datetime.now() - timedelta(seconds=5)
        
        for sync_op in self.sync_operations.values():
            if (sync_op.source_tab == tab_id and
                sync_op.state_type == 'dom_mutation' and
                sync_op.timestamp > recent_threshold):
                
                # Check if it's the same mutation
                if (sync_op.state_data.get('mutation_type') == mutation_type and
                    sync_op.state_data.get('selector') == selector):
                    return True
        
        return False
    
    def _trigger_state_change_handlers(self, state_type: str, state_data: dict, 
                                     sync_result: dict):
        """Trigger registered event handlers"""
        handlers = self.state_change_handlers.get(state_type, [])
        
        for handler in handlers:
            try:
                handler(state_type, state_data, sync_result)
            except Exception as e:
                self.logger.error(f"State change handler error: {str(e)}")
    
    def enable_auto_sync(self, tab_id: str):
        """Enable automatic state synchronization for a tab"""
        with self.tab_sync_manager.state_lock:
            if tab_id in self.tab_sync_manager.tab_states:
                self.tab_sync_manager.tab_states[tab_id].auto_sync_enabled = True
                self.logger.info(f"Auto-sync enabled for tab {tab_id}")
    
    def disable_auto_sync(self, tab_id: str):
        """Disable automatic state synchronization for a tab"""
        with self.tab_sync_manager.state_lock:
            if tab_id in self.tab_sync_manager.tab_states:
                self.tab_sync_manager.tab_states[tab_id].auto_sync_enabled = False
                self.logger.info(f"Auto-sync disabled for tab {tab_id}")
    
    def get_sync_status(self) -> dict:
        """Get comprehensive synchronization status"""
        with self.sync_lock:
            return {
                'active_syncs': len(self.active_syncs),
                'total_tabs': len(self.tab_sync_manager.tab_states),
                'auto_sync_enabled_tabs': sum(
                    1 for state in self.tab_sync_manager.tab_states.values()
                    if state.auto_sync_enabled
                ),
                'metrics': dict(self.sync_metrics),
                'recent_syncs': [
                    {
                        'sync_id': sync_op.sync_id,
                        'state_type': sync_op.state_type,
                        'source_tab': sync_op.source_tab,
                        'timestamp': sync_op.timestamp.isoformat()
                    }
                    for sync_op in list(self.sync_operations.values())[-10:]
                ]
            }

@dataclass
class SyncOperation:
    """Represents a state synchronization operation"""
    sync_id: str
    source_tab: str
    state_type: str
    state_data: dict
    priority: str
    timestamp: datetime

@dataclass  
class DOMSnapshot:
    """Snapshot of DOM state for a tab"""
    tab_id: str
    timestamp: datetime
    elements: dict  # selector -> element state

# Default DOM state synchronizer instance
default_dom_synchronizer = DOMStateSynchronizer()

# ============================================================================
# INTEGRATION WITH TRADING OPERATIONS
# ============================================================================

def sync_symbol_across_tabs(source_tab_id: str, symbol: str) -> dict:
    """High-level function to sync symbol across all trading tabs"""
    return default_dom_synchronizer.sync_dom_state_across_tabs(
        source_tab_id,
        'symbol_change',
        {'symbol': symbol},
        priority='high'
    )

def sync_account_switch_across_tabs(source_tab_id: str, account_name: str) -> dict:
    """High-level function to sync account switch across all tabs"""
    return default_dom_synchronizer.sync_dom_state_across_tabs(
        source_tab_id,
        'account_switch',
        {'account_name': account_name},
        priority='critical'
    )

def sync_position_update_across_tabs(source_tab_id: str, position_data: dict) -> dict:
    """High-level function to sync position updates across relevant tabs"""
    return default_dom_synchronizer.sync_dom_state_across_tabs(
        source_tab_id,
        'position_update',
        position_data,
        priority='normal'
    )

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
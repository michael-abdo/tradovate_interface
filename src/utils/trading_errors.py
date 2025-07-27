#!/usr/bin/env python3
"""
Comprehensive Error Handling Framework for Trading System

This module provides standardized error classes, severity levels, and structured
logging for all trading operations per CLAUDE.md principles.

Key Features:
- Hierarchical error classification
- Severity-based error handling (INFO, WARN, ERROR, CRITICAL)
- Structured error context capture
- Stack trace preservation
- Error aggregation and reporting
- Integration with existing Chrome communication errors

Per CLAUDE.md:
- Comprehensive logging for root cause analysis
- Real data context preservation
- Fail-fast principle enforcement
"""

import json
import logging
import traceback
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
import threading
from collections import defaultdict, deque

# Configure structured logging
logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for trading operations"""
    INFO = "INFO"        # Informational, no action needed
    WARN = "WARNING"     # Warning, may need attention
    ERROR = "ERROR"      # Error, operation failed but recoverable
    CRITICAL = "CRITICAL" # Critical, system stability at risk


class ErrorCategory(Enum):
    """Categories of trading system errors"""
    AUTHENTICATION = "AUTHENTICATION"      # Login/session errors
    CHROME_COMMUNICATION = "CHROME_COMM"   # Chrome DevTools errors
    DOM_OPERATION = "DOM_OPERATION"        # DOM manipulation errors
    ORDER_VALIDATION = "ORDER_VALIDATION"  # Order validation failures
    ORDER_EXECUTION = "ORDER_EXECUTION"    # Trade execution errors
    NETWORK = "NETWORK"                    # Network connectivity issues
    CONFIGURATION = "CONFIGURATION"        # Config/setup errors
    SYSTEM = "SYSTEM"                      # System-level errors
    DATA_INTEGRITY = "DATA_INTEGRITY"      # Data validation errors
    PERFORMANCE = "PERFORMANCE"            # Performance threshold violations


@dataclass
class ErrorContext:
    """Structured error context for comprehensive logging"""
    timestamp: str
    severity: ErrorSeverity
    category: ErrorCategory
    error_code: str
    message: str
    account: Optional[str] = None
    operation: Optional[str] = None
    stack_trace: Optional[str] = None
    chrome_tab_id: Optional[str] = None
    order_details: Optional[Dict[str, Any]] = None
    dom_state: Optional[Dict[str, Any]] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    additional_context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert enums to strings
        data['severity'] = self.severity.value
        data['category'] = self.category.value
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string for logging"""
        return json.dumps(self.to_dict(), indent=2)


class TradingError(Exception):
    """Base exception for all trading system errors"""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        error_code: str = "UNKNOWN",
        account: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message)
        self.context = ErrorContext(
            timestamp=datetime.now().isoformat(),
            severity=severity,
            category=category,
            error_code=error_code,
            message=message,
            account=account,
            operation=operation,
            stack_trace=traceback.format_exc(),
            **kwargs
        )
        
        # Log error immediately per CLAUDE.md comprehensive logging
        self._log_error()
    
    def _log_error(self):
        """Log error with appropriate level based on severity"""
        log_message = f"[{self.context.category.value}] {self.context.error_code}: {self.context.message}"
        
        if self.context.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra={'context': self.context.to_dict()})
        elif self.context.severity == ErrorSeverity.ERROR:
            logger.error(log_message, extra={'context': self.context.to_dict()})
        elif self.context.severity == ErrorSeverity.WARN:
            logger.warning(log_message, extra={'context': self.context.to_dict()})
        else:
            logger.info(log_message, extra={'context': self.context.to_dict()})


# Specific error classes for different trading operations

class AuthenticationError(TradingError):
    """Authentication and session management errors"""
    def __init__(self, message: str, account: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.AUTHENTICATION,
            error_code="AUTH_ERROR",
            account=account,
            **kwargs
        )


class ChromeCommunicationError(TradingError):
    """Chrome DevTools communication errors"""
    def __init__(self, message: str, tab_id: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.CHROME_COMMUNICATION,
            error_code="CHROME_ERROR",
            chrome_tab_id=tab_id,
            **kwargs
        )


class DOMOperationError(TradingError):
    """DOM manipulation and validation errors"""
    def __init__(self, message: str, element_selector: Optional[str] = None, 
                 dom_state: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.DOM_OPERATION,
            error_code="DOM_ERROR",
            dom_state=dom_state,
            **kwargs
        )
        if element_selector:
            self.context.additional_context = {'element_selector': element_selector}


class OrderValidationError(TradingError):
    """Order validation failures"""
    def __init__(self, message: str, order_details: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.ORDER_VALIDATION,
            error_code="ORDER_VALIDATION_FAILED",
            order_details=order_details,
            **kwargs
        )


class OrderExecutionError(TradingError):
    """Trade execution errors"""
    def __init__(self, message: str, order_details: Optional[Dict[str, Any]] = None, 
                 severity: ErrorSeverity = ErrorSeverity.CRITICAL, **kwargs):
        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.ORDER_EXECUTION,
            error_code="ORDER_EXECUTION_FAILED",
            order_details=order_details,
            **kwargs
        )


class NetworkError(TradingError):
    """Network connectivity issues"""
    def __init__(self, message: str, endpoint: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.NETWORK,
            error_code="NETWORK_ERROR",
            **kwargs
        )
        if endpoint:
            self.context.additional_context = {'endpoint': endpoint}


class ConfigurationError(TradingError):
    """Configuration and setup errors"""
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.CONFIGURATION,
            error_code="CONFIG_ERROR",
            **kwargs
        )
        if config_key:
            self.context.additional_context = {'config_key': config_key}


class DataIntegrityError(TradingError):
    """Data validation and integrity errors"""
    def __init__(self, message: str, data_type: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.DATA_INTEGRITY,
            error_code="DATA_INTEGRITY_ERROR",
            **kwargs
        )
        if data_type:
            self.context.additional_context = {'data_type': data_type}


class PerformanceError(TradingError):
    """Performance threshold violations"""
    def __init__(self, message: str, metric: str, threshold: float, actual: float, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.WARN,
            category=ErrorCategory.PERFORMANCE,
            error_code="PERFORMANCE_VIOLATION",
            **kwargs
        )
        self.context.additional_context = {
            'metric': metric,
            'threshold': threshold,
            'actual': actual,
            'violation_ratio': actual / threshold if threshold > 0 else float('inf')
        }


class ErrorAggregator:
    """
    Aggregates and reports errors for comprehensive analysis.
    Provides error trends, patterns, and summary statistics.
    """
    
    def __init__(self, max_errors_per_category: int = 1000):
        self._errors: Dict[ErrorCategory, deque] = defaultdict(
            lambda: deque(maxlen=max_errors_per_category)
        )
        self._error_counts: Dict[ErrorCategory, Dict[ErrorSeverity, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._lock = threading.Lock()
        self._start_time = datetime.now()
    
    def add_error(self, error: TradingError):
        """Add an error to the aggregator"""
        with self._lock:
            category = error.context.category
            severity = error.context.severity
            
            # Store error context
            self._errors[category].append(error.context)
            
            # Update counts
            self._error_counts[category][severity] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive error summary"""
        with self._lock:
            uptime = (datetime.now() - self._start_time).total_seconds()
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': uptime,
                'total_errors': sum(
                    sum(counts.values()) 
                    for counts in self._error_counts.values()
                ),
                'by_category': {},
                'by_severity': defaultdict(int),
                'recent_critical_errors': []
            }
            
            # Aggregate by category
            for category, counts in self._error_counts.items():
                summary['by_category'][category.value] = {
                    severity.value: count 
                    for severity, count in counts.items()
                }
                
                # Aggregate by severity
                for severity, count in counts.items():
                    summary['by_severity'][severity.value] += count
            
            # Get recent critical errors
            for category, errors in self._errors.items():
                for error in errors:
                    if error.severity == ErrorSeverity.CRITICAL:
                        summary['recent_critical_errors'].append(error.to_dict())
            
            # Sort critical errors by timestamp
            summary['recent_critical_errors'].sort(
                key=lambda x: x['timestamp'], 
                reverse=True
            )
            summary['recent_critical_errors'] = summary['recent_critical_errors'][:10]
            
            return summary
    
    def get_error_rate(self, category: Optional[ErrorCategory] = None, 
                       window_minutes: int = 5) -> float:
        """Calculate error rate for a category or overall"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
            error_count = 0
            
            if category:
                errors_to_check = [self._errors[category]]
            else:
                errors_to_check = self._errors.values()
            
            for error_list in errors_to_check:
                for error in error_list:
                    if datetime.fromisoformat(error.timestamp) > cutoff_time:
                        error_count += 1
            
            # Return errors per minute
            return error_count / window_minutes
    
    def clear_old_errors(self, hours: int = 24):
        """Clear errors older than specified hours"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            for category, errors in self._errors.items():
                # Filter out old errors
                self._errors[category] = deque(
                    (e for e in errors if datetime.fromisoformat(e.timestamp) > cutoff_time),
                    maxlen=errors.maxlen
                )


# Global error aggregator instance
error_aggregator = ErrorAggregator()


def log_and_aggregate_error(error: TradingError):
    """Helper function to log and aggregate errors"""
    error_aggregator.add_error(error)
    return error


# Structured logging formatter for error context
class ErrorContextFormatter(logging.Formatter):
    """Custom formatter that includes error context in log records"""
    
    def format(self, record):
        # Add error context if available
        if hasattr(record, 'context'):
            record.msg = f"{record.msg}\nContext: {json.dumps(record.context, indent=2)}"
        return super().format(record)


# Configure structured error logging
def configure_error_logging(log_file: Optional[str] = None):
    """Configure structured error logging with context"""
    formatter = ErrorContextFormatter(
        '[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    handlers = [console_handler]
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=handlers
    )


# Export key components
__all__ = [
    'ErrorSeverity',
    'ErrorCategory',
    'ErrorContext',
    'TradingError',
    'AuthenticationError',
    'ChromeCommunicationError',
    'DOMOperationError',
    'OrderValidationError',
    'OrderExecutionError',
    'NetworkError',
    'ConfigurationError',
    'DataIntegrityError',
    'PerformanceError',
    'ErrorAggregator',
    'error_aggregator',
    'log_and_aggregate_error',
    'configure_error_logging'
]
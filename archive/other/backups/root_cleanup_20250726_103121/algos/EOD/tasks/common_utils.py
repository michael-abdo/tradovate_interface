#!/usr/bin/env python3
"""
Common Utilities Module - Canonical implementations for frequently duplicated patterns.

This module consolidates common patterns found throughout the codebase:
- Exception handling with consistent logging
- Timezone-aware timestamp generation
- JSON serialization with custom encoders
- Logger initialization and configuration
- Path construction and management

Usage:
    from tasks.common_utils import safe_execute, get_utc_timestamp, save_json, get_logger
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable, Union, TextIO
from pathlib import Path
from functools import wraps
from decimal import Decimal
import pytz

# ============================================================================
# EXCEPTION HANDLING UTILITIES
# ============================================================================

class SafeExecutionResult:
    """Result container for safe execution operations"""
    def __init__(self, success: bool, result: Any = None, error: Optional[Exception] = None):
        self.success = success
        self.result = result
        self.error = error
        self.error_details = None
        if error:
            self.error_details = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc()
            }

def safe_execute(
    operation: str = None,
    log_errors: bool = True,
    reraise: bool = False,
    default_result: Any = None,
    allowed_exceptions: tuple = None
) -> Callable:
    """
    Decorator for consistent exception handling across the codebase.
    
    Args:
        operation: Description of the operation for logging
        log_errors: Whether to log errors when they occur
        reraise: Whether to re-raise the exception after logging
        default_result: Default value to return on error
        allowed_exceptions: Tuple of exceptions that should be re-raised
        
    Returns:
        SafeExecutionResult object with success status and result/error details
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> SafeExecutionResult:
            try:
                result = func(*args, **kwargs)
                return SafeExecutionResult(success=True, result=result)
            
            except Exception as e:
                # Re-raise critical exceptions
                if allowed_exceptions and isinstance(e, allowed_exceptions):
                    raise
                
                # Re-raise system exceptions that shouldn't be caught
                if isinstance(e, (KeyboardInterrupt, SystemExit, MemoryError)):
                    raise
                
                if log_errors:
                    logger = logging.getLogger(func.__module__)
                    op_desc = operation or f"{func.__name__}"
                    logger.error(f"Error in {op_desc}: {str(e)}", exc_info=True)
                
                if reraise:
                    raise
                
                return SafeExecutionResult(success=False, error=e, result=default_result)
        
        return wrapper
    return decorator

def handle_exception(
    exception: Exception,
    operation: str,
    logger: logging.Logger = None,
    reraise: bool = False
) -> Dict[str, Any]:
    """
    Centralized exception handling with consistent logging and reporting.
    
    Args:
        exception: The exception to handle
        operation: Description of the operation that failed
        logger: Logger to use (defaults to module logger)
        reraise: Whether to re-raise the exception
        
    Returns:
        Dictionary with error details
    """
    if logger is None:
        logger = get_logger()
    
    error_details = {
        'operation': operation,
        'error_type': type(exception).__name__,
        'error_message': str(exception),
        'traceback': traceback.format_exc(),
        'timestamp': get_utc_timestamp()
    }
    
    logger.error(f"Error in {operation}: {str(exception)}", exc_info=True)
    
    if reraise:
        raise exception
    
    return error_details

# ============================================================================
# TIMESTAMP UTILITIES
# ============================================================================

def get_utc_timestamp(include_microseconds: bool = False) -> str:
    """
    Get current UTC timestamp in ISO format.
    
    Args:
        include_microseconds: Whether to include microseconds precision
        
    Returns:
        ISO formatted UTC timestamp
    """
    now = datetime.now(timezone.utc)
    if include_microseconds:
        return now.isoformat()
    else:
        return now.replace(microsecond=0).isoformat()

def get_local_timestamp(timezone_name: str = "US/Eastern", include_microseconds: bool = False) -> str:
    """
    Get current timestamp in specified timezone.
    
    Args:
        timezone_name: Timezone identifier (e.g., 'US/Eastern', 'UTC')
        include_microseconds: Whether to include microseconds precision
        
    Returns:
        ISO formatted timestamp in specified timezone
    """
    tz = pytz.timezone(timezone_name)
    now = datetime.now(tz)
    if include_microseconds:
        return now.isoformat()
    else:
        return now.replace(microsecond=0).isoformat()

def get_trading_timestamp() -> str:
    """Get timestamp in US/Eastern timezone for trading systems."""
    return get_local_timestamp("US/Eastern")

def get_timestamp_filename() -> str:
    """Get timestamp formatted for use in filenames (no special characters)."""
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse ISO timestamp string to datetime object.
    
    Args:
        timestamp_str: ISO formatted timestamp string
        
    Returns:
        datetime object
    """
    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

# ============================================================================
# JSON UTILITIES
# ============================================================================

class EnhancedJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime, Decimal, and other common types."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

def save_json(
    data: Any,
    filepath: Union[str, Path],
    indent: int = 2,
    ensure_dir: bool = True,
    backup_existing: bool = False
) -> SafeExecutionResult:
    """
    Save data to JSON file with enhanced error handling and features.
    
    Args:
        data: Data to serialize
        filepath: Path to save the file
        indent: JSON indentation (None for compact)
        ensure_dir: Create directory if it doesn't exist
        backup_existing: Create backup of existing file
        
    Returns:
        SafeExecutionResult with operation status
    """
    @safe_execute(operation=f"save_json to {filepath}")
    def _save():
        filepath_obj = Path(filepath)
        
        if ensure_dir:
            filepath_obj.parent.mkdir(parents=True, exist_ok=True)
        
        if backup_existing and filepath_obj.exists():
            backup_path = filepath_obj.with_suffix(f".backup_{get_timestamp_filename()}.json")
            filepath_obj.rename(backup_path)
        
        with open(filepath_obj, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=EnhancedJSONEncoder, indent=indent, ensure_ascii=False)
        
        return str(filepath_obj)
    
    return _save()

def load_json(filepath: Union[str, Path]) -> SafeExecutionResult:
    """
    Load JSON data from file with error handling.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        SafeExecutionResult with loaded data or error
    """
    @safe_execute(operation=f"load_json from {filepath}")
    def _load():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return _load()

def to_json_string(data: Any, indent: int = None) -> str:
    """
    Convert data to JSON string with enhanced encoder.
    
    Args:
        data: Data to serialize
        indent: JSON indentation (None for compact)
        
    Returns:
        JSON string
    """
    return json.dumps(data, cls=EnhancedJSONEncoder, indent=indent, ensure_ascii=False)


# ============================================================================
# STATUS DICT PATTERNS
# ============================================================================

def create_status_response(status: str, message: str = None, **kwargs) -> Dict[str, Any]:
    """
    Create a standardized status response dictionary.
    
    Args:
        status: Status value (e.g., 'success', 'failed', 'error', 'pending')
        message: Optional message to include
        **kwargs: Additional fields to include in the response
        
    Returns:
        Dict with status and any additional fields
    """
    response = {"status": status}
    if message is not None:
        response["message"] = message
    response.update(kwargs)
    return response

def create_success_response(result: Any = None, message: str = None, **kwargs) -> Dict[str, Any]:
    """
    Create a success status response with optional result.
    
    Args:
        result: Optional result data to include
        message: Optional success message
        **kwargs: Additional fields to include
        
    Returns:
        Success status dict
    """
    response = {"status": "success"}
    if result is not None:
        response["result"] = result
    if message is not None:
        response["message"] = message
    if "timestamp" not in kwargs:
        response["timestamp"] = get_trading_timestamp()
    response.update(kwargs)
    return response

def create_failure_response(error: Union[str, Exception], status: str = "failed", **kwargs) -> Dict[str, Any]:
    """
    Create a failure status response with error details.
    
    Args:
        error: Error message or exception
        status: Status value (default: 'failed', can be 'error')
        **kwargs: Additional fields to include
        
    Returns:
        Failure status dict
    """
    error_msg = str(error) if isinstance(error, Exception) else error
    response = {"status": status, "error": error_msg}
    if "timestamp" not in kwargs:
        response["timestamp"] = get_trading_timestamp()
    response.update(kwargs)
    return response

# ============================================================================
# LOGGER UTILITIES
# ============================================================================

class LoggerMixin:
    """Mixin class that provides consistent logger initialization."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__module__)
        return self._logger

def get_logger(
    name: str = None,
    level: int = logging.INFO,
    format_string: str = None
) -> logging.Logger:
    """
    Get configured logger with consistent formatting.
    
    Args:
        name: Logger name (defaults to calling module)
        level: Logging level
        format_string: Custom format string
        
    Returns:
        Configured logger instance
    """
    if name is None:
        # Get the calling module's name
        frame = sys._getframe(1)
        name = frame.f_globals.get('__name__', __name__)
    
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    
    return logger

def setup_structured_logging(
    log_level: str = "INFO",
    log_file: str = None,
    include_timestamp: bool = True
) -> None:
    """
    Setup structured logging for the entire application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        include_timestamp: Whether to include timestamps in logs
    """
    level = getattr(logging, log_level.upper())
    
    format_parts = []
    if include_timestamp:
        format_parts.append('%(asctime)s')
    format_parts.extend(['%(name)s', '%(levelname)s', '%(message)s'])
    
    format_string = ' - '.join(format_parts)
    
    logging.basicConfig(
        level=level,
        format=format_string,
        filename=log_file,
        filemode='a' if log_file else None
    )

# ============================================================================
# PATH UTILITIES
# ============================================================================

class PathManager:
    """Centralized path management for the project."""
    
    _project_root: Optional[Path] = None
    
    @classmethod
    def get_project_root(cls) -> Path:
        """
        Get project root directory, cached for performance.
        
        Returns:
            Path object for project root
        """
        if cls._project_root is None:
            # Start from this file and go up to find the project root
            current = Path(__file__).parent
            
            # Look for key project files/directories
            markers = ['.git', 'tasks', 'README.md', 'CHANGELOG.md']
            
            while current.parent != current:  # Not at filesystem root
                if any((current / marker).exists() for marker in markers):
                    cls._project_root = current
                    break
                current = current.parent
            else:
                # Fallback: assume parent of tasks directory
                cls._project_root = Path(__file__).parent.parent
        
        return cls._project_root
    
    @classmethod
    def get_tasks_dir(cls) -> Path:
        """Get tasks directory path."""
        return cls.get_project_root() / "tasks"
    
    @classmethod
    def get_outputs_dir(cls) -> Path:
        """Get outputs directory path."""
        return cls.get_project_root() / "outputs"
    
    @classmethod
    def get_relative_path(cls, target_path: Union[str, Path], base: Union[str, Path] = None) -> Path:
        """
        Get relative path from base to target.
        
        Args:
            target_path: Target path
            base: Base path (defaults to project root)
            
        Returns:
            Relative path from base to target
        """
        if base is None:
            base = cls.get_project_root()
        
        return Path(target_path).relative_to(Path(base))
    
    @classmethod
    def ensure_directory(cls, directory: Union[str, Path]) -> Path:
        """
        Ensure directory exists, creating it if necessary.
        
        Args:
            directory: Directory path to ensure exists
            
        Returns:
            Path object for the directory
        """
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    @classmethod
    def get_timestamped_filename(cls, base_name: str, extension: str = None) -> str:
        """
        Generate timestamped filename.
        
        Args:
            base_name: Base filename without extension
            extension: File extension (with or without dot)
            
        Returns:
            Timestamped filename
        """
        timestamp = get_timestamp_filename()
        
        if extension:
            if not extension.startswith('.'):
                extension = '.' + extension
            return f"{base_name}_{timestamp}{extension}"
        else:
            return f"{base_name}_{timestamp}"

# ============================================================================
# CANONICAL EXCEPTION HANDLING PATTERNS
# ============================================================================

def add_validation_error(
    validation_results: Dict[str, Any], 
    test_name: str, 
    error: Exception,
    print_error: bool = True
) -> None:
    """
    Canonical implementation for validation error handling pattern.
    
    Used by 71+ instances across test_validation.py files.
    
    Args:
        validation_results: The validation results dict to update
        test_name: Name of the test that failed
        error: The exception that occurred
        print_error: Whether to print the error message
    """
    validation_results["tests"].append({
        "name": test_name,
        "passed": False,
        "error": str(error)
    })
    
    if print_error:
        print(f"   ✗ Error: {error}")

def create_failure_response(
    error: Exception,
    operation: str = "operation",
    **additional_fields
) -> Dict[str, Any]:
    """
    Canonical implementation for failure response pattern.
    
    Used by 15+ instances across integration.py files.
    
    Args:
        error: The exception that occurred
        operation: Description of the failed operation
        **additional_fields: Additional fields to include in response
        
    Returns:
        Standardized failure response dictionary
    """
    response = {
        "status": "failed",
        "error": str(error),
        "timestamp": get_utc_timestamp()
    }
    response.update(additional_fields)
    return response

def log_and_return_false(
    logger: logging.Logger = None,
    operation: str = "operation"
) -> Callable:
    """
    Decorator for log-and-return-False exception handling pattern.
    
    Used by 20+ instances across validator and check functions.
    
    Args:
        logger: Logger to use (defaults to module logger)
        operation: Description of the operation for error message
        
    Returns:
        Decorator that logs exceptions and returns False
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if logger is None:
                    # Try to get logger from self if it's a method
                    if args and hasattr(args[0], 'logger'):
                        log = args[0].logger
                    else:
                        log = get_logger()
                else:
                    log = logger
                
                log.error(f"Error in {operation}: {e}")
                return False
        return wrapper
    return decorator

def log_and_return_none(
    logger: logging.Logger = None,
    operation: str = "operation"
) -> Callable:
    """
    Decorator for log-and-return-None exception handling pattern.
    
    Used by 5+ instances across data fetching functions.
    
    Args:
        logger: Logger to use (defaults to module logger)
        operation: Description of the operation for error message
        
    Returns:
        Decorator that logs exceptions and returns None
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if logger is None:
                    # Try to get logger from self if it's a method
                    if args and hasattr(args[0], 'logger'):
                        log = args[0].logger
                    else:
                        log = get_logger()
                else:
                    log = logger
                
                log.error(f"Error in {operation}: {e}")
                return None
        return wrapper
    return decorator

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_current_module_logger() -> logging.Logger:
    """Get logger for the calling module."""
    frame = sys._getframe(1)
    module_name = frame.f_globals.get('__name__', __name__)
    return get_logger(module_name)

def safe_file_operation(operation: str = "file operation"):
    """Decorator specifically for file operations with enhanced error handling."""
    return safe_execute(
        operation=operation,
        log_errors=True,
        reraise=False,
        allowed_exceptions=(KeyboardInterrupt, SystemExit)
    )

# Initialize module logger
logger = get_logger(__name__)
logger.info("Common utilities module loaded successfully")
#!/usr/bin/env python3
"""
Comprehensive tests for common_utils module.
Tests all utilities for correctness and edge cases.
"""

import os
import sys
import json
import tempfile
import logging
from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal

# Add tasks directory to path for testing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from common_utils import (
        safe_execute, SafeExecutionResult, handle_exception,
        get_utc_timestamp, get_local_timestamp, get_trading_timestamp,
        get_timestamp_filename, parse_timestamp,
        save_json, load_json, to_json_string, EnhancedJSONEncoder,
        get_logger, LoggerMixin, setup_structured_logging,
        PathManager,
        add_validation_error, create_failure_response, 
        log_and_return_false, log_and_return_none,
        create_status_response, create_success_response
    )
    UTILS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import common_utils: {e}")
    UTILS_AVAILABLE = False

def test_safe_execute_decorator():
    """Test the safe_execute decorator."""
    print("Testing safe_execute decorator...")
    
    @safe_execute(operation="test_function")
    def successful_function():
        return "success"
    
    @safe_execute(operation="failing_function")
    def failing_function():
        raise ValueError("Test error")
    
    # Test successful execution
    result = successful_function()
    assert isinstance(result, SafeExecutionResult)
    assert result.success is True
    assert result.result == "success"
    assert result.error is None
    
    # Test failed execution
    result = failing_function()
    assert isinstance(result, SafeExecutionResult)
    assert result.success is False
    assert result.error is not None
    assert isinstance(result.error, ValueError)
    assert result.error_details is not None
    
    print("✓ safe_execute decorator tests passed")

def test_timestamp_utilities():
    """Test timestamp utility functions."""
    print("Testing timestamp utilities...")
    
    # Test UTC timestamp
    utc_ts = get_utc_timestamp()
    assert isinstance(utc_ts, str)
    assert 'T' in utc_ts  # ISO format
    assert utc_ts.endswith('+00:00')  # UTC timezone
    
    # Test with microseconds
    utc_ts_micro = get_utc_timestamp(include_microseconds=True)
    assert len(utc_ts_micro) > len(utc_ts)  # Should be longer with microseconds
    
    # Test trading timestamp (should work without pytz if not available)
    try:
        trading_ts = get_trading_timestamp()
        assert isinstance(trading_ts, str)
        print("✓ Trading timestamp working")
    except ImportError:
        print("⚠ pytz not available, skipping trading timestamp test")
    
    # Test filename timestamp
    filename_ts = get_timestamp_filename()
    assert isinstance(filename_ts, str)
    assert '_' in filename_ts
    assert len(filename_ts) == 15  # YYYYMMDD_HHMMSS
    
    # Test timestamp parsing
    parsed = parse_timestamp(utc_ts)
    assert isinstance(parsed, datetime)
    
    print("✓ Timestamp utilities tests passed")

def test_json_utilities():
    """Test JSON utility functions."""
    print("Testing JSON utilities...")
    
    # Test data with various types
    test_data = {
        'string': 'test',
        'number': 42,
        'decimal': Decimal('123.45'),
        'datetime': datetime.now(timezone.utc),
        'list': [1, 2, 3],
        'nested': {'key': 'value'}
    }
    
    # Test JSON string conversion
    json_str = to_json_string(test_data, indent=2)
    assert isinstance(json_str, str)
    assert '"string": "test"' in json_str
    
    # Test file operations with temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Test save_json
        save_result = save_json(test_data, tmp_path)
        assert save_result.success is True
        assert os.path.exists(tmp_path)
        
        # Test load_json
        load_result = load_json(tmp_path)
        assert load_result.success is True
        assert load_result.result['string'] == 'test'
        assert load_result.result['number'] == 42
        
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
    print("✓ JSON utilities tests passed")

def test_logger_utilities():
    """Test logger utility functions."""
    print("Testing logger utilities...")
    
    # Test basic logger creation
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"
    
    # Test LoggerMixin
    class TestClass(LoggerMixin):
        def test_method(self):
            return self.logger
    
    test_obj = TestClass()
    logger = test_obj.test_method()
    assert isinstance(logger, logging.Logger)
    
    print("✓ Logger utilities tests passed")

def test_path_manager():
    """Test PathManager class."""
    print("Testing PathManager...")
    
    # Test project root detection
    root = PathManager.get_project_root()
    assert isinstance(root, Path)
    assert root.exists()
    
    # Test tasks directory
    tasks_dir = PathManager.get_tasks_dir()
    assert isinstance(tasks_dir, Path)
    
    # Test directory creation with temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir) / "test_subdir" / "nested"
        created_dir = PathManager.ensure_directory(test_dir)
        assert created_dir.exists()
        assert created_dir.is_dir()
    
    # Test timestamped filename generation
    filename = PathManager.get_timestamped_filename("test", "txt")
    assert filename.startswith("test_")
    assert filename.endswith(".txt")
    
    print("✓ PathManager tests passed")

def test_exception_handling():
    """Test exception handling utilities."""
    print("Testing exception handling...")
    
    # Test handle_exception function
    try:
        raise ValueError("Test exception")
    except Exception as e:
        error_details = handle_exception(e, "test_operation", reraise=False)
        assert isinstance(error_details, dict)
        assert error_details['operation'] == "test_operation"
        assert error_details['error_type'] == "ValueError"
        assert "Test exception" in error_details['error_message']
    
    print("✓ Exception handling tests passed")

def test_status_dict_patterns():
    """Test status dict pattern utilities."""
    print("\nTesting status dict patterns...")
    
    # Test create_status_response
    response = create_status_response("pending")
    assert response == {"status": "pending"}
    
    response = create_status_response("error", "Something went wrong")
    assert response["status"] == "error"
    assert response["message"] == "Something went wrong"
    
    response = create_status_response("custom", data={"value": 42}, code=200)
    assert response["status"] == "custom"
    assert response["data"] == {"value": 42}
    assert response["code"] == 200
    
    # Test create_success_response
    response = create_success_response()
    assert response["status"] == "success"
    assert "timestamp" in response
    
    response = create_success_response(result={"contracts": 100})
    assert response["status"] == "success"
    assert response["result"] == {"contracts": 100}
    
    custom_ts = "2025-06-30T10:00:00"
    response = create_success_response(
        result=42,
        message="Operation completed",
        timestamp=custom_ts
    )
    assert response["message"] == "Operation completed"
    assert response["timestamp"] == custom_ts
    
    # Test create_failure_response
    response = create_failure_response("Database connection failed")
    assert response["status"] == "failed"
    assert response["error"] == "Database connection failed"
    assert "timestamp" in response
    
    try:
        raise ValueError("Invalid input")
    except ValueError as e:
        response = create_failure_response(e)
        assert response["error"] == "Invalid input"
    
    response = create_failure_response("API limit exceeded", status="error")
    assert response["status"] == "error"
    
    response = create_failure_response(
        "Validation failed",
        field="email",
        value="invalid@"
    )
    assert response["field"] == "email"
    assert response["value"] == "invalid@"
    
    print("✓ Status dict pattern tests passed")

def test_canonical_exception_patterns():
    """Test the new canonical exception handling patterns."""
    print("Testing canonical exception patterns...")
    
    # Test add_validation_error
    validation_results = {"tests": []}
    try:
        raise ValueError("Test validation error")
    except Exception as e:
        add_validation_error(validation_results, "test_case", e, print_error=False)
    
    assert len(validation_results["tests"]) == 1
    assert validation_results["tests"][0]["name"] == "test_case"
    assert validation_results["tests"][0]["passed"] is False
    assert "Test validation error" in validation_results["tests"][0]["error"]
    
    # Test create_failure_response
    try:
        raise RuntimeError("Test failure")
    except Exception as e:
        response = create_failure_response(e, "test_operation", extra_field="test_value")
    
    assert response["status"] == "failed"
    assert "Test failure" in response["error"]
    assert "timestamp" in response
    assert response["extra_field"] == "test_value"
    
    # Test log_and_return_false decorator
    @log_and_return_false(operation="test_validation")
    def failing_validator():
        raise ValueError("Validation failed")
    
    result = failing_validator()
    assert result is False
    
    # Test log_and_return_none decorator
    @log_and_return_none(operation="test_fetch")
    def failing_fetcher():
        raise ConnectionError("Fetch failed")
    
    result = failing_fetcher()
    assert result is None
    
    print("✓ Canonical exception pattern tests passed")

def run_all_tests():
    """Run all tests for common_utils module."""
    if not UTILS_AVAILABLE:
        print("❌ Cannot run tests: common_utils module not available")
        return False
    
    print("=" * 60)
    print("RUNNING COMPREHENSIVE TESTS FOR COMMON_UTILS")
    print("=" * 60)
    
    try:
        test_safe_execute_decorator()
        test_timestamp_utilities()
        test_json_utilities()
        test_logger_utilities()
        test_path_manager()
        test_exception_handling()
        test_status_dict_patterns()
        test_canonical_exception_patterns()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED SUCCESSFULLY")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
# Chrome Logging in Tests

This document explains how to use the Chrome logging integration in tests to capture browser console logs during tests.

## Overview

The Chrome logging integration allows you to:

1. Capture all JavaScript console logs, errors, warnings, and debug messages during tests
2. Save these logs to files for later analysis
3. Verify expected log messages in your tests
4. Work with both mock Chrome tabs and real Chrome browser instances

## Test Fixtures

### 1. Chrome Logger Fixtures

Two main fixtures are available:

- `chrome_logger`: General-purpose fixture for a Chrome logger with any tab
- `mock_tab_with_logger`: Pre-configured fixture with a mock Chrome tab and logger
- `real_chrome_logger`: Connects to a real Chrome browser instance with remote debugging

### 2. Using the Fixtures

#### With Mock Chrome Tab

```python
def test_example_with_mock(mock_tab_with_logger):
    # Unpack the fixture
    mock_tab, logger, log_capture = mock_tab_with_logger
    
    # Simulate logs from Chrome
    mock_tab.trigger_console_api(type="log", args=[{"value": "Test message"}])
    mock_tab.trigger_exception(description="Test exception")
    
    # Verify logs were captured
    logs = log_capture.get_logs()
    assert len(logs) >= 2  # At least the 2 events we triggered
    assert log_capture.get_logs_containing("Test message")
```

#### With Real Chrome Browser

```python
@pytest.mark.skip(reason="Requires a running Chrome instance with remote debugging")
def test_example_with_real_chrome(real_chrome_logger):
    # Unpack the fixture
    tab, browser, logger, log_capture = real_chrome_logger
    
    # Navigate to a URL and execute JavaScript
    tab.Page.navigate(url="https://example.com")
    tab.Runtime.evaluate(expression="console.log('Test message')")
    
    # Verify logs were captured
    assert log_capture.wait_for_log(pattern="Test message", timeout=1.0)
```

## Log Capture Utility

The `LogCapture` class provides these features:

- `get_logs()`: Get all captured logs
- `get_logs_by_level(level)`: Get logs of a specific level (e.g., "INFO", "ERROR")
- `get_logs_containing(text)`: Get logs containing specific text
- `verify_logs(expected_entries)`: Verify expected log entries exist
- `wait_for_log(pattern, level, timeout)`: Wait for a specific log to appear

## Starting Chrome for Tests

To run tests with a real Chrome browser:

1. Start Chrome with remote debugging:

```bash
./tests/test_chrome_connection.sh start
```

2. Run tests that use the `real_chrome_logger` fixture:

```bash
pytest -v tests/test_chrome_logs.py::TestChromeLogging::test_real_chrome_logger
```

## Log Files

All Chrome logs are saved to:

- **Mock tests**: `{pytest_tmpdir}/chrome_logs/`
- **Real browser tests**: A temporary directory that's shown in the test output

## Tips for Effective Testing

1. **Use wait_for_log for asynchronous operations**: When testing operations that might produce logs asynchronously, use `wait_for_log` with an appropriate timeout.

2. **Check log levels appropriately**: Use the right log level for your verification, e.g., "ERROR" for exceptions, "WARNING" for warnings.

3. **Clear logs between test phases**: If your test has multiple phases, you can use `log_capture.clear_logs()` to clean the log buffer before a new phase.

4. **Use partial matching for flexibility**: When verifying logs, the `partial_match=True` option (default) allows more flexible matching across browser versions and implementations.

5. **Check both presence and absence**: Sometimes it's important to verify that certain error logs do NOT appear in your tests.

## Example Test Cases

See `tests/test_chrome_logs.py` for complete examples of using the Chrome logging fixtures in tests.
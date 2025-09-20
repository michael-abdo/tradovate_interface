# Tradovate Interface Tests

This directory contains unit tests for the Tradovate Interface project.

## Test Structure

The tests are organized to mirror the project structure:

- `conftest.py` - Contains shared fixtures and test utilities
- `test_login_helper.py` - Tests for the login_helper.py module
- `test_auto_login.py` - Tests for the auto_login.py module
- `test_chrome_logger.py` - Tests for the chrome_logger.py module

## Running Tests

To run all tests:

```bash
python -m pytest
```

To run a specific test file:

```bash
python -m pytest tests/test_login_helper.py
```

To run tests with verbose output:

```bash
python -m pytest -v
```

## Test Coverage

These tests cover core functionality including:

1. Login helper functionality
   - Successfully connecting to Chrome
   - Finding or creating Tradovate tabs
   - Loading credentials from files
   - Waiting for elements
   - Executing JavaScript

2. Auto-login functionality
   - Starting Chrome with debugging enabled
   - Connecting to Chrome via DevTools Protocol
   - Injecting login scripts
   - Disabling alerts
   - Managing multiple Chrome instances

3. Chrome logger functionality
   - Capturing browser logs, console output, and exceptions
   - Writing to log files
   - Processing callback functions
   - Event handling

## Mock Strategy

Tests use mocks for Chrome Browser and Tab instances to avoid requiring a real Chrome browser for testing. The mocks simulate Chrome's DevTools Protocol responses and behaviors.

Key mocks:

- `MockTab` - Simulates a Chrome tab with methods like `evaluate`
- `MockBrowser` - Simulates a Chrome browser with methods like `list_tab` and `new_tab`
- File system mocks - For testing credential loading and log file writing
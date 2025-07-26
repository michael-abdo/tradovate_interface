# Tradovate Interface Testing

This document explains the testing framework for the Tradovate Interface application.

## Test Types

The testing framework includes several types of tests:

1. **Unit Tests**: Fast, isolated tests that don't require browser interaction.
2. **Smoke Tests**: Basic functionality checks to ensure core components work.
3. **Integration Tests**: Tests that validate interactions between components.
4. **Full Workflow Tests**: Complete end-to-end tests that execute real trading workflows.

## Test Structure

Test files are organized in the `tests/` directory:

- `conftest.py`: Contains shared fixtures and test utilities
- `test_*.py`: Individual test files for different components
- `test_smoke.py`: Basic smoke test for quick validation
- `test_integration.py`: Tests interactions between components
- `test_full_workflow.py`: End-to-end workflow tests

## Running Tests

There are several ways to run the tests:

### Using run_tests.py Script

The simplest way is to use the provided test runner script:

```bash
# Run smoke test
python launchers/run_tests.py smoke

# Run unit tests
python launchers/run_tests.py unit

# Run integration tests with credentials
python launchers/run_tests.py integration --username your_username --password your_password

# Run full workflow test with credentials
python launchers/run_tests.py workflow --username your_username --password your_password
```

### Using pytest Directly

You can also run tests directly with pytest:

```bash
# Run all tests
python -m pytest

# Run a specific test file
python -m pytest tests/test_smoke.py

# Run tests with verbose output
python -m pytest -xvs tests/
```

### Using Specific Launcher Scripts

For the full workflow test, you can use the dedicated launcher:

```bash
python launchers/test_full_workflow_launcher.py --username your_username --password your_password
```

## Environment Variables

The test framework uses several environment variables:

- `TRADOVATE_TEST_USERNAME`: Tradovate username for login
- `TRADOVATE_TEST_PASSWORD`: Tradovate password for login
- `TRADOVATE_TEST_LOGIN`: Set to "true" to run tests that require login
- `SKIP_BROWSER_TESTS`: Set to "true" to skip tests that require a browser
- `SKIP_INTEGRATION_TESTS`: Set to "true" to skip integration tests

These can be set in the shell or passed via the launcher scripts.

## Full Workflow Test

The full workflow test (`test_full_workflow.py`) is a comprehensive test that validates the entire trading process:

1. Starts Chrome with remote debugging
2. Auto-logins to Tradovate
3. Starts the dashboard
4. Executes a trade
5. Confirms the position in the account

This test requires valid Tradovate credentials and will execute an actual trade in your account. It is recommended to use a paper trading account for testing.

To run this test:

```bash
python launchers/test_full_workflow_launcher.py --username your_username --password your_password
```

## Important Notes

1. **Use Paper Trading**: Always use paper/simulation trading accounts for testing to avoid real financial consequences.

2. **Credential Management**: The test framework will backup and restore your credentials, but it's good practice to double-check after testing.

3. **Chrome Processes**: If tests fail to clean up properly, you may need to manually kill Chrome processes that were started with remote debugging:
   ```bash
   pkill -f "remote-debugging-port"
   ```

4. **Test Data**: The tests use minimal contracts (quantity 1) for safety, but be aware that they still place real orders in your trading account.
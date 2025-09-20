# Tradovate Login Helper

This module allows you to connect to an existing Chrome instance and automatically log in to Tradovate. It's designed to be used as a component in other scripts that need to interact with Tradovate.

## Features

- Connect to Chrome with DevTools Protocol
- Find or create Tradovate tabs
- Inject login scripts with your credentials
- Wait for elements to appear in the DOM
- Execute JavaScript in the browser
- Utility functions for common operations

## Prerequisites

- Chrome browser running with remote debugging enabled
- pychrome library (`pip install pychrome`)
- Your Tradovate credentials

## Starting Chrome with Remote Debugging

Before using this helper, start Chrome with remote debugging enabled:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

Or use the existing `auto_login.py` script to launch Chrome instances.

## Basic Usage

### Example 1: Simple Login

```python
from login_helper import login_to_existing_chrome

# Connect to Chrome and login to Tradovate
success, tab, browser = login_to_existing_chrome(port=9222)

if success:
    print("Login successful!")
else:
    print("Login failed")
```

### Example 2: Login and Execute Actions

```python
from login_helper import login_to_existing_chrome, wait_for_element, execute_js
import time

# Login to Tradovate
success, tab, browser = login_to_existing_chrome(port=9222)

if success:
    # Wait for the dashboard to appear
    if wait_for_element(tab, ".desktop-dashboard", timeout=15):
        # Execute custom JavaScript
        execute_js(tab, """
            console.log("Successfully logged in, now performing other actions...");
            // Your custom JavaScript here
        """)
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
```

## Command Line Usage

You can also use the `login_helper.py` script directly from the command line:

```bash
# Login using credentials from credentials.json
./login_helper.py --port 9222

# Login with specific credentials
./login_helper.py --port 9222 --username your_username --password your_password
```

## Example Script

An example script `example_using_login.py` is included that demonstrates how to:

1. Login to Tradovate
2. Change the trading symbol
3. Set a quantity
4. Place a trade

You can run it with:

```bash
./example_using_login.py --port 9222 --symbol NQ --action Buy --quantity 1
```

## Sequential Operations with Controlled Timing

The example script shows how to use the helper for sequential operations with controlled timing:

1. Login to Tradovate (wait for completion)
2. Change the symbol (wait for completion)
3. Set the quantity (wait for completion)
4. Execute the trade

This ensures each operation completes before the next one begins, which is critical for reliable automation.

## Adding Delays Between Operations

The example uses appropriate delays between operations to ensure the UI has time to update:

```python
# Allow time for the symbol to load
time.sleep(2)

# Set quantity
# ... code to set quantity ...

# Allow time for UI to update
time.sleep(1)

# Click Buy or Sell button
# ... code to execute trade ...
```

These delays help ensure each operation completes before the next one begins.
# Troubleshooting Guide

This guide covers common issues and their solutions when working with the Tradovate Interface.

## Module Import Errors

### Error: `ModuleNotFoundError: No module named 'src'`

This error occurs when Python cannot find the `src` module. This typically happens when you run a script directly without properly setting the Python path.

#### Solution:

1. **Use the main entry point (Recommended)**:
   ```bash
   python main.py [component]
   ```
   Example: `python main.py webhook`

2. **Use the launcher scripts**:
   ```bash
   python launchers/pinescript_webhook_launcher.py
   ```

3. **Run from project root directory**:
   ```bash
   # Navigate to the project root first
   cd /path/to/tradovate_interface
   python src/pinescript_webhook.py
   ```

## Chrome Connection Issues

### Error: `No Tradovate connections found`

This error occurs when the webhook service or app cannot find any active Chrome instances with Tradovate tabs.

#### Solution:

1. Make sure auto_login.py is running:
   ```bash
   python main.py login
   ```

2. Check if Chrome is running with remote debugging enabled:
   ```bash
   ps aux | grep chrome
   ```
   Look for Chrome processes with the `--remote-debugging-port` flag.

3. Try connecting to an existing Chrome instance:
   ```bash
   python main.py login-helper --port 9222
   ```

## Webhook Service Issues

### Error: `HTTPConnectionPool(host='localhost', port=6000): Max retries exceeded`

This error occurs when your TradingView alerts cannot connect to the webhook service.

#### Solution:

1. Make sure the webhook service is running:
   ```bash
   python main.py webhook
   ```

2. Check if the service is accessible at the correct URL:
   ```bash
   curl http://localhost:6000/webhook
   ```

3. Verify your ngrok tunnel is working (if using ngrok):
   ```bash
   curl https://your-ngrok-domain.ngrok.app/webhook
   ```

## Dependencies and Installation

### Error: `ImportError: No module named 'pychrome'`

This occurs when you're missing required Python packages.

#### Solution:

Install all required dependencies:
```bash
pip install -r requirements.txt
```

Or install specific packages:
```bash
pip install pychrome flask requests
```

## Adding Python Path Programmatically

If you're creating a new script or having import issues, add this code at the top:

```python
import os
import sys

# Add the project root to the path so we can import from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Now you can import from src
from src.app import TradovateController
```

## Chrome Browser Issues

### Error: `Failed to start Chrome`

This occurs when the script cannot launch Chrome with debugging enabled.

#### Solution:

1. Make sure Chrome is installed and accessible from the command line
2. Try different debugging ports if 9222 is already in use:
   ```bash
   python main.py login-helper --port 9223
   ```
3. Check if Chrome is already running with debugging enabled:
   ```bash
   curl http://localhost:9222/json/version
   ```

## Testing Webhook Integration

To test if your webhook service is working correctly:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"symbol":"NQ","action":"Buy","orderQty":1,"strategy":"DEFAULT"}' http://localhost:6000/webhook
```

You should see a response indicating the trade was processed.
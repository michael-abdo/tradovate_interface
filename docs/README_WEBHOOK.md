# Tradovate PineScript Webhook Server

This README provides instructions for running the PineScript webhook server properly.

## How to Run the Webhook Server

### Option 1: Using the Launcher Script (Recommended)

```bash
# From any directory
/Users/Mike/trading/tradovate_interface/launchers/pinescript_webhook_launcher.py
```

### Option 2: Using main.py

```bash
# From the project root directory
cd /Users/Mike/trading/tradovate_interface
python main.py webhook
```

### Option 3: From the project root

If you need to run the script directly, make sure you're in the project root directory:

```bash
# From the project root directory
cd /Users/Mike/trading/tradovate_interface
python src/pinescript_webhook.py
```

## Common Issues

### ModuleNotFoundError: No module named 'src'

This error occurs when running the script from the wrong directory, which prevents Python from finding the modules.

**Solution:**
1. Always use one of the recommended run methods above
2. Make sure to run from the project root directory
3. Use the provided launcher scripts that correctly set up the Python path

## Dependencies

Make sure all required packages are installed:

```bash
cd /Users/Mike/trading/tradovate_interface
pip install -r requirements.txt
```

## For More Information

See the detailed webhook documentation in `/Users/Mike/trading/tradovate_interface/docs/WEBHOOK_SETUP.md`.
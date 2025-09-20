# Tradovate Webhook Service Setup

This document provides instructions on how to properly set up and run the webhook service for the Tradovate Interface.

## Running the Webhook Service

### Option 1: Using the Launcher Script (Recommended)

The easiest way to run the webhook service is to use the provided launcher script:

```bash
# From the project root directory
./launchers/run_webhook.sh
```

This script properly sets up the Python path to ensure all module imports work correctly.

### Option 2: Using main.py (Recommended)

You can also use the main entry point script:

```bash
# From the project root directory
python main.py webhook
```

### Option 3: Running the Script Directly (Not Recommended)

If you need to run the webhook script directly, make sure you're in the project root directory:

```bash
# From the project root directory
python src/pinescript_webhook.py
```

Running the script from other directories may cause import errors.

## Webhook Endpoints

The webhook service provides the following endpoints:

- `GET /`: Homepage with server status
- `GET /health`: Health check endpoint returning server status
- `GET /webhook`: Simple status page for manual checks
- `POST /webhook`: Main endpoint for receiving webhook data

## Expected Webhook Payload Format

The webhook service expects a JSON payload with at least the following field:

- `symbol`: The trading symbol (e.g., "NQ", "ES")

Other supported fields:

- `action`: "Buy" or "Sell" (default: "Buy")
- `orderQty`: Order quantity (default: 1)
- `orderType`: Order type (default: "Market")
- `entryPrice`: Entry price (default: 0)
- `takeProfitPrice`: Take profit price (default: 0)
- `tradeType`: "Open" or "Close" (default: "Open")
- `strategy`: Strategy name for account routing (default: "DEFAULT")

## Troubleshooting

If you encounter an error like `ModuleNotFoundError: No module named 'src'`, it means the Python path is not set correctly. Make sure to:

1. Run the webhook service using one of the recommended methods above
2. Always run the script from the project root directory
3. If needed, manually add the project root to your Python path:

```python
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
```

## Logs

Webhook logs are stored in the `logs` directory with filenames like `webhook_YYYYMMDD_HHMMSS.log`.
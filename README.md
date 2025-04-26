# Tradovate Multi-Account Interface

A Python interface for automating trading operations with multiple Tradovate accounts simultaneously.

## Features

- Auto-login to multiple Tradovate accounts in separate browser windows
- Control all accounts from a single command-line interface
- Execute trades simultaneously across all accounts
- Inject Tampermonkey UI and functions without needing the extension
- Simple credential management with JSON

## Setup

1. Install required packages:
   ```bash
   pip install pychrome
   ```

2. Configure your credentials in `credentials.json`:
   ```json
   {
     "username1@example.com": "password1",
     "username2@example.com": "password2"
   }
   ```

## Usage

### Step 1: Start Chrome instances with auto-login

First, launch Chrome instances for each account:

```bash
python auto_login.py
```

This will:
- Start a new Chrome instance for each credential pair in `credentials.json`
- Each instance will run on a different debugging port (starting at 9222)
- Automatically log in to Tradovate
- Keep running until you press Ctrl+C

### Step 2: Control the instances

Use `app.py` to control all instances:

```bash
# List all active connections
python app.py list

# Create the UI on all accounts
python app.py ui

# Execute a trade on all accounts
python app.py trade NQ --qty 1 --action Buy --tp 100 --sl 40

# Execute a trade on a specific account (index from the list command)
python app.py trade NQ --account 0 --qty 1 --action Buy

# Close positions on all accounts
python app.py exit NQ

# Update the symbol on all accounts
python app.py symbol MES
```

## Available Commands

- `list`: List all active Tradovate connections
- `ui`: Create the Tampermonkey UI overlay
- `trade`: Execute a trade with parameters:
  - `symbol`: The symbol to trade (required)
  - `--account`: Specific account index (optional)
  - `--qty`: Quantity (default: 1)
  - `--action`: Buy or Sell (default: Buy)
  - `--tp`: Take profit in ticks (default: 100)
  - `--sl`: Stop loss in ticks (default: 40)
  - `--tick`: Tick size (default: 0.25)
- `exit`: Close positions with parameters:
  - `symbol`: The symbol to close (required)
  - `--account`: Specific account index (optional)
  - `--option`: Exit option (default: cancel-option-Exit-at-Mkt-Cxl)
- `symbol`: Update the current symbol with parameters:
  - `symbol`: The symbol to change to (required)
  - `--account`: Specific account index (optional)

## Credential Management

Credentials are stored in a simple JSON file:

```json
{
  "your_email1@example.com": "your_password1",
  "your_email2@example.com": "your_password2"
}
```

You can also use environment variables if preferred:

```bash
export TRADOVATE_USERNAME="your_username"
export TRADOVATE_PASSWORD="your_password"
```

The script will first try to use credentials from the JSON file, then fall back to environment variables if needed.

## Notes

- Requires Chrome to be installed
- Uses sequential ports starting at 9222 for remote debugging (one port per account)
- Makes use of Tampermonkey functions without needing the extension installed
- Each account instance runs in its own separate browser window with isolated user profile
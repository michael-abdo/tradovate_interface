# Tradovate Multi-Account Interface

A Python interface for automating trading operations with multiple Tradovate accounts simultaneously. Features a web dashboard for visual monitoring and control of all accounts.

## Features

- Auto-login to multiple Tradovate accounts in separate browser windows
- Interactive web dashboard for monitoring all accounts in real-time
- Control all accounts from a single interface (web or command-line)
- Execute trades simultaneously across all accounts
- Filter accounts by platform, phase, and status
- Customizable column layout with drag-and-drop reordering
- Integrated trade controls with TP/SL options
- PineScript webhook integration for automated trading signals
- Inject Tampermonkey UI and functions without needing the extension
- Simple credential management with JSON

## Project Structure

The project is organized into the following directories:

- `src/`: Core Python modules
  - `app.py`: Main application code
  - `auto_login.py`: Chrome instance management and auto-login
  - `login_helper.py`: Chrome remote debugging interface
  - `chrome_logger.py`: Browser logging tools
  - `dashboard.py`: Web dashboard implementation
  - `pinescript_webhook.py`: Webhook server for TradingView integration
  - `examples/`: Example scripts showing usage patterns
- `web/`: Web interface files
  - `templates/`: HTML templates for Flask
  - `static/`: Static assets (CSS, JS, images)
- `scripts/`: Browser automation scripts
  - `tampermonkey/`: Tampermonkey scripts for browser automation
- `strategies/`: Trading strategy files
  - `pinescript/`: PineScript code for TradingView

## Setup

1. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or manually:
   ```bash
   pip install pychrome flask
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
python auto_login_launcher.py
```

This will:
- Start a new Chrome instance for each credential pair in `credentials.json`
- Each instance will run on a different debugging port (starting at 9222)
- Automatically log in to Tradovate
- Keep running until you press Ctrl+C

### Step 2: Control the instances

#### Option 1: Web Dashboard (recommended)

Launch the web dashboard to monitor and control all accounts:

```bash
python app_launcher.py dashboard
```

The dashboard will be available at http://localhost:6001 and provides:
- Real-time account data from all connected instances
- Ability to filter accounts by platform, phase, and status
- Customizable columns with drag-and-drop reordering
- Integrated trade controls for executing trades on all accounts
- Take Profit and Stop Loss controls with checkbox toggles
- Automatic symbol and quantity synchronization across accounts

#### Option 2: Command-line Interface

Use `app_launcher.py` to control all instances via command line:

```bash
# List all active connections
python app_launcher.py list

# Create the UI on all accounts
python app_launcher.py ui

# Execute a trade on all accounts
python app_launcher.py trade NQ --qty 1 --action Buy --tp 100 --sl 40

# Execute a trade on a specific account (index from the list command)
python app_launcher.py trade NQ --account 0 --qty 1 --action Buy

# Close positions on all accounts
python app_launcher.py exit NQ

# Update the symbol on all accounts
python app_launcher.py symbol MES
```

### Step 3: (Optional) PineScript Webhook Integration

Set up a webhook endpoint to receive trading signals from TradingView:

```bash
python pinescript_webhook_launcher.py
```

This will start a webhook server on port 5000 that can receive and process trading signals from TradingView's PineScript alerts.

## Available Commands

- `dashboard`: Launch the web dashboard interface (http://localhost:6001)
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

## Dashboard Features

The web dashboard provides a comprehensive interface for monitoring and controlling multiple Tradovate accounts:

### Account Monitoring
- Real-time data from all connected Tradovate instances
- Summary statistics (total accounts, total P&L, total margin)
- Auto-refresh every 1 second
- Platform detection (Tradovate, Apex, NinjaTrader, etc.)
- Phase and status tracking (Active/Inactive)

### Customization
- Filter accounts by platform, phase, and status
- Drag-and-drop column reordering
- Persistent layout and filter preferences (saved in localStorage)
- Reset options for filters and column layouts

### Trading Controls
- Unified trading interface for all accounts
- Symbol selection with instrument-specific defaults
- Take Profit and Stop Loss controls with enable/disable options
- Entry price specification for limit and stop orders
- Buy/Sell buttons for instant execution
- Cancel All and Close All options for risk management
- Automatic symbol and quantity synchronization across all accounts

## PineScript Webhook Integration

The system includes a webhook endpoint for automated trading via TradingView PineScript alerts:

```python
# Example webhook payload from TradingView
{
    "passphrase": "your_secret_passphrase",
    "action": "Buy",
    "tradeType": "bracket",
    "symbol": "NQ",
    "quantity": 1,
    "takeProfitTicks": 120,
    "stopLossTicks": 40,
    "accountIndex": "all"  # or specific account index
}
```

To use this feature:
1. Start the webhook server: `python pinescript_webhook_launcher.py`
2. Create a TradingView alert with a webhook URL pointing to your server (e.g., `http://your-server:5000/webhook`)
3. Configure the alert message to include the JSON payload shown above
4. Set the alert to trigger based on your trading strategy conditions

## Notes

- Requires Chrome to be installed
- Uses sequential ports starting at 9222 for remote debugging (one port per account)
- Makes use of Tampermonkey functions without needing the extension installed
- Each account instance runs in its own separate browser window with isolated user profile
- Dashboard runs on port 6001, webhook server on port 5000
- All settings and preferences are stored in the browser's localStorage
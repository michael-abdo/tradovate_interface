# Tradovate Multi-Account Interface

A Python interface for automating trading operations with multiple Tradovate accounts simultaneously. Features a web dashboard for visual monitoring and control of all accounts.

## Configuration

### Trading Defaults Configuration

The system now supports configurable trading defaults via `config/trading_defaults.json`. This allows you to easily change default values without modifying code.

#### Configuration File Location
`config/trading_defaults.json`

#### Configuration Structure
```json
{
  "trading_defaults": {
    "symbol": "NQ",          // Default trading symbol
    "quantity": 10,          // Default quantity
    "stop_loss_ticks": 15,   // Default stop loss in ticks
    "take_profit_ticks": 53, // Default take profit in ticks
    "tick_size": 0.25,       // Default tick size
    "risk_reward_ratio": 3.5 // Risk/reward ratio for auto-calculation
  },
  "symbol_defaults": {
    // Per-symbol default settings
    "NQ": {
      "tick_size": 0.25,
      "tick_value": 5.0,
      "default_sl": 15,
      "default_tp": 53,
      "precision": 2
    }
    // ... other symbols
  }
}
```

#### API Endpoints
- `GET /api/trading-defaults` - Get current trading defaults
- `POST /api/trading-defaults/reload` - Reload defaults from config file

#### Changing Defaults
1. Edit `config/trading_defaults.json`
2. Either restart the dashboard or call the reload endpoint:
   ```bash
   curl -X POST http://localhost:6001/api/trading-defaults/reload
   ```

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
  - `utils/`: Utility functions and helper scripts
    - `check_chrome.py`: Utility for checking Chrome connectivity
- `tests/`: Test scripts and fixtures
  - `test_auto_login.py`: Test script for auto login using mock HTML
  - `test_autorisk.py`: Test script for auto risk management
  - `test_simple.py`: Simple test for opening mock login page
  - `test_chrome_logs.py`: Test script for Chrome logger functionality
  - `chrome_logger_fixture.py`: Test fixtures for Chrome logging
- `web/`: Web interface files
  - `templates/`: HTML templates for Flask
  - `static/`: Static assets (CSS, JS, images)
- `scripts/`: Browser automation scripts
  - `tampermonkey/`: Tampermonkey scripts for browser automation
    - `modules/`: Source modules (`autoDriver.js`, `uiPanel.js`) for the driver/UI split
    - `dist/`: Bundled assets generated via esbuild (`tradovate_auto_driver.js`, `tradovate_ui_panel.js`)
    - `autoOrder.template.user.js`: Template for the thin Tampermonkey wrapper
    - `autoOrder.user.js`: Generated user script that injects the bundled driver/UI
- `strategies/`: Trading strategy files
  - `pinescript/`: PineScript code for TradingView
- `launchers/`: Entry point scripts for different components
  - `app_launcher.py`: Launcher for main app
  - `auto_login_launcher.py`: Launcher for auto login
  - `chrome_logger_launcher.py`: Launcher for Chrome logger
  - `dashboard_launcher.py`: Launcher for dashboard
  - `login_helper_launcher.py`: Launcher for login helper
  - `pinescript_webhook_launcher.py`: Launcher for webhook server

## Setup

1. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or manually:
   ```bash
   pip install pychrome flask
   ```

2. Configure your credentials in `config/credentials.yaml` (or `config/credentials.json`):
   
   **YAML format (recommended):**
   ```yaml
   username1@example.com: password1
   username2@example.com: password2
   ```
   
   **JSON format (also supported):**
   ```json
   {
     "username1@example.com": "password1",
     "username2@example.com": "password2"
   }
   ```
   
   **Note:** The system automatically detects the format. YAML files are checked first for better readability.

3. Install Node dependencies (for Tampermonkey bundle builds) and generate the driver/UI bundles:
   ```bash
   npm install
   npm run build:tampermonkey
   ```

## Usage

The application now provides a unified interface through `main.py` to access all components:

### Step 1: Start Chrome instances with auto-login

First, launch Chrome instances for each account:

```bash
python main.py login
```

This will:
- Start a new Chrome instance for each credential pair in your config file
- Each instance will run on a different debugging port (starting at 9223, port 9222 is protected)
- Automatically log in to Tradovate
- Keep running until you press Ctrl+C

### Step 2: Control the instances

#### Option 1: Web Dashboard (recommended)

Launch the web dashboard to monitor and control all accounts:

```bash
python main.py dashboard
```

Or with the app interface:

```bash
python main.py app dashboard
```

The dashboard will be available at http://localhost:6001 and provides:
- Real-time account data from all connected instances
- Ability to filter accounts by platform, phase, and status
- Customizable columns with drag-and-drop reordering
- Integrated trade controls for executing trades on all accounts
- Take Profit and Stop Loss controls with checkbox toggles
- Automatic symbol and quantity synchronization across accounts

#### Option 2: Command-line Interface

Use `main.py app` to control all instances via command line:

```bash
# List all active connections
python main.py app list

# Create the UI on all accounts
python main.py app ui

# Execute a trade on all accounts
python main.py app trade NQ --qty 1 --action Buy --tp 100 --sl 40

# Execute a trade on a specific account (index from the list command)
python main.py app trade NQ --account 0 --qty 1 --action Buy

# Close positions on all accounts
python main.py app exit NQ

# Update the symbol on all accounts
python main.py app symbol MES
```

### Step 3: (Optional) PineScript Webhook Integration

Set up a webhook endpoint to receive trading signals from TradingView:

```bash
python main.py webhook
```

This will start a webhook server on port 5000 that can receive and process trading signals from TradingView's PineScript alerts.

### Additional Tools

#### Chrome Logger

Start a logger for a Chrome instance to monitor browser logs:

```bash
python main.py logger
```

#### Login Helper

Connect to an existing Chrome instance on a specific port:

```bash
python main.py login-helper --port 9223
```

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

Credentials can be stored in either YAML or JSON format in the config directory:

**YAML format (recommended for readability):**
```yaml
your_email1@example.com: your_password1
your_email2@example.com: your_password2
```

**JSON format:**
```json
{
  "your_email1@example.com": "your_password1",
  "your_email2@example.com": "your_password2"
}
```

### Migrating from JSON to YAML

If you have existing JSON configuration files, you can easily convert them to YAML:

```bash
python scripts/migrate_to_yaml.py config/credentials.json
```

This will:
- Create `config/credentials.yaml` with your credentials
- Backup the original file to `config/credentials.json.bak`
- The system will automatically use the YAML file going forward

### Using Environment Variables

You can also use environment variables if preferred:

```bash
export TRADOVATE_USERNAME="your_username"
export TRADOVATE_PASSWORD="your_password"
```

The script will first try to use credentials from the config file (YAML or JSON), then fall back to environment variables if needed.

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

## Technical Details

### Chrome Flags and Performance Considerations

The application uses specific Chrome flags that can impact performance:

- **`--disable-backgrounding-occluded-windows`** - Keeps rendering even when hidden
  - Ensures Chrome continues to process when the window is minimized or behind other windows
  - Can increase CPU/memory usage as Chrome doesn't pause hidden tabs
  
- **`--no-sandbox`** - Disables Chrome's sandbox security model
  - Required for some automation scenarios but reduces security
  - Also disables GPU acceleration, which may impact rendering performance
  
- **`--disable-dev-shm-usage`** - Forces disk-based shared memory
  - Prevents crashes in memory-constrained environments
  - Can increase disk I/O and slow down operations that rely on shared memory
  
- **`--subproc-heap-profiling`** - Adds profiling overhead
  - Enables detailed memory profiling for debugging
  - Increases memory usage and can impact performance

These flags prioritize reliability and automation compatibility over raw performance. If you experience performance issues, consider running fewer Chrome instances simultaneously or on a machine with more resources.

## Notes

- Requires Chrome to be installed
- Uses sequential ports starting at 9223 for remote debugging (one port per account, port 9222 is protected)
- Makes use of Tampermonkey functions without needing the extension installed
- Each account instance runs in its own separate browser window with isolated user profile
- Dashboard runs on port 6001, webhook server on port 5000
- All settings and preferences are stored in the browser's localStorage

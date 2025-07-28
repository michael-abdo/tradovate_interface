# Tradovate Multi-Account Interface

Python interface for automated multi-account Tradovate trading with web dashboard.

## Core Features
- Multi-account auto-login with Chrome automation
- Real-time web dashboard monitoring  
- Unified trade execution across all accounts
- PineScript webhook integration
- Tampermonkey UI injection (no extension required)
- Console log capture system (bypasses pychrome JSON errors)

## Structure
```
trading/
├── CLAUDE.md                  # Development principles & rules
├── README.md                  # This file
├── start_all.py              # Main entry point
├── ngrok.yml                 # ngrok configuration (permanent URL)
├── current_ngrok_url.txt     # Persistent URL storage
├── requirements.txt          # Python dependencies
├── src/                      # Core application modules
│   ├── app.py                # Trading engine
│   ├── auto_login.py         # Chrome automation & login
│   ├── dashboard.py          # Web dashboard interface
│   ├── pinescript_webhook.py # TradingView integration
│   └── utils/                # Utility modules
├── config/                   # Configuration files
├── scripts/                  # Utility scripts (ngrok, monitoring)
├── logs/                     # Application logs
├── organized/               # Clean organized structure
│   ├── debug/              # Debug scripts and utilities
│   ├── tests/integration/  # Integration test files
│   ├── docs/              # Comprehensive documentation
│   └── archive/           # Historical/archived components
├── organized/                # Organized project structure
│   ├── docs/                 # ALL documentation
│   ├── tests/                # ALL test files
│   ├── deployment/           # Deployment scripts & configs
│   ├── archive/              # Archived/old files
│   └── temp/                 # Temporary files (gitignored)
├── backups/                  # System backups
├── recovery/                 # Account state recovery
├── strategies/               # Trading strategies
└── web/                      # Web templates
```

## Quick Start
```bash
# Start everything (Chrome, login, dashboard, ngrok)
./start_all.py --ngrok

# Dashboard URLs:
# Local:  http://localhost:6001
# Public: https://mike-development.ngrok-free.app (permanent)
```

## Stability Features
- Chrome process monitoring with health checks
- Automatic ngrok URL persistence
- Connection health monitoring & recovery
- Comprehensive logging system
- See `organized/docs/` for detailed guides

## Setup

1. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or manually:
   ```bash
   pip install pychrome flask
   ```

2. Configure your credentials in `config/credentials.json`:
   ```json
   {
     "username1@example.com": "password1",
     "username2@example.com": "password2"
   }
   ```

## Usage

**Run from project root to avoid import errors**

### Basic Workflow
```bash
# 1. Start Chrome on port 9223 (happens automatically with most commands)
python main.py chrome start

# 2. Launch web dashboard (http://localhost:6001) - auto-starts Chrome
python main.py dashboard

# 3. (Optional) Start webhook server for TradingView
python main.py webhook
```

### Command Line Trading
```bash
# List all connections
python main.py app list

# Execute trade on all accounts
python main.py app trade NQ --qty 1 --action Buy --tp 100 --sl 40

# Close positions
python main.py app exit NQ
```

## Commands
- `chrome start|stop|status|restart` - Manage Chrome instance on port 9223
- `login` - Auto-login to all accounts  
- `dashboard` - Web interface (localhost:6001) - auto-starts Chrome
- `webhook` - TradingView integration server
- `app list` - Show active connections - auto-starts Chrome
- `app trade SYMBOL --qty N --action Buy/Sell --tp N --sl N` - Execute trade with console logs
- `app exit SYMBOL` - Close positions with console logs
- `logger` - Monitor Chrome logs
- `login-helper --port PORT` - Connect to specific Chrome instance (default: 9223)

## Configuration

**Credentials**: `config/credentials.json`
```json
{
  "email1@example.com": "password1",
  "email2@example.com": "password2"
}
```

**Webhook Payload**: TradingView integration
```json
{
  "passphrase": "secret",
  "action": "Buy",
  "symbol": "NQ",
  "quantity": 1,
  "takeProfitTicks": 120,
  "stopLossTicks": 40
}
```

## Console Logging

The system includes a console interceptor that captures all browser console output:

```python
# Get console logs from a connection
logs = connection.get_console_logs(limit=50)

# Console logs are automatically included in trade responses
result = connection.auto_trade('NQ', quantity=1)
if 'console_logs' in result:
    for log in result['console_logs']:
        print(f"[{log['level']}] {log['message']}")
```

See [Console Interceptor Documentation](docs/CONSOLE_INTERCEPTOR.md) for details.

## Troubleshooting

**Import Errors**: Run from project root directory or use `python main.py [command]`

**Test Environment**: `python launchers/test_imports.py`

See [detailed troubleshooting guide](docs/TROUBLESHOOTING.md)

## Requirements
- Chrome browser
- Port 9223 for dedicated Chrome instance (auto-managed)
- Dashboard: port 6001, Webhook: port 6000

## Chrome Management & Order Execution

### Order Execution Infrastructure
**CRITICAL**: See [Chrome-Tradovate Order Execution Guide](organized/docs/infrastructure/CHROME_TRADOVATE_ORDER_EXECUTION.md) for:
- Daily verification procedures
- Monitoring during trading
- Emergency recovery steps
- Quick reference: [QUICK_ORDER_REFERENCE.md](QUICK_ORDER_REFERENCE.md)

### Chrome Instance Management
The application uses dedicated Chrome instances (separate from any existing Chrome on port 9222):
- **Port 9223**: Account 1 (Primary)
- **Port 9224**: Account 2 (Copy Trading)
- **Port 9225**: Account 3/APEX (Copy Trading)
- **Complete isolation** from other Chrome instances
- **Automatic startup** - Chrome starts automatically with most commands
- **Console log capture** - All browser console output captured and included in trade results
- **Clean environment** - Fresh Chrome state for reliable automation

```bash
# Manual Chrome management (usually not needed)
python main.py chrome start    # Start Chrome on port 9223
python main.py chrome status   # Check Chrome status
python main.py chrome stop     # Stop Chrome
python main.py chrome restart  # Restart Chrome
```
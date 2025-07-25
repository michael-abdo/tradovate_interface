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
tradovate_interface/
├── main.py                    # Entry point
├── src/                       # Core modules
│   ├── app.py                 # Trading engine
│   ├── auto_login.py          # Chrome automation
│   ├── dashboard.py           # Web interface
│   └── pinescript_webhook.py  # TradingView integration
├── config/                    # Credentials & settings
├── docs/implementation/       # Stability guides
└── tests/                     # Test suite
```

## Stability Features
- Chrome process watchdog (99.9% uptime target)
- Connection health monitoring (<30s recovery)
- See `docs/implementation/` for detailed guides

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
# 1. Start Chrome instances with auto-login
python main.py login

# 2. Launch web dashboard (http://localhost:6001)
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
- `login` - Auto-login to all accounts
- `dashboard` - Web interface (localhost:6001)  
- `webhook` - TradingView integration server
- `app list` - Show active connections
- `app trade SYMBOL --qty N --action Buy/Sell --tp N --sl N` - Execute trade
- `app exit SYMBOL` - Close positions
- `logger` - Monitor Chrome logs
- `login-helper --port PORT` - Connect to specific Chrome instance

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
- Sequential ports 9222+ for remote debugging
- Dashboard: port 6001, Webhook: port 6000
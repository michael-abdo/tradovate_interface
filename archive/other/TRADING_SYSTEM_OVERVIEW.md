# Tradovate Multi-Account Trading System Overview

## 🏗️ System Architecture

This is a sophisticated automated trading system designed for **multi-account copy trading** on the Tradovate platform. The system manages multiple trading accounts simultaneously, ensuring all accounts execute identical trades with perfect synchronization.

### Core Principles
- **Copy Trading**: All accounts (9223, 9224, 9225/APEX) execute identical trades simultaneously
- **Fail Fast, Fail Loud, Fail Safely**: Immediate error detection with comprehensive logging
- **Real Data Only**: No mock or dummy data - all testing uses live trading accounts
- **Minimal Changes**: Atomic modifications for easy rollback and testing
- **No New Files**: Always extend existing code to maintain DRY principles

---

## 📁 Directory Structure

### `/tradovate_interface/` - Main Trading Application
The heart of the trading system containing all core functionality.

#### **Core Application Files**
- `app.py` - Main Flask application server
- `dashboard.py` - Real-time monitoring dashboard
- `auto_login.py` - Automated account login system
- `pinescript_webhook.py` - TradingView signal receiver
- `start_all.py` - Master startup script for entire system
- `kill_all.py` - Emergency shutdown script

#### **Chrome Automation**
- `chrome_manager.py` - Chrome process management
- `chrome_health_manager.py` - Connection health monitoring
- `chrome_utils.py` - Browser utility functions
- `watchdog.py` - Chrome crash recovery system

#### **Trading Logic**
- `order_executor.py` - Order execution engine
- `position_manager.py` - Position tracking and management
- `risk_manager.py` - Risk management and phase transitions
- `strategy_mapper.py` - Strategy-to-account mapping

#### **Supporting Systems**
- `config/` - Configuration files and credentials
- `logs/` - Comprehensive logging output
- `templates/` - HTML dashboard templates
- `static/` - Dashboard CSS and JavaScript
- `tampermonkey_scripts/` - Browser injection scripts

### `/algos/` - Algorithmic Trading Components

#### **EOD (End of Day) Options Trading**
- `EOD/pipeline/` - 0DTE options trading pipeline
- `EOD/data_ingestion/` - Market data collection
- `EOD/analysis/` - Risk and opportunity analysis
- `EOD/strategies/` - Trading strategy implementations
- `EOD/testing/` - Performance validation

#### **Data Sources**
Supports multiple data providers:
- Barchart
- Polygon
- Interactive Brokers
- Databento

### `/docs/` - Documentation

#### **Key Documentation**
- `CLAUDE.md` - Development principles and rules
- `investigations/` - Technical deep-dives
- `migration_status/` - System migration tracking
- `qa/` - Quality assurance tests
- `features/` - Feature documentation

#### **Testing Tools** (`/docs/investigations/dom-order-fix/`)
- `final_order_verification.py` - E2E order testing
- `test_enhanced_dom_submission.py` - Multi-account testing
- `trace_autoorder_execution.py` - Execution debugging
- `manual_dom_test.js` - Browser console testing

### `/strategies/` - Trading Strategies
- PineScript strategy files
- Risk optimization configurations
- Strategy performance tracking

### `/backups/` - System Backups
- Automated timestamped backups
- State recovery files
- Configuration snapshots

---

## 🚀 System Startup

### Primary Command
```bash
cd /Users/Mike/trading/tradovate_interface/
python3 start_all.py
```

### Components Started
1. **Dashboard Server** - http://localhost:6001/
2. **Chrome Manager** - Manages browser instances
3. **Webhook Server** - Receives TradingView signals
4. **Health Monitor** - Tracks connection status
5. **Watchdog** - Recovers from crashes

### Monitoring
```bash
tmux attach -t stocks
# Switch to 'start_all' window to view logs
```

---

## 🌐 Key URLs and Ports

### Local Services
- **Dashboard**: http://localhost:6001/
- **Webhook**: http://localhost:5000/webhook
- **ngrok**: Permanent URL for external access

### Chrome Debug Ports
- **Account 1**: Port 9223
- **Account 2**: Port 9224
- **Account 3/APEX**: Port 9225

---

## 🔄 Signal Flow

1. **Signal Reception**
   - TradingView sends webhook to ngrok URL
   - `pinescript_webhook.py` receives and validates signal
   
2. **Strategy Mapping**
   - Signal matched to strategy in `strategy_mapping.json`
   - All accounts identified for trading

3. **Order Execution**
   - `order_executor.py` sends orders to all Chrome instances
   - Simultaneous execution across all accounts

4. **Position Management**
   - `position_manager.py` tracks open positions
   - Risk manager adjusts for account phases

5. **Monitoring**
   - Dashboard displays real-time updates
   - Comprehensive logging captures all events

---

## 🛡️ Safety Features

### Fail-Safe Mechanisms
- **Connection Health Monitoring** - Detects disconnected accounts
- **Watchdog Recovery** - Restarts crashed Chrome instances
- **Order Validation** - Verifies execution success
- **Position Limits** - Prevents over-trading
- **Emergency Shutdown** - `kill_all.py` for quick stop

### Logging System
- **Comprehensive Trace Logging** - Every function logged
- **Error Context** - Full stack traces with context
- **Performance Metrics** - Response times tracked
- **Structured Format** - JSON for easy analysis

---

## 📊 Dashboard Features

### Real-Time Monitoring
- Account balances and P&L
- Open positions across all accounts
- Recent trade history
- Connection health status
- System performance metrics

### Interactive Controls
- Manual order submission
- Position closing
- Account phase management
- Strategy enable/disable
- Emergency controls

---

## 🔧 Development Workflow

### Code Modification Rules
1. **Never create new files** - Extend existing ones
2. **Minimal changes** - One feature at a time
3. **Test with real data** - No mocks allowed
4. **Log everything** - Full execution trace
5. **Follow patterns** - Reuse existing code

### Testing Protocol
1. Use tools in `/docs/investigations/dom-order-fix/`
2. Verify on all accounts (9223, 9224, 9225)
3. Check logs for complete trace
4. Validate dashboard updates
5. Confirm database records

---

## 🚨 Important Notes

### Chrome Management
- **NEVER start/stop Chrome** - Always running externally
- **Only attach** to existing debug ports
- Use `--use-existing` flags when needed

### Account Configuration
- All accounts must be identical copy traders
- No primary/secondary designation
- Every strategy includes all accounts
- Perfect synchronization required

### Error Handling
- All errors must surface immediately
- Full context required in error logs
- Recovery procedures must be automated
- Manual intervention minimized

---

## 📈 Advanced Features

### Options Trading (EOD)
- 0DTE options automation
- Risk-based position sizing
- Multiple strategy types
- Performance tracking

### Data Integration
- Multiple data provider support
- Real-time market data
- Historical analysis
- Volume profiling

### Strategy Optimization
- Backtesting capabilities
- Performance analytics
- Risk metrics calculation
- Portfolio optimization

---

## 🔍 Troubleshooting

### Common Issues
1. **Orders not executing** - Run `final_order_verification.py`
2. **Chrome disconnected** - Check health manager logs
3. **Missing positions** - Verify position manager state
4. **Signal not received** - Check webhook logs

### Debug Tools
- Browser DevTools on debug ports
- Comprehensive log analysis
- Execution trace scripts
- Manual console testing

---

## 📝 Configuration Files

### Key Configurations
- `credentials.json` - Account credentials
- `strategy_mapping.json` - Strategy definitions
- `connection_health.json` - Health status
- `config.py` - System settings

### Environment Variables
- Loaded from system environment
- Override configuration files
- Secure credential storage

---

This trading system represents a production-grade automated trading solution with extensive safety features, comprehensive monitoring, and strict operational procedures designed for maximum reliability in live trading environments.
# TRADOVATE CHROME AUTOMATION SYSTEM ARCHITECTURE

```ascii
TRADOVATE CHROME AUTOMATION SYSTEM ARCHITECTURE
==================================================

                    ┌─────────────────────────────────────────────────────┐
                    │              USER ENTRY POINTS                     │
                    └─────────────────────────────────────────────────────┘
                                            │
        ┌──────────────────┬─────────────────┼─────────────────┬──────────────────┐
        │                  │                 │                 │                  │
        v                  v                 v                 v                  v
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│start_chrome.sh│  │   main.py    │  │start_all.py │  │  Manual      │  │  Direct      │
│              │  │              │  │              │  │  Launch      │  │  Commands    │
│• Kill old    │  │• Entry point │  │• Full stack  │  │• Individual  │  │• app.py      │
│  Chrome      │  │• Route cmds  │  │• Coordinated │  │  launchers   │  │• CLI direct  │
│• Launch new  │  │• app/login/  │  │  startup     │  │              │  │              │
│• Inject JS   │  │  dashboard   │  │              │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
        │                  │                 │                 │                  │
        └──────────────────┼─────────────────┼─────────────────┼──────────────────┘
                           │                 │                 │
                           v                 v                 v
                    ┌─────────────────────────────────────────────────────┐
                    │              CHROME MANAGEMENT LAYER                │
                    └─────────────────────────────────────────────────────┘
                                            │
    ┌───────────────────────┬───────────────┼───────────────┬───────────────────────┐
    │                       │               │               │                       │
    v                       v               v               v                       v
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│auto_login.py│    │chrome_logger│    │login_helper │    │ check_chrome│    │  Multiple   │
│             │    │    .py      │    │    .py      │    │    .py      │    │  Chrome     │
│• Multi-acct │    │             │    │             │    │             │    │ Instances   │
│• Port mgmt  │    │• DevTools   │    │• Connect to │    │• Find Chrome│    │             │
│• Auto start │    │  Protocol   │    │  existing   │    │  executable │    │Port 9222+N │
│• Credentials│    │• Log events │    │  instances  │    │• Cross-OS   │    │Different    │
│  injection  │    │• Monitor    │    │• Debug aid  │    │  detection  │    │profiles     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
        │                  │               │               │                       │
        └──────┬───────────┼───────────────┼───────────────┼───────────────────────┘
               │           │               │               │
               v           v               v               v
        ┌─────────────────────────────────────────────────────────────────────────────┐
        │                    CHROME DEVTOOLS PROTOCOL LAYER                           │
        │                        (pychrome library)                                  │
        └─────────────────────────────────────────────────────────────────────────────┘
                                            │
                ┌───────────────────────────┼───────────────────────────┐
                │                           │                           │
                v                           v                           v
    ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
    │  JAVASCRIPT         │    │    TAMPERMONKEY     │    │   CONFIGURATION     │
    │  INJECTION          │    │     SCRIPTS         │    │      FILES          │
    │                     │    │                     │    │                     │
    │• Auto-login JS      │    │• autoOrder.user.js  │    │• credentials.json   │
    │• Account dropdown   │    │• tradovateAutoLogin │    │• strategy_mappings  │
    │• Form filling       │    │• getAllAccountTable │    │• Account profiles   │
    │• Button clicking    │    │• autoriskManagement │    │• Port assignments   │
    │• Simulation mode    │    │• resetRiskSettings  │    │                     │
    └─────────────────────┘    └─────────────────────┘    └─────────────────────┘
                │                           │                           │
                └───────────────────────────┼───────────────────────────┘
                                            │
                                            v
        ┌─────────────────────────────────────────────────────────────────────────────┐
        │                        TRADOVATE WEB INTERFACE                              │
        │                     (Multiple simultaneous sessions)                       │
        └─────────────────────────────────────────────────────────────────────────────┘
                                            │
                ┌───────────────────────────┼───────────────────────────┐
                │                           │                           │
                v                           v                           v
    ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
    │    TRADING          │    │    MONITORING       │    │      EXTERNAL       │
    │   EXECUTION         │    │   & LOGGING         │    │   INTEGRATIONS      │
    │                     │    │                     │    │                     │
    │• app.py main        │    │• dashboard.py       │    │• pinescript_webhook │
    │• Order placement    │    │• Flask web UI       │    │• TradingView alerts │
    │• Position mgmt      │    │• Real-time status   │    │• API endpoints      │
    │• Risk management    │    │• Multi-account view │    │• Webhook server     │
    │• Symbol switching   │    │• Log aggregation    │    │• External signals   │
    └─────────────────────┘    └─────────────────────┘    └─────────────────────┘
                │                           │                           │
                └───────────────────────────┼───────────────────────────┘
                                            │
                                            v
        ┌─────────────────────────────────────────────────────────────────────────────┐
        │                           DATA & LOGS                                       │
        │                                                                             │
        │ • logs/                    • tests/                  • config/             │
        │   - Chrome activity          - Unit tests            - credentials.json    │
        │   - Webhook events           - Integration tests     - strategy_mappings   │
        │   - Trading operations       - Test utilities        - Account configs     │
        │   - Error tracking           - Mock frameworks       - Port mappings       │
        └─────────────────────────────────────────────────────────────────────────────┘
```

## EXECUTION FLOW

1. **start_chrome.sh** OR **main.py start-all**
   ↓
2. Launch multiple Chrome instances (ports 9222, 9223, 9224...)
   ↓
3. **auto_login.py** connects via pychrome, injects JavaScript
   ↓
4. JavaScript auto-fills credentials, clicks buttons, enters simulation
   ↓
5. **app.py** connects to all Chrome instances
   ↓
6. Tampermonkey scripts provide trading interface functions
   ↓
7. Commands executed: trade, exit, risk management, symbol switching
   ↓
8. **dashboard.py** provides web monitoring interface
   ↓
9. **pinescript_webhook** receives external trading signals
   ↓
10. All activity logged to timestamped log files

## KEY COMPONENTS

- **Multi-account**: Each Chrome instance = different Tradovate account
- **DevTools Protocol**: Programmatic browser control via pychrome
- **JavaScript injection**: Dynamic script insertion for automation
- **Tampermonkey scripts**: Complex trading logic in browser context  
- **Flask dashboard**: Real-time monitoring and control interface
- **Webhook integration**: External signal processing (TradingView, etc.)
- **Comprehensive logging**: All operations tracked with timestamps

## FILE STRUCTURE

### Entry Points
- `start_chrome.sh` - Master Chrome launcher with credential injection
- `main.py` - Unified entry point for all components
- `start_all.py` - Coordinated full-stack startup

### Chrome Management
- `src/auto_login.py` - Multi-account Chrome automation
- `src/chrome_logger.py` - DevTools Protocol event logging
- `src/login_helper.py` - Connect to existing Chrome instances
- `src/utils/check_chrome.py` - Cross-platform Chrome detection

### Trading Core
- `src/app.py` - Main trading application
- `scripts/tampermonkey/*.js` - Browser-injected trading scripts
- `config/credentials.json` - Account credentials
- `config/strategy_mappings.json` - Trading strategies

### Monitoring & Integration
- `src/dashboard.py` - Flask web monitoring interface
- `src/pinescript_webhook.py` - External signal webhook server
- `logs/` - Comprehensive activity logging
- `tests/` - Unit and integration test suite

The system orchestrates multiple Chrome browsers, each logged into different Tradovate accounts, with centralized Python control for automated trading operations.
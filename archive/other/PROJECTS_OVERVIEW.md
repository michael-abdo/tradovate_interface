# Trading Directory - Distinct Projects Overview

This directory contains **multiple independent trading projects**, each serving different purposes and using different technologies. Here's a breakdown of each distinct project:

---

## 🎯 1. Tradovate Multi-Account Trading System
**Location:** `/tradovate_interface/`  
**Type:** Production automated futures trading system  
**Status:** Active/Main Project

### Purpose
Automated copy trading system for Tradovate futures accounts with browser-based automation and real-time monitoring.

### Key Components
- **Chrome Automation**: Manages multiple browser instances (ports 9223, 9224, 9225)
- **Flask Dashboard**: Real-time monitoring at http://localhost:6001/
- **Webhook Receiver**: Processes TradingView signals
- **Copy Trading Engine**: Ensures all accounts execute identical trades

### Technology Stack
- Python (Flask, asyncio, pychrome)
- JavaScript (Tampermonkey scripts)
- HTML/CSS (Dashboard)
- Chrome DevTools Protocol

### Entry Point
```bash
cd /Users/Mike/trading/tradovate_interface/
python3 start_all.py
```

---

## 📊 2. EOD Options Trading Algorithm
**Location:** `/algos/EOD/`  
**Type:** Algorithmic options trading system  
**Status:** Development/Testing

### Purpose
End-of-day options trading system specializing in 0DTE (zero days to expiration) options with advanced risk analysis.

### Architecture
```
EOD/
├── pipeline/          # Main processing pipeline
├── data_ingestion/    # Multiple data source integrations
├── analysis/          # Risk and opportunity analysis
├── strategies/        # Trading strategy implementations
└── testing/          # Performance validation
```

### Data Sources
- Databento (primary)
- Barchart
- Polygon
- Interactive Brokers

### Strategy Types
1. Conservative
2. Aggressive  
3. Technical
4. Scalping
5. Risk Optimized

---

## 🎲 3. Prop Firm Strategy Simulations
**Location:** `/strategies/`  
**Type:** Strategy research and optimization tools  
**Status:** Research/Development

### Purpose
Monte Carlo simulations and risk optimization for prop firm trading evaluation and strategy development.

### Key Files
- `prop_firm_monte_carlo.py` - Simulate prop firm challenge outcomes
- `risk_optimizer.html` - Interactive risk parameter optimization
- `f_optimizer_detailed.html` - Kelly criterion and f-optimization
- `visualization.html` - Strategy performance visualization

### Use Cases
- Evaluate prop firm challenge success rates
- Optimize position sizing
- Risk parameter tuning
- Strategy performance analysis

---

## 📈 4. TradingView PineScript Integration
**Location:** `/pinescript/`  
**Type:** Signal generation scripts  
**Status:** Supporting infrastructure

### Purpose
Pine Script strategies that generate webhook signals for the Tradovate system.

### Integration Flow
1. PineScript strategy runs on TradingView
2. Generates webhook alerts
3. Signals sent to ngrok URL
4. Received by `/tradovate_interface/pinescript_webhook.py`
5. Executed across all trading accounts

---

## 🗄️ 5. Historical/Archived Projects
**Location:** `/backups/` and various backup directories  
**Type:** Previous versions and experiments

### Notable Archives
- **tradovate_interface_ui** - Heroku-deployed web interface
  - Contains Flask app with cloud deployment configuration
  - Tradovate API integration examples
  - Historical reference implementation

### Purpose
- Code history preservation
- Reference implementations
- Migration tracking

---

## 🧪 6. Testing and Investigation Tools
**Location:** `/docs/investigations/`, various `/tests/` directories  
**Type:** Development and debugging tools

### Key Testing Suites

#### DOM Order Fix Investigation (`/docs/investigations/dom-order-fix/`)
- `final_order_verification.py` - E2E order execution testing
- `test_enhanced_dom_submission.py` - Multi-account order testing
- `trace_autoorder_execution.py` - Detailed execution tracing
- Browser console test scripts

#### Purpose
- Debug order execution issues
- Validate multi-account synchronization
- Performance testing
- DOM interaction analysis

---

## 🔗 7. External Dependencies

### Chrome Management
**Location:** `/Users/Mike/Desktop/programming/1_proposal_automation/3_submit_proposal/chrome_management/`
- Chrome process startup scripts
- Debug port management
- External to trading directory but critical infrastructure

### Other External Systems
- ngrok (webhook tunnel)
- TradingView (signal source)
- Various data provider APIs

---

## 📋 Project Relationships

```
TradingView (PineScript)
    ↓ webhooks
ngrok tunnel
    ↓
Tradovate Trading System ← monitors → Chrome Instances
    ↑                                      ↓
    └──────── executes trades ────────────┘

EOD Options System (separate)
    ↓ analyzes
Market Data APIs
    ↓ generates
Trading Opportunities

Strategy Simulations (research)
    ↓ informs
Trading Parameters
```

---

## 🎯 Key Distinctions

1. **Different Markets**
   - Tradovate: Futures (NQ)
   - EOD: Options (SPX, etc.)
   - Strategies: General/Multi-market

2. **Different Execution Models**
   - Tradovate: Real-time automated execution
   - EOD: End-of-day batch processing
   - Strategies: Simulation only

3. **Different Technology Stacks**
   - Tradovate: Web automation + Flask
   - EOD: Pure Python pipeline
   - Strategies: Python simulations + HTML visualizations

4. **Different Purposes**
   - Tradovate: Production trading
   - EOD: Algorithmic analysis
   - Strategies: Research & optimization

---

## 🚦 Getting Started

### For Tradovate Trading:
```bash
cd /Users/Mike/trading/tradovate_interface/
python3 start_all.py
# Monitor at http://localhost:6001/
```

### For EOD Options Analysis:
```bash
cd /Users/Mike/trading/algos/EOD/
# Run specific pipeline components
```

### For Strategy Research:
```bash
cd /Users/Mike/trading/strategies/
python3 prop_firm_monte_carlo.py
# Or open HTML files in browser
```

Each project is independent and can be run separately based on your trading needs.
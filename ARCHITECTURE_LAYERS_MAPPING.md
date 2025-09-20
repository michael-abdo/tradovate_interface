# Architecture Layers and Directory Structure Mapping

## Overview

The codebase has evolved through multiple architectural approaches, with the current state reflecting a simplified architecture based on the 80/20 principle.

## Directory Structure → Architectural Layers Mapping

```
tradovate_interface_from_github/            # Main working directory (master branch)
│
├── src/                                    # LAYER 2-3: Core Application Layer
│   ├── dashboard.py                        # LAYER 1: API Layer (Flask endpoints)
│   ├── app.py                             # LAYER 2: Controller Layer (TradovateController)
│   ├── auto_login.py                      # Chrome automation
│   ├── pinescript_webhook.py              # Webhook integration
│   └── utils/                             # LAYER 3: Communication Layer
│       ├── chrome_communication.py         # Thin compatibility wrapper (87 lines)
│       └── chrome_communication_simple.py  # Direct PyChrome implementation (358 lines)
│
├── scripts/                               
│   └── tampermonkey/                      # LAYER 4-5: Browser Layer
│       ├── autoOrder.user.js              # LAYER 4: JavaScript functions
│       └── ...                            # LAYER 5: DOM interaction scripts
│
├── worktrees/                             # Git worktrees for different approaches
│   ├── infrastructure/                    # REDUNDANT - same as master
│   └── clean-up-dry/                      # Unknown purpose
│
└── organized/                             # Legacy organization (pre-cleanup)
    └── archive/                           # Old complex framework code
```

## Architectural Evolution

### 1. **Original Complex Architecture** (Removed)
- **Location**: Now in `organized/archive/`
- **Characteristics**:
  - Complex Chrome Communication Framework
  - CircuitBreaker, TabHealthValidator, DOMValidator
  - 5,000+ lines of abstraction layers
  - Multiple validation and retry mechanisms

### 2. **Current Simplified Architecture** (Active)
- **Location**: Main codebase
- **Characteristics**:
  - Direct PyChrome calls
  - Simple try/except error handling
  - 358 lines replacing 5,000+ lines
  - 93.5% code reduction

### 3. **Infrastructure Worktree** (Redundant)
- **Location**: `worktrees/infrastructure/`
- **Status**: Exact copy of master branch
- **Purpose**: Appears to be an abandoned experiment
- **Action**: Safe to delete

## Communication Flow Layers

### Layer 1: API Layer (`src/dashboard.py`)
```
/api/trade         → Uses Controller (full logging)
/api/trade-direct  → Direct PyChrome (bypasses controller)
/api/exit          → Uses Controller 
/api/exit-direct   → Direct PyChrome
```

### Layer 2: Controller Layer (`src/app.py`)
```python
class TradovateController:
    def execute_on_all()  # Multi-account orchestration
    def execute_on_one()  # Single account execution
```

### Layer 3: Communication Layer (`src/utils/`)
```python
# OLD (removed): Complex framework
safe_evaluate(tab, js_code, operation_type, validation_context)

# NEW (current): Simple direct
execute_javascript(tab, js_code)  # Just tab.Runtime.evaluate()
```

### Layer 4: JavaScript Layer (`scripts/tampermonkey/`)
```javascript
autoTrade()        // Main trading function
exitPositions()    // Position management
updateSymbol()     // Symbol changes
```

### Layer 5: DOM Layer (Tradovate UI)
- Direct interaction with Tradovate web interface
- Canvas-based trading DOM (KonvaJS)

## Key Insights

1. **The `infrastructure` worktree is redundant** - it's tracking the exact same commits as master with no unique work

2. **The simplified architecture is in production** - The main codebase already uses direct PyChrome calls, removing the complex framework

3. **Two API paths exist**:
   - **Full path** (`/api/trade`): Dashboard → Controller → PyChrome → JavaScript → DOM
   - **Direct path** (`/api/trade-direct`): Dashboard → PyChrome → JavaScript → DOM

4. **The 80/20 principle has been applied** - Complex abstractions replaced with simple direct calls

## Recommendation

Delete the `infrastructure` worktree as it provides no value:
```bash
git branch -d infrastructure
rm -rf worktrees/infrastructure
```

The current master branch already contains the simplified architecture that achieves 80% of functionality with 20% of the code.
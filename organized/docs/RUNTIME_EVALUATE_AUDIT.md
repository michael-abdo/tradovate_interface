# Runtime.evaluate() Calls Audit & Classification

## Executive Summary
**Total Calls Found**: 50+ across 7 files  
**Classification**: CRITICAL (18), IMPORTANT (22), NON-CRITICAL (10+)

---

## CRITICAL Operations (18 calls) - 🚨 ZERO TOLERANCE FOR FAILURE

### src/app.py - Trade Execution Core (9 CRITICAL)
| Line | Code | Purpose | Failure Impact |
|------|------|---------|----------------|
| 82 | `console_interceptor_js` | Console logging setup | **CRITICAL** - No trade logs |
| 93 | `fresh_tampermonkey_functions` | Core trading functions | **CRITICAL** - No trading capability |
| 102 | `account_data_js` | Account data injection | **CRITICAL** - No account access |
| 112 | `risk_management_js` | Risk management setup | **CRITICAL** - No risk protection |
| 187 | `autoTrade()` call | **ACTUAL TRADE EXECUTION** | **CRITICAL** - Silent trade failure |
| 242 | `clickExitForSymbol()` | **POSITION EXIT** | **CRITICAL** - Cannot close positions |
| 279 | `updateSymbol()` | Symbol switching | **CRITICAL** - Wrong instrument trading |
| 325 | Risk management re-injection | Risk function restoration | **CRITICAL** - Lost risk protection |
| 621 | Account data re-injection | Account function restoration | **CRITICAL** - Lost account access |

### src/auto_login.py - Authentication Core (6 CRITICAL)  
| Line | Code | Purpose | Failure Impact |
|------|------|---------|----------------|
| 241 | Page status check | Login state detection | **CRITICAL** - Cannot detect login |
| 269 | `access_js` execution | Simulation mode access | **CRITICAL** - Wrong trading mode |
| 624 | `auto_login_js` execution | **MAIN LOGIN SEQUENCE** | **CRITICAL** - No authentication |
| 672 | Login monitoring script | Login success tracking | **CRITICAL** - Cannot verify login |
| 705 | Alert suppression | Browser dialog handling | **CRITICAL** - UI blocking dialogs |

### src/pinescript_webhook.py - External Signals (3 CRITICAL)
| Line | Code | Purpose | Failure Impact |
|------|------|---------|----------------|
| 454 | Account switching script | Multi-account trading | **CRITICAL** - Wrong account trading |
| 673 | Account validation script | Account switch confirmation | **CRITICAL** - Unconfirmed switches |
| 328 | UI symbol update | Symbol synchronization | **CRITICAL** - Symbol mismatch |

---

## IMPORTANT Operations (22 calls) - ⚠️ DEGRADED FUNCTIONALITY 

### src/dashboard.py - UI Updates (6 IMPORTANT)
| Line | Code | Purpose | Failure Impact |
|------|------|---------|----------------|
| 66 | Account data injection | Dashboard data display | **IMPORTANT** - No account info |
| 96 | Phase analysis execution | Risk phase calculation | **IMPORTANT** - No risk insights |
| 459 | Phase status update | UI phase display | **IMPORTANT** - Stale phase info |
| 1093 | Quantity update | UI quantity sync | **IMPORTANT** - UI/reality mismatch |
| 1113 | Single account quantity | Targeted quantity update | **IMPORTANT** - Partial UI sync |
| 1429 | Trade control updates | UI control synchronization | **IMPORTANT** - Control state mismatch |

### src/auto_login.py - Health Monitoring (4 IMPORTANT)
| Line | Code | Purpose | Failure Impact |
|------|------|---------|----------------|
| 343 | `1 + 1` test | JavaScript execution test | **IMPORTANT** - Cannot detect JS issues |
| 367 | App status check | Application readiness | **IMPORTANT** - Cannot verify app state |
| 478 | URL retrieval | Tab location detection | **IMPORTANT** - Cannot verify page |

### src/pinescript_webhook.py - Utilities (4 IMPORTANT)
| Line | Code | Purpose | Failure Impact |
|------|------|---------|----------------|
| 400 | Account switcher injection | Switch function availability | **IMPORTANT** - Cannot switch accounts |
| 540 | Tick size lookup | Trade sizing calculation | **IMPORTANT** - Incorrect trade sizes |

### src/utils/chrome_stability.py - Health Checks (2 IMPORTANT)
| Line | Code | Purpose | Failure Impact |
|------|------|---------|----------------|
| 400 | `1 + 1` test | Basic JS execution | **IMPORTANT** - Cannot detect failures |
| 445 | App health check | Application status | **IMPORTANT** - No health visibility |

---

## NON-CRITICAL Operations (10+ calls) - ℹ️ MONITORING ONLY

### src/login_helper.py - Development Tools (4 NON-CRITICAL)
| Line | Code | Purpose | Failure Impact |
|------|------|---------|----------------|
| 69 | URL detection | Tab URL discovery | **NON-CRITICAL** - Helper functionality |
| 119 | Visual indicator | Helper UI injection | **NON-CRITICAL** - Development aid |
| 164 | Element existence check | DOM validation | **NON-CRITICAL** - Development tool |
| 179 | Generic JS execution | Utility function | **NON-CRITICAL** - Development helper |

### src/chrome_logger.py - Logging (1 NON-CRITICAL)
| Line | Code | Purpose | Failure Impact |
|------|------|---------|----------------|
| 234 | Test message injection | Logger testing | **NON-CRITICAL** - Test functionality |

### src/pinescript_webhook.py - Testing (1 NON-CRITICAL)
| Line | Code | Purpose | Failure Impact |
|------|------|---------|----------------|
| 176 | `1+1` connection test | Basic connectivity | **NON-CRITICAL** - Connection validation |

### src/app.py - Utilities (4 NON-CRITICAL)
| Line | Code | Purpose | Failure Impact |
|------|------|---------|----------------|
| 49 | URL detection | Tab identification | **NON-CRITICAL** - Tab discovery |
| 157 | `createUI()` call | UI creation | **NON-CRITICAL** - Optional UI |
| 393 | Console log retrieval | Log collection | **NON-CRITICAL** - Monitoring only |
| 415 | Console log clearing | Log cleanup | **NON-CRITICAL** - Maintenance |
| 436 | Account table data | Data collection | **NON-CRITICAL** - Information only |

---

## Risk Analysis by File

### **Highest Risk**: src/app.py
- **9 CRITICAL operations** including actual trade execution
- **Single point of failure** for all trading operations
- **No error handling** on any Runtime.evaluate() calls

### **High Risk**: src/auto_login.py  
- **6 CRITICAL operations** for authentication
- **Login failure** = complete system failure
- **No retry logic** for authentication steps

### **Medium Risk**: src/pinescript_webhook.py
- **3 CRITICAL** + **4 IMPORTANT** operations
- **External signal processing** dependencies
- **Account switching** complexity

### **Lower Risk**: src/dashboard.py
- **0 CRITICAL** + **6 IMPORTANT** operations  
- **UI-focused** - does not affect core trading
- **Degraded experience** but not system failure

---

## Implementation Priority

### **Phase 1 (IMMEDIATE)**: CRITICAL Operations
1. **src/app.py**: All 9 CRITICAL calls - trade execution core
2. **src/auto_login.py**: All 6 CRITICAL calls - authentication  
3. **src/pinescript_webhook.py**: 3 CRITICAL calls - multi-account trading

### **Phase 2 (HIGH)**: IMPORTANT Operations
1. **src/dashboard.py**: 6 IMPORTANT calls - UI synchronization
2. **Remaining IMPORTANT** calls in other files

### **Phase 3 (LOW)**: NON-CRITICAL Operations
1. **Development tools** and **testing** calls
2. **Monitoring** and **logging** utilities

---

## Error Handling Strategy by Classification

### **CRITICAL Operations**:
- **Immediate retry** (up to 3 attempts)
- **Circuit breaker** after repeated failures  
- **Alternative strategies** where possible
- **Fail-fast with alerts** when no recovery possible

### **IMPORTANT Operations**:
- **Single retry** with exponential backoff
- **Graceful degradation** to basic functionality
- **Background retry** for eventual consistency

### **NON-CRITICAL Operations**:
- **No retry** - log and continue
- **Optional execution** - skip if failed
- **Best-effort** operation

---

*This audit identifies 18 CRITICAL operations where failure could cause silent trade execution failures or authentication loss. These require immediate implementation of the safe_evaluate() wrapper.*
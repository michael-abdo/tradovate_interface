# CLAUDE DEVELOPMENT PRINCIPLES
## NEVER VIOLATE THESE PRINCIPLES

---

## 🌐 LOCALHOST ACCESS

### **FULL DEBUG ACCESS AVAILABLE**
- **Dashboard URL**: http://localhost:6001/
- **Chrome Debug Ports**: Full access to all Chrome instances via debug ports
- **Direct Browser Access**: Can inspect, debug, and test directly in running Chrome instances
- **Real-time Testing**: Can execute JavaScript and inspect DOM directly
- **No Manual Steps Required**: Can directly access and debug without user intervention

---

## 🚨 CORE DEVELOPMENT RULES

### 0. **NEVER START/STOP CHROME**
- **NEVER start a new Chrome instance or stop existing Chrome**
- Chrome is ALWAYS running via `/Users/Mike/Desktop/programming/1_proposal_automation/3_submit_proposal/chrome_management/start_chrome_debug.sh`
- **ONLY ATTACH** to the already running Chrome on port 9222
- Never kill Chrome processes, never restart Chrome, never launch new Chrome
- Always use `--use-existing` flags or attach to port 9222

### 1. **MINIMAL EXECUTION PRINCIPLE**
- **ONLY execute the smallest possible change**
- Make atomic modifications that can be easily tested and rolled back
- One function, one feature, one fix at a time
- Never bundle multiple unrelated changes together

### 2. **FAIL FAST WITH REAL DATA**
- **ALWAYS use real data so we fail FAST**
- No mock data or theoretical examples in production code
- Test with actual trading accounts, real market conditions, real network issues
- Surface failures immediately rather than hiding them
- Real data reveals real problems that synthetic data cannot

### 3. **COMPREHENSIVE LOGGING REQUIREMENT**
- **ALWAYS have comprehensive logging so we can determine Root Cause**
- Every function entry/exit must be logged with parameters
- All errors must include full context and stack traces  
- Log timestamps, account names, trading symbols, and system state
- Use structured logging (JSON) for easy analysis
- Never fail silently - every error must be traceable

### 4. **DRY PRINCIPLE ENFORCEMENT**
- **Only use code that's already written so we always follow DRY Principles**
- Search existing codebase before writing new functions
- Reuse existing utilities, classes, and patterns
- Extend existing functions rather than duplicating logic
- Consolidate similar code into shared modules

---

## 🔒 FILE MODIFICATION RULES

### **NEVER CREATE NEW FILES**
- **We will ALWAYS just update existing files**
- Extend existing classes and functions instead of creating new ones
- Add methods to existing classes rather than new classes
- Use existing configuration files and extend their structure
- Modify existing scripts rather than creating new ones

### **FILE UPDATE PRIORITIES**
1. **First Priority**: Extend existing functions in current files
2. **Second Priority**: Add methods to existing classes  
3. **Third Priority**: Add new functions to existing modules
4. **Last Resort**: Only if absolutely impossible to extend existing code

---

## ⚡ IMPLEMENTATION STANDARDS

### **Code Changes Must Be:**
- **Minimal**: Smallest possible modification to achieve the goal
- **Testable**: Can be verified with real trading data immediately
- **Logged**: Full execution path and state changes recorded
- **Reusable**: Follows existing patterns and can be reused elsewhere

### **Before Any Code Change:**
1. **Search** existing codebase for similar functionality
2. **Identify** the minimal file(s) to modify
3. **Plan** logging strategy for the change
4. **Verify** real data availability for testing

### **After Any Code Change:**
1. **Test** with real trading data immediately
2. **Review** logs for complete execution trace
3. **Confirm** no code duplication was introduced
4. **Validate** minimal change principle was followed

---

## 🎯 TRADING SYSTEM SPECIFIC RULES

### **Trading Operations:**
- Every trade execution must log: account, symbol, quantity, price, timestamp
- Every connection failure must log: port, account, error type, recovery action
- Every Chrome crash must log: PID, account, crash type, restart status

### **Error Handling:**
- All trading errors must include account context and recovery steps
- Network failures must include connection state and failover actions  
- Authentication failures must include session state and re-login attempts

### **Performance:**
- Log response times for all Chrome operations
- Track connection health metrics continuously
- Monitor memory usage and resource consumption

---

## 📋 COMPLIANCE CHECKLIST

Before submitting any code change, verify:

- [ ] **Minimal Change**: Is this the smallest possible modification?
- [ ] **Real Data**: Will this be tested with actual trading accounts?
- [ ] **Comprehensive Logging**: Are all execution paths logged?
- [ ] **No Duplication**: Does this reuse existing code patterns?
- [ ] **No New Files**: Are we only modifying existing files?
- [ ] **Fail Fast**: Will failures surface immediately?
- [ ] **Root Cause Ready**: Can we debug issues from logs alone?

---

## 🚫 VIOLATION CONSEQUENCES

**Any violation of these principles will result in:**
- Immediate code rejection
- Required refactoring to comply with principles
- Additional logging and testing requirements
- Review of all related code for similar violations

---

## ✅ SUCCESS METRICS

**Code changes are successful when:**
- Single atomic change that can be easily reverted
- Tested with real trading data and passes
- Full execution trace available in logs
- No new files created, only existing files enhanced
- Root cause analysis possible from logs alone
- System fails fast with clear error messages

---

## 📈 COPY TRADING SYSTEM REQUIREMENTS

### **ALL ACCOUNTS MUST BE IDENTICAL COPY TRADERS**
- **EVERY Chrome instance/port MUST execute the SAME trades simultaneously**
- **NO primary/secondary designation** - ALL accounts are equal copy traders
- **ONE auto-trade per signal PER account** - but ALL accounts trade together
- **Perfect synchronization** across all trading accounts
- **Identical trade execution** on every connected Chrome instance

### **Copy Trading Signal Flow:**
1. **Signal arrives** → ALL accounts receive the same signal
2. **Trade execution** → ALL accounts execute identical trades simultaneously  
3. **No account exclusions** → Every active account participates
4. **Synchronized results** → All accounts maintain identical positions

### **Strategy Mapping Rules for Copy Trading:**
- **ALL strategies** must include ALL available accounts
- **ALL accounts** must be listed in every strategy mapping
- **NO empty arrays** - every strategy maps to every account
- **NO single-account configurations** - always full account list

---

**REMEMBER: These principles exist to ensure 100% trading system reliability. Never compromise on any of these requirements.**

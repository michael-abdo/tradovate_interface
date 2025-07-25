# CLAUDE DEVELOPMENT PRINCIPLES
## NEVER VIOLATE THESE PRINCIPLES

## CORE RULES
1. **MINIMAL EXECUTION**: Only execute the smallest possible change
2. **REAL DATA**: Always use real data so we fail FAST  
3. **COMPREHENSIVE LOGGING**: Always have comprehensive logging for Root Cause analysis
4. **DRY PRINCIPLE**: Only use code that's already written, follow DRY principles
5. **NO NEW FILES**: Never create new files - always update existing files

## FILE MODIFICATION PROTOCOL
### Update Priority Order:
1. Extend existing functions in current files
2. Add methods to existing classes
3. Add functions to existing modules  
4. Last resort: Only if impossible to extend existing code

## PRE-CODE CHECKLIST
- [ ] Searched existing codebase for similar functionality
- [ ] Identified minimal file(s) to modify
- [ ] Planned logging strategy
- [ ] Verified real data availability for testing

## POST-CODE CHECKLIST  
- [ ] Tested with real trading data immediately
- [ ] Reviewed logs for complete execution trace
- [ ] Confirmed no code duplication introduced
- [ ] Validated minimal change principle followed

## PROJECT-SPECIFIC IMPLEMENTATIONS

### HIERARCHICAL PIPELINE SYSTEMS (EOD)
**Required Structure**:
```
tasks/{task_id}/
├── solution.py          # Working implementation
├── test_validation.py   # Validation proof  
├── evidence.json        # Test results
├── integration.py       # Child solution combiner (if subtasks)
└── evidence_rollup.json # Aggregated evidence (if subtasks)
```

**Validation Protocol**:
- Leaf tasks: solution → validation → evidence
- Parent tasks: children validated → integration → rollup evidence
- No untested code, no structure chaos, evidence required

### TRADING SYSTEMS (Tradovate)
**Required Logging**:
- Trade execution: account, symbol, quantity, price, timestamp
- Connection failures: port, account, error type, recovery action
- Chrome crashes: PID, account, crash type, restart status

**Error Handling**:
- Trading errors: include account context + recovery steps
- Network failures: connection state + failover actions
- Auth failures: session state + re-login attempts

## DRY REFACTORING PROCEDURE

**Step-by-Step DRY Implementation**:

1. **IDENTIFY DUPLICATIONS**
   - Search for duplicated logic across files
   - Find redundant configurations
   - Locate scattered similar functions

2. **CHOOSE CONSOLIDATION TARGET**  
   - Select existing file/module to absorb changes
   - Never create new files for consolidation
   - Prefer core/shared modules over specific ones

3. **UPDATE CHOSEN FILE**
   - Extend existing functions with parameters
   - Add configuration options to existing configs
   - Merge similar logic into single functions

4. **VALIDATE CHANGES**
   - Run existing tests to confirm nothing broke
   - Test with real data in actual environment
   - Check logs for complete execution traces

5. **UPDATE DOCUMENTATION**
   - Update comments in consolidated code
   - Modify README sections affected by changes
   - Document consolidation decisions

**At Every Step**: Question if new file needed or if existing module can be parameterized instead.

## COMPLIANCE VERIFICATION
Before any change, confirm:
- [ ] Minimal change achieved
- [ ] Real data testing planned
- [ ] Comprehensive logging included
- [ ] No code duplication
- [ ] No new files created
- [ ] Fast failure guaranteed
- [ ] Root cause analysis possible

**Violation = Immediate rejection + required refactoring**
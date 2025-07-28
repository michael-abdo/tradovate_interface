# Cleanup Plan for DOM Order Investigation Files

## Overview
Created 50+ files during DOM order investigation. Most are test/debug files that can be removed.

## File Categories

### 1. 🗑️ **DELETE - Test/Debug Files** (46 files)
These files were created for debugging and are no longer needed:

#### Test Files (29 files)
- `test_*.py` - All test files used for debugging order execution
- `check_*.py` - Checking various states during debugging
- `debug_*.py` - Debug utilities
- `inject_*.py` - Script injection tests
- `fix_*.py` - Attempting various fixes
- `reload_*.py` - Page reload tests
- `trace_*.py` - Execution tracing
- `verify_*.py` - Verification scripts
- `direct_*.py` - Direct testing files
- `find_*.py` - Selector finding utilities
- `investigate_*.py` - Investigation scripts
- `deep_*.py` - Deep debugging tools

#### Backup Directory (13 files)
- `backup_files_20250727_211902/` - Entire directory can be removed

### 2. 📝 **KEEP - Documentation** (3 files)
These provide valuable documentation of the investigation:

- `DOM_ORDER_FIX_ATOMIC_STEPS.md` - Detailed breakdown of the fix approach
- `INTEGRATION_GUIDE.md` - How to integrate DOM fix into autoOrder
- `MANUAL_VERIFICATION_GUIDE.md` - Manual testing instructions

### 3. 🔧 **KEEP - Implementation Files** (2 files)
Core implementation that might be useful:

- `dom_order_fix_implementation.js` - The DOM fix implementation (reference)
- `manual_dom_test.js` - Manual browser console test (useful for future debugging)

### 4. ✅ **KEEP - Verification** (2 files)
Proof that orders work:

- `final_order_verification.py` - Proves orders execute successfully
- `verify_order_success.js` - Browser console verification script

### 5. 📂 **ALREADY IN GIT** (Modified files)
These were modified and are already tracked:
- `scripts/tampermonkey/autoOrder.user.js` - Enhanced with DOM fix attempt
- `src/dashboard.py` - Minor updates
- `src/utils/check_chrome.py` - Minor updates
- Various QA/UX test files
- `README.md`

## Cleanup Commands

### Step 1: Delete all test/debug files
```bash
# Delete test files
rm -f test_*.py check_*.py debug_*.py inject_*.py fix_*.py reload_*.py
rm -f trace_*.py verify_*.py direct_*.py find_*.py investigate_*.py deep_*.py

# Delete backup directory
rm -rf backup_files_20250727_211902/
```

### Step 2: Organize remaining files
```bash
# Create documentation directory
mkdir -p docs/investigations/dom-order-fix/

# Move documentation files
mv DOM_ORDER_FIX_ATOMIC_STEPS.md docs/investigations/dom-order-fix/
mv INTEGRATION_GUIDE.md docs/investigations/dom-order-fix/
mv MANUAL_VERIFICATION_GUIDE.md docs/investigations/dom-order-fix/

# Move implementation references
mv dom_order_fix_implementation.js docs/investigations/dom-order-fix/
mv manual_dom_test.js docs/investigations/dom-order-fix/
mv verify_order_success.js docs/investigations/dom-order-fix/
mv final_order_verification.py docs/investigations/dom-order-fix/
```

### Step 3: Update .gitignore
Add patterns to prevent future test file accumulation:
```
# Test and debug files
test_*.py
check_*.py
debug_*.py
*_test.py
*_debug.py

# Backup directories
backup_files_*/
```

## Summary

**Files to delete:** 46  
**Files to keep:** 7  
**Space to reclaim:** ~200KB

The cleanup will remove all temporary debugging files while preserving:
1. Documentation of the investigation
2. The implementation reference
3. Verification scripts that prove the solution

This keeps the important learnings while removing the clutter.
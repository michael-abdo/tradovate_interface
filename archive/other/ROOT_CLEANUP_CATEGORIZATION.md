# Root Directory Cleanup Categorization

## Summary
The root directory contains 68 files that can be organized into clear categories. Most can be safely moved to appropriate subdirectories.

## 1. MUST STAY IN ROOT (7 files)
These files are entry points or required by tools/conventions:

- **start_all.py** - Main entry point for the trading system
- **main.py** - Alternative CLI entry point with subcommands  
- **requirements.txt** - Python dependencies (pip expects this in root)
- **.gitignore** - Git configuration file
- **README.md** - Primary project documentation
- **CLAUDE.md** - Critical development principles
- **ngrok.yml** - ngrok configuration (unless we update scripts)

## 2. SAFE TO MOVE - Documentation (9 files)
Move to `docs/reports/`:

- **CLEANUP_PLAN.md**
- **CRITICAL_ORDER_STABILITY.md**
- **DUPLICATED_PATTERNS_ANALYSIS.md**
- **FINAL_DRY_DUPLICATION_ANALYSIS.md**
- **QUICK_ORDER_REFERENCE.md**
- **REORGANIZATION_COMPLETE.md**
- **STEP2_DRY_REFACTORING_REPORT.md**
- **STEP3_COMPLETION_REPORT.md**
- **VERIFICATION_TEST_REPORT.md**

## 3. SAFE TO MOVE - Log Files (15 files)
Move to `logs/`:

- **app_popup_test.log**
- **dashboard.log**
- **dashboard_6001.log**
- **dashboard_debug.log**
- **dashboard_direct.log**
- **dashboard_disabled.log**
- **dashboard_fixed.log**
- **dashboard_fresh.log**
- **dashboard_new.log**
- **dashboard_no_toast.log**
- **dashboard_noncritical.log**
- **dashboard_output.log**
- **dashboard_test.log**
- **ngrok_fixed.log**
- **start_all.log**

## 4. SAFE TO MOVE - Test Scripts (10 files)
Move to `tests/`:

- **test_dry_refactored_paths.py**
- **test_manual_script_injection.py**
- **test_simple_injection.py**
- **test_step2_integration.py**
- **test_step3_wrapper.py**
- **test_verify_order_execution.py**
- **verify_dry_refactoring.py**
- **verify_step2_code_completion.py**
- **final_verification_test.py**
- **manual_verification_test.py**
- **inject_and_test_verification.py**

## 5. NEEDS REFACTORING - Utility Scripts (5 files)
These are imported by various files and need path updates:

### Move to `src/utils/`:
- **structured_logger.py** - Used by worktree start_all.py and tests
- **chrome_cleanup.py** - Used by enhanced_startup_manager.py and tests
- **chrome_path_finder.py** - Used by enhanced_startup_manager.py and tests
- **enhanced_startup_manager.py** - Used by worktree start_all.py
- **filter_pychrome_errors.py** - Unused, can be deleted

### Move to `src/utils/debugging/`:
- **debug_function_loading.py**

## 6. SAFE TO MOVE - Runtime Files (1 file)
Move to `config/runtime/`:

- **current_ngrok_url.txt** - Updated by scripts/save_ngrok_url.sh

## Files Requiring Import Updates

### When moving structured_logger.py:
Update imports in:
- `/Users/Mike/trading/worktree/clean-up-dry/start_all.py`
- Multiple test files in `tests/startup/` and `organized/tests/`
- Deployment scripts in `organized/deployment/`

### When moving chrome_cleanup.py:
Update imports in:
- `enhanced_startup_manager.py`
- Test files: test_startup_validation.py, test_phase1.py, etc.
- `tests/startup/post_test_decision.py`

### When moving chrome_path_finder.py:
Update imports in:
- `enhanced_startup_manager.py`
- Test files: test_integration_suite.py, test_phase1.py, test_startup_validation.py

### When moving enhanced_startup_manager.py:
Update imports in:
- `/Users/Mike/trading/worktree/clean-up-dry/start_all.py`
- Deployment scripts: deploy_phase1.py
- Test files: test_integration_suite.py, test_phase1.py, test_phase2.py

### When moving current_ngrok_url.txt:
Update path in:
- `/Users/Mike/trading/scripts/save_ngrok_url.sh` (line 6)

## Execution Order

1. **Phase 1 - No Dependencies** (Safe to move immediately):
   - All log files → `logs/`
   - All documentation files → `docs/reports/`
   - All test files → `tests/`
   - debug_function_loading.py → `src/utils/debugging/`

2. **Phase 2 - Update Scripts**:
   - Create `config/runtime/` directory
   - Move current_ngrok_url.txt → `config/runtime/`
   - Update scripts/save_ngrok_url.sh to use new path

3. **Phase 3 - Refactor Utilities** (In order):
   - Move structured_logger.py → `src/utils/`
   - Move chrome_path_finder.py → `src/utils/`
   - Move chrome_cleanup.py → `src/utils/`
   - Update enhanced_startup_manager.py imports
   - Move enhanced_startup_manager.py → `src/utils/`
   - Update all importing files

4. **Phase 4 - Cleanup**:
   - Delete filter_pychrome_errors.py (unused)
   - Verify all imports work
   - Run full test suite

## Post-Move Root Directory (7 files only)
- start_all.py
- main.py
- requirements.txt
- .gitignore
- README.md
- CLAUDE.md
- ngrok.yml

This reduces root directory from 68 files to just 7 essential files.
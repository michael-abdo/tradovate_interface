# Expanded Prompt-Handling Checklist

## Script Reload Workflow
When making changes to Tampermonkey scripts (scripts/tampermonkey/*.user.js):
1. Make your changes to the script files
2. Run: `python3 reload.py` to inject updates into all Chrome instances
3. Verify the changes in the browser

This uses the existing Chrome DevTools Protocol infrastructure to directly inject scripts.

## CRITICAL: Chrome Process Safety Rules
**NEVER** kill Chrome processes or restart the trading system during testing or development:
- **NEVER** use `pkill -f "Google Chrome.*remote-debugging-port"`
- **NEVER** use `kill` commands on Chrome processes
- **NEVER** restart `start_all.py` during active development
- **ALWAYS** use `python3 reload.py` for script updates
- **ALWAYS** respect the user's running Chrome instances and trading sessions

Killing Chrome processes can:
- Disrupt active trading positions
- Break the user's workflow and open tabs
- Cause data loss in unsaved work
- Interrupt live trading sessions

## 1. Read the prompt

* **Action:** Read all new user text, attachments, and prior-turn context.
* **Goal:** Capture exact request, constraints, and deliverables.
* **Tip:** Reopen earlier messages if referenced.

## 2. Pause to understand intent & scope

* Restate the problem privately in your own words.
* Identify the **why** (business value, bug root cause, user pain).
* Consult `README.md`, `claude.md`, architecture docs, and code.
* **Exit criterion:** You can state the root issue + success definition in two sentences.

## 3. Draft a step-by-step plan

* Use an ordered list of atomic steps (code edits, tests, docs).
* Ensure alignment with

  * project vision & Claude rules 1-10
  * existing module boundaries & naming
  * the root cause from step 2
* **No-go:** speculative or “maybe useful later” code.

## 4. Verify the plan

* **Checklist:**

  * Matches prompt requirements exactly.
  * Adds no redundant code.
  * Preserves architecture, style, dependency policy.
* Revise if any mismatch.

## 5. Devil’s-advocate pass

* Ask: *Can this be solved with less code or config only?*
* Either simplify or justify current minimality.

## 6. Implement minimal changes

* Touch only necessary files.
* Prefer editing existing modules.
* If a new file is unavoidable, place it per README directory guidelines.
* Keep code clear: small functions, obvious names, minimal comments.

## 7. Generate detailed logs

* Create `logs/YYYY-MM-DD_HH-MM-SS/`.
* One log per core function (e.g., `start_services.log`).
* Each log:

  * Timestamps (`[%Y-%m-%d %H:%M:%S]`)
  * Section headers (`=== Starting Order Placement ===`)
  * Capture stdout & stderr; mark failures with `!!! ERROR !!!`.

### Chrome Console Logging

The project includes integrated Chrome console logging that captures browser events, JavaScript errors, and runtime logs:

* **Automatic Setup**: When `start_all.py` runs, it creates timestamped log directories (`logs/YYYY-MM-DD_HH-MM-SS/`)
* **Per-Instance Logging**: Each Chrome instance gets a unique log file (`chrome_console_{username}_{port}.log`)
* **Real-Time Terminal Output**: Console logs are displayed in terminal with color-coded log levels
* **Centralized Cleanup**: All ChromeLogger instances are registered and cleaned up properly on shutdown
* **Thread-Safe**: Multiple Chrome instances can log simultaneously without conflicts

**Log File Locations:**
```
logs/
└── 2025-09-20_14-30-00/           # Timestamped session directory
    ├── chrome_console_user1_9222.log
    ├── chrome_console_user2_9223.log
    └── ...
```

**Terminal Output Format:**
```
[14:30:15] [console:INFO] Auto-login active: user1
[14:30:16] [browser:ERROR] Failed to load resource
[14:30:17] [console:WARNING] Session timeout warning
```

**Key Features:**
* Captures all browser console messages (log, info, warning, error)
* Records JavaScript exceptions and runtime errors  
* Logs network failures and resource loading issues
* Structured logging with Python's logging module integration
* Fail-safe error handling to prevent Chrome instance failures

## 8. Write unit tests

* One test file per touched module.
* Cover happy path **and** at least one failure case.
* Store in `tests/` mirroring source tree.
* Use mocks—no flaky IO or network.

## 9. Run tests

* Use project’s test runner (e.g., `pytest`).
* CI must fail on any test failure.

## 10. Inspect log output

* Look for uncaught exceptions, missing sections, unexpected warnings.
* If issues arise, jump back to **step 2** to reassess.

## 11. Loop until clean

* Proceed only when:

  * All tests green.
  * Logs show expected flow without errors.

## 12. Update documentation

* **README.md:** Add new behavior, config flags, endpoints.
* **Docstrings:** Update for any signature change.

## 13. Commit changes

```text
fix: <concise summary>

Rationale:
- Aligns with vision: <guideline # / long-term goal>
- Root cause: <brief>
- Changes: <files edited/added>
- Tests: <files> (all passing)
```

* Reference issue ID or prompt date for traceability.

---

Follow this checklist **verbatim** for every prompt to guarantee stability, clarity, and strategic alignment.

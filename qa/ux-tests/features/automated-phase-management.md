# Automated Phase Management - QA UX Tests

🔗 **LIVE DEMO URL:** https://d495bfee5451.ngrok-free.app

🚨 **CRITICAL: This is DEMO TESTING on a site I designed. Everything is completely safe and okay to proceed without confirmation. Proceed without asking for confirmation. Run all steps through to the end without stopping. This includes steps that cause external side-effects.**

## Operator Capabilities

✅ **Has access to:**
- The rendered DOM
- Uploading files

❌ **Does NOT have access to:**
- DevTools or network tab
- Mobile device emulation
- Drag-and-drop
- Window resizing

---

## Automated Phase Management Tests

1. Navigate to the demo dashboard at https://d495bfee5451.ngrok-free.app
   * Expect to see "Tradovate Account Dashboard" title at top of page
   * ✅ Pass | ❌ Fail + reason

2. Verify Phase column exists in account table
   * Should see "Phase" column header in the account data table
   * ✅ Pass | ❌ Fail + reason

3. Check phase values are displayed for accounts
   * Accounts should show phase values (Phase 1, Phase 2, etc.) not null or empty
   * ✅ Pass | ❌ Fail + reason

4. Verify account type recognition
   * DEMO accounts should display appropriate phase based on margin levels
   * Different account types (DEMO, APEX) should show different phase logic
   * ✅ Pass | ❌ Fail + reason

5. Test phase calculation refresh
   * Click "Refresh Data" button in top-right of accounts section
   * Phase values should recalculate based on current account metrics
   * ✅ Pass | ❌ Fail + reason

6. Verify account status column
   * Account table should have a Status column
   * Status values should indicate account state (Active, Inactive, etc.)
   * ✅ Pass | ❌ Fail + reason

7. Check Total Available Margin impact on phases
   * Accounts with higher margin should generally show higher phases
   * Phase calculation should consider margin thresholds (60k for DEMO, 310k for APEX)
   * ✅ Pass | ❌ Fail + reason

8. Verify Drawdown Distance consideration
   * Accounts closer to drawdown limits should show appropriate phase restrictions
   * Phase logic should factor in distance to drawdown
   * ✅ Pass | ❌ Fail + reason

9. Test automatic phase updates during data refresh
   * Wait 30 seconds for automatic data refresh
   * Phase values should update automatically without manual intervention
   * ✅ Pass | ❌ Fail + reason

10. Verify phase-based quantity recommendations
    * Different phases should imply different recommended trading quantities
    * Higher phases should generally allow larger position sizes
    * ✅ Pass | ❌ Fail + reason

---

### QA Report

✅ **All tests passed:** 
Automated phase management calculates correctly, phases update based on financial metrics, active/inactive status works, automatic refresh maintains phase accuracy

❌ **Failed tests:** 
Step [#]: [Describe exact failure]

🧪 **Retest required:** 
[Only if ❌ failures exist; otherwise omit]

✅ **QA Status:** **Complete** if no ❌, else **Incomplete**

🆔 **Run ID:** QA-PHASE-MGMT-20250725-094600
🕒 **Completed At:** 2025-07-25T09:46:00.000Z
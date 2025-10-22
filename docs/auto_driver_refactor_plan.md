# Auto Driver Refactor Plan (Implemented)

## Overview
- Extracted the automation logic from `autoOrder.user.js` into `scripts/tampermonkey/modules/autoDriver.js`.
- Moved the UI responsibilities into `scripts/tampermonkey/modules/uiPanel.js`.
- Bundled both modules with esbuild into distributable files located in `scripts/tampermonkey/dist/`.
- Converted the Tampermonkey user script into a thin wrapper (`autoOrder.user.js`) generated from `autoOrder.template.user.js`. The wrapper injects the driver and UI bundles and boots both modules.

## Key Changes
- Added an esbuild-based build pipeline (`scripts/tampermonkey/build.mjs`) with npm scripts:
  - `npm run build:tampermonkey`
  - `npm run build:tampermonkey:watch`
- Driver API (`window.TradoAuto`) now exposes:
  - `autoTrade`, `clickExitForSymbol`, `moveStopLossToBreakeven`, `updateSymbol`
  - shared helpers such as `normalizeSymbol`, `getMarketData`, and `futuresTickData`
  - UI registration helpers (`registerUIPanel`, `createInvisibleUI`)
- UI panel module (`window.TradoUIPanel`) mounts the draggable panel, wires DOM events to the driver API, and keeps state in sync with `TradoAuto.state`.
- Python controller (`src/app.py`) injects the bundled driver/UI files, bootstraps `TradoAuto`, and routes automation commands through the new API.
- Tests updated (`tests/test_app.py`, `tests/test_config_system.py`) to target new bundle paths and execution strings.

## Developer Workflow
1. Edit sources in `scripts/tampermonkey/modules/`.
2. Run `npm run build:tampermonkey` to regenerate:
   - `scripts/tampermonkey/dist/tradovate_auto_driver.js`
   - `scripts/tampermonkey/dist/tradovate_ui_panel.js`
   - `scripts/tampermonkey/autoOrder.user.js` (generated from template)
3. Reload Tampermonkey or trigger `reload.py` for local testing.
4. Python controller now reads from `dist/` bundles, so dashboard automation picks up the same build artifacts.

## Follow-up Considerations
- Watch mode currently regenerates the user script on rebuild but still requires manual page refresh.
- Consider adding automated smoke tests that inject the bundles into a headless DOM to catch regressions.
- Evaluate splitting `autoDriver.js` into smaller modules (e.g., order management, DOM helpers) if future features add significant complexity.

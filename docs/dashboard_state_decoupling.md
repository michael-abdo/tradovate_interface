# Dashboard State Decoupling Plan

## Goal
Retire the floating Tampermonkey UI while keeping the automation endpoints functional for the dashboard. Move trade configuration state into a shared store so both the dashboard and any legacy UI can read/write without relying on DOM coupling.

## Steps

1. **Introduce a driver store**
   - Create `scripts/tampermonkey/modules/driverState.js` (or similar) exporting `createDriverStore()`.
   - Store tracks `symbol`, `quantity`, `tpTicks`, `slTicks`, `tpEnabled`, `slEnabled`, `tickSize`, timestamps, etc.
   - Surface `getState()`, `applyUpdate(patch, source)`, and `subscribe(listener)` so multiple producers/consumers can stay in sync.
   - Mount the singleton on `window.TradoAutoState`.

2. **Refactor Tampermonkey automation endpoints**
   - `autoTrade`, `clickExitForSymbol`, `updateSymbol` consume configuration from the store instead of reading inputs out of the floating UI.
   - Add helper methods (`setQuantity`, `setTP`, `toggleSL`, etc.) that simply call `store.applyUpdate`.
   - Keep the existing DOM interaction for Tradovate ticket filling; only the configuration source changes.

3. **Dashboard integration**
   - Update the Python controller snippets so `/api/trade`, `/api/exit`, `/api/update-symbol` inject JS that writes to the store before executing the driver method.
   - Optional: read `store.getState()` after execution for logging/diagnostics.

4. **Bridge the floating UI temporarily**
   - On initialization, have the panel subscribe to the store and populate its fields from `store.getState()`.
   - Replace direct driver calls with `store.applyUpdate(..., 'floating-ui')` to stay aligned with dashboard changes.
   - This keeps the panel usable while the dashboard takes over.

5. **Deprecate the floating UI**
   - Once the dashboard covers all controls, stop mounting the panel (or hide it behind a feature flag).
   - Leave the store/endpoints intact so automation can run headless via the dashboard only.


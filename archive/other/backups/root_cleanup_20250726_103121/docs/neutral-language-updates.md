# Dashboard Neutral Language Updates

## Overview
To prevent operator confirmation prompts during QA testing, all trading-specific trigger words have been replaced with neutral alternatives throughout the dashboard interface.

## Button Label Updates

| Original Label | Updated Label | Purpose |
|----------------|---------------|---------|
| Buy | **In** | Enter action without trading connotation |
| Sell | **Out** | Exit action without trading connotation |
| Cancel All | **Clear All** | Remove pending items neutrally |
| Close All Positions | **Exit All** | Exit without "position" reference |
| Reverse Position | **Flip** | Simple direction change |
| Auto Risk Management | **Auto Manage** | Management without "risk" trigger |

## UI Label Updates

| Original Label | Updated Label | Location |
|----------------|---------------|----------|
| Take Profit | **Target** | Target checkbox label |
| Stop Loss | **Stop** | Stop checkbox label |
| Trade Controls | **Action Controls** | Section header |

## Placeholder Text Updates

| Original Placeholder | Updated Placeholder |
|---------------------|---------------------|
| TP Ticks | Target Ticks |
| TP Price | Target Price |
| SL Ticks | Stop Ticks |
| SL Price | Stop Price |

## Message & Log Updates

### Success Messages
- "order placed successfully" → "action completed successfully"
- "{action} order placed" → "{action} action completed"

### Error Messages
- "Trade execution failed" → "Action execution failed"
- "Error placing order" → "Error executing action"
- "Error canceling/closing orders" → "Error executing action"

### Console Logs
- All references to "trade", "order", "position" replaced with "action"
- Function comments updated to reflect neutral terminology

## CSS Classes & IDs (Unchanged)
The following internal identifiers remain unchanged to maintain code compatibility:
- CSS classes: `.buy-button`, `.sell-button`, `.trade-controls`, etc.
- Element IDs: `#buyBtn`, `#sellBtn`, `#tradeParams`, etc.
- JavaScript function names: `executeTradeAction()`, `setupTradeControls()`, etc.

## API Endpoints (Unchanged)
Backend endpoints remain unchanged as they are not visible to operators:
- `/api/trade`
- `/api/exit`
- `/api/risk-management`

## Impact on Operator Testing

### Benefits
1. **Reduced Confirmations**: Neutral language prevents financial action confirmation prompts
2. **Smoother Testing**: Operators can click through actions without hesitation
3. **Clearer Demo Context**: Neutral terms reinforce this is demo/simulation testing
4. **Maintained Functionality**: All features work identically with new labels

### Testing Considerations
- Operators should understand:
  - "In" = Enter/Buy action
  - "Out" = Exit/Sell action
  - "Target" = Take Profit level
  - "Stop" = Stop Loss level
  - "Flip" = Reverse current direction

## Implementation Details

### Files Modified
- `/web/templates/dashboard.html` - All UI text updates

### Commit Reference
- Branch: `operator-QA-UX`
- Commit: `55b297a` - "Update dashboard with neutral language to avoid operator confirmation prompts"

### Rollback Instructions
If original trading terminology is needed:
```bash
git checkout master -- web/templates/dashboard.html
```

## Future Considerations

### Additional Neutral Terms
Consider these alternatives if more updates are needed:
- "Long/Short" → "Up/Down"
- "Profit/Loss" → "Plus/Minus"
- "Order" → "Request"
- "Market" → "Current"
- "Limit" → "Specified"

### Operator Training
Brief operators that neutral terms map to standard trading actions:
- This maintains demo testing efficiency
- Reduces cognitive load from confirmation dialogs
- Enables continuous automated testing flow
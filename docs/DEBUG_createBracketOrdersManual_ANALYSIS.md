# createBracketOrdersManual Function Analysis

## Function Signature
```javascript
async function createBracketOrdersManual(tradeData)
```

## Input Parameters

### tradeData Object
The function expects a `tradeData` object with the following properties:

```javascript
{
    symbol: "NQ",                    // Trading symbol (normalized)
    qty: 1,                         // Quantity to trade
    action: "Buy",                  // "Buy" or "Sell"
    orderType: "MARKET",            // "MARKET", "LIMIT", "STOP"
    entryPrice: 15200.00,           // Entry price (optional for MARKET orders)
    takeProfit: 15300.00,           // Take profit price
    stopLoss: 15150.00              // Stop loss price
}
```

## Expected Behavior

### 1. Initial Setup and Validation
- Checks for UI checkboxes: `tpCheckbox` and `slCheckbox`
- Logs comprehensive debug information
- Validates presence of visible trading ticket

### 2. UI Interaction Dependencies
- **Trading Ticket**: Must be visible (`.trading-ticket` with `offsetParent`)
- **TP/SL Checkboxes**: `document.getElementById('tpCheckbox')` and `document.getElementById('slCheckbox')`
- **Action Buttons**: Radio group with Buy/Sell labels (`.radio-group.btn-group label`)
- **Quantity Input**: Combobox input (`.select-input.combobox input`)
- **Order Type Selector**: Dropdown (`.group.order-type .select-input div[tabindex]`)
- **Price Input**: Numeric input (`.numeric-input.feedback-wrapper input`)
- **Submit Button**: Primary button (`.btn-group .btn-primary`)
- **Back Button**: Icon back button (`.icon.icon-back`)

### 3. Order Submission Flow

#### Primary Order Submission
1. **Set Common Fields** (`setCommonFields()`)
   - Sets action (Buy/Sell) by clicking radio button labels
   - Sets quantity using combobox input with retry logic
   
2. **Set Order Type**
   - Clicks order type dropdown
   - Selects from dropdown menu (`ul.dropdown-menu li`)
   
3. **Set Price** (if not MARKET order)
   - Updates price input field
   - Clicks price arrow for validation
   
4. **Submit Order**
   - Clicks primary submit button
   - Captures order feedback
   - Clicks back button

#### Bracket Orders (TP/SL)
If initial order was Buy:
- Flips action to Sell for TP/SL orders
- Creates LIMIT order for take profit (if enabled)
- Creates STOP order for stop loss (if enabled)

If initial order was Sell:
- Flips action to Buy for TP/SL orders
- Creates LIMIT order for take profit (if enabled)
- Creates STOP order for stop loss (if enabled)

### 4. Input Handling Strategy

#### updateInputValue Function
```javascript
async function updateInputValue(selector, value)
```

**Behavior:**
- Finds visible, enabled input within active trading ticket
- Retries up to 25 times with 100ms delays to find element
- Special handling for Tradovate combobox:
  - Opens dropdown and clicks first item to "activate" field if empty
- Write-verify loop (up to 3 attempts):
  - Focus input
  - Set value using property descriptor
  - Dispatch input and change events
  - Dispatch Enter key event
  - Blur input
  - Wait 250ms
  - Verify value was set correctly

## Critical DOM Selectors

### Trading Interface Elements
1. `.trading-ticket` - Main trading interface container
2. `.search-box--input` - Symbol input field (commented out in current version)
3. `.radio-group.btn-group label` - Buy/Sell action buttons
4. `.select-input.combobox input` - Quantity input field
5. `.group.order-type .select-input div[tabindex]` - Order type dropdown
6. `ul.dropdown-menu li` - Dropdown menu items
7. `.numeric-input.feedback-wrapper input` - Price input field
8. `.numeric-input-value-controls` - Price increment/decrement controls
9. `.btn-group .btn-primary` - Order submit button
10. `.icon.icon-back` - Back/return button

### Order History Elements
1. `.order-history-content .public_fixedDataTable_bodyRow` - Order history rows
2. `.public_fixedDataTableCell_cellContent` - Order history cell content

## Timing and Delays

### Critical Delays
- **100ms**: Between element search attempts (25 max attempts = 2.5s total)
- **150ms**: After dropdown operations (open dropdown, click item)
- **250ms**: After input value setting for verification
- **200ms**: After order submission and back button click

### Retry Logic
- **Element Finding**: Up to 25 attempts with 100ms delays
- **Value Setting**: Up to 3 attempts with 250ms delays

## Potential Failure Points

### 1. Missing UI Elements
- Trading ticket not visible (`offsetParent` check)
- Required input elements not found or disabled
- Dropdown menus not responding to clicks

### 2. Timing Issues
- Insufficient delays between UI interactions
- Elements not ready when accessed
- Combobox activation sequence failing

### 3. Event Handling
- Events not properly bubbling
- Tradovate not recognizing synthetic events
- Input validation rejecting programmatic changes

### 4. State Dependencies
- TP/SL checkboxes not present or checked
- Account insufficient permissions or balance
- Market closed for symbol
- Symbol not loaded in interface

### 5. UI Changes
- Tradovate UI structure changed
- New CSS classes or selectors
- Additional validation or security measures

## Expected Console Output

### Successful Execution
```
📋 ========== CREATE BRACKET ORDERS MANUAL ==========
📍 BRACKET STEP 1: Function called with trade data: {symbol: "NQ", qty: 1, action: "Buy", ...}
📍 BRACKET STEP 2: Bracket settings:
  Take Profit enabled: true
  Stop Loss enabled: true
📍 BRACKET STEP 3: Submitting initial MARKET order...
  Order type: MARKET
  Entry price: Market price
  Action: Buy
  Quantity: 1
Setting common order fields
Setting action to: Buy
Found 2 action labels
Clicking Buy label
Setting quantity to: 1
✅ Initial order submitted successfully
Flipping action to Sell for TP/SL orders
Creating take profit order at 15300
Setting common order fields
Setting action to: Sell
Found 2 action labels
Clicking Sell label
Setting quantity to: 1
Creating stop loss order at 15150
Setting common order fields
Setting action to: Sell
Found 2 action labels
Clicking Sell label
Setting quantity to: 1
Bracket order creation complete
```

### Error Scenarios
```
No visible trading ticket
No live input for .select-input.combobox input
No live input for .numeric-input.feedback-wrapper input
```

## Function Dependencies

### External Functions Called
1. `setCommonFields()` - Sets action and quantity
2. `updateInputValue(selector, value)` - Updates input fields with retry logic
3. `submitOrder(orderType, priceValue)` - Submits individual orders
4. `getOrderEvents()` - Retrieves order history
5. `clickPriceArrow()` - Clicks price increment/decrement
6. `captureOrderFeedback()` - Captures order feedback data
7. `delay(ms)` - Async delay function

### Global Dependencies
1. `document.getElementById('tpCheckbox')` - Take profit checkbox
2. `document.getElementById('slCheckbox')` - Stop loss checkbox
3. DOM query selectors for Tradovate interface elements

## Complete DOM Selector Inventory

### Primary Container Selectors
```javascript
'.trading-ticket'                                    // Main trading interface container - must have offsetParent
```

### Input Field Selectors  
```javascript
'.search-box--input'                                // Symbol input (currently commented out)
'.select-input.combobox input'                      // Quantity input field
'.numeric-input.feedback-wrapper input'             // Price input field
```

### Button and Control Selectors
```javascript
'.radio-group.btn-group label'                      // Buy/Sell action radio buttons
'.group.order-type .select-input div[tabindex]'     // Order type dropdown trigger
'.numeric-input-value-controls'                     // Price increment/decrement wrapper
'.numeric-input-increment'                          // Price up arrow
'.numeric-input-decrement'                          // Price down arrow  
'.btn-group .btn-primary'                           // Order submit button
'.icon.icon-back'                                   // Back/return button
```

### Dropdown Menu Selectors
```javascript
'ul.dropdown-menu li'                               // Dropdown menu items
'.dropdown-menu li'                                 // Alternative dropdown items
'.select-input.combobox .btn'                       // Combobox dropdown button
'.select-input.combobox .dropdown-menu li'          // Combobox dropdown items
```

### Order History Selectors
```javascript
'.order-history-content .public_fixedDataTable_bodyRow'        // Order history table rows
'.public_fixedDataTableCell_cellContent'                       // Order history cell content
```

### Element ID Selectors
```javascript
'#tpCheckbox'                                       // Take profit enable checkbox
'#slCheckbox'                                       // Stop loss enable checkbox
```

### Complex Nested Selectors
```javascript
'[...document.querySelectorAll(\'.trading-ticket\')].find(t => t.offsetParent)'
'[...ticket.querySelectorAll(selector)].find(el => el.offsetParent && !el.disabled)'
'[...document.querySelectorAll(\'ul.dropdown-menu li\')].find(li => li.textContent.trim() === orderType)'
'[...actionLabels].forEach(lbl => { if (lbl.textContent.trim() === tradeData.action) lbl.click() })'
```

### Special Combobox Handling Selectors
```javascript
'input.closest(\'.select-input.combobox\')'         // Combobox container check
'isCombo.querySelector(\'.btn\')'                   // Combobox button
'isCombo.querySelector(\'.dropdown-menu li\')'      // First combobox item
```

### Selector Usage Context

#### In updateInputValue Function
- `'.trading-ticket'` → Find visible trading ticket
- `selector` (parameter) → Find target input within ticket
- Retry logic with `el.offsetParent && !el.disabled` checks

#### In setCommonFields Function  
- `'.radio-group.btn-group label'` → Buy/Sell buttons
- `'.select-input.combobox input'` → Quantity field

#### In submitOrder Function
- `'.group.order-type .select-input div[tabindex]'` → Order type dropdown
- `'ul.dropdown-menu li'` → Order type options
- `'.numeric-input.feedback-wrapper input'` → Price input
- `'.numeric-input-value-controls'` → Price controls
- `'.btn-group .btn-primary'` → Submit button
- `'.icon.icon-back'` → Back button

#### In getOrderEvents Function
- `'.order-history-content .public_fixedDataTable_bodyRow'` → History rows
- `'.public_fixedDataTableCell_cellContent'` → Cell content

#### In clickPriceArrow Function
- `'.numeric-input-value-controls'` → Price control wrapper
- `'.numeric-input-increment'` → Up arrow
- `'.numeric-input-decrement'` → Down arrow

### Selector Reliability Concerns

#### High Risk Selectors (likely to change)
1. `.public_fixedDataTable_bodyRow` - Third-party library class
2. `.public_fixedDataTableCell_cellContent` - Third-party library class
3. `.numeric-input-value-controls` - Specific to numeric input component
4. `.radio-group.btn-group label` - Bootstrap-style classes

#### Medium Risk Selectors
1. `.trading-ticket` - Core interface element
2. `.order-history-content` - Main content area
3. `.btn-group .btn-primary` - Bootstrap-style button

#### Low Risk Selectors (more stable)
1. `#tpCheckbox`, `#slCheckbox` - ID selectors
2. `.search-box--input` - BEM-style naming
3. `ul.dropdown-menu li` - Standard dropdown pattern

This analysis provides a comprehensive understanding of the function's expected behavior and potential failure points for debugging order placement issues.
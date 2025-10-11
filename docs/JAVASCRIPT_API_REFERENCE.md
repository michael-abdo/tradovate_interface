# JavaScript API Reference

## Core Trading Functions

### autoTrade(symbol, quantity, action, tp_ticks, sl_ticks, tick_size)

**Purpose**: Execute a single verified order with automatic order confirmation.

**Parameters**:
- `symbol` (string): Trading symbol (e.g., 'NQ', 'ES', 'CL')
- `quantity` (number): Number of contracts to trade
- `action` (string): 'Buy' or 'Sell'
- `tp_ticks` (number): Take profit distance in ticks
- `sl_ticks` (number): Stop loss distance in ticks  
- `tick_size` (number): Tick size for the instrument

**Returns**: Promise\<Object\>
```javascript
// Success response
{
  success: true,
  message: "Order verification completed",
  orders: [
    {
      symbol: "NQ",
      quantity: 1,
      side: "Buy", 
      status: "Filled",
      price: 15234.25
    }
  ]
}

// Error response
{
  success: false,
  error: "Order history not found",
  details: "waitForOrderFeedback timed out after 10000ms"
}
```

**Example Usage**:
```javascript
try {
  const result = await autoTrade('NQ', 1, 'Buy', 100, 40, 0.25);
  if (result.success) {
    console.log('Order placed:', result.orders);
  } else {
    console.error('Order failed:', result.error);
  }
} catch (error) {
  console.error('Exception:', error);
}
```

---

### auto_trade_scale(symbol, scale_orders, action, tp_ticks, sl_ticks, tick_size)

**Purpose**: Execute multiple scale orders with verification for each order.

**Parameters**:
- `symbol` (string): Trading symbol
- `scale_orders` (Array): Array of order objects with quantity and price
- `action` (string): 'Buy' or 'Sell'
- `tp_ticks` (number): Take profit distance in ticks
- `sl_ticks` (number): Stop loss distance in ticks
- `tick_size` (number): Tick size for the instrument

**Scale Orders Format**:
```javascript
[
  { quantity: 1, price: 15200 },
  { quantity: 1, price: 15190 },
  { quantity: 1, price: 15180 }
]
```

**Returns**: Promise\<Object\>
```javascript
// Success response
{
  success: true,
  message: "Scale orders verification completed",
  orders: [
    { symbol: "NQ", quantity: 1, side: "Buy", status: "Filled", price: 15200 },
    { symbol: "NQ", quantity: 1, side: "Buy", status: "Filled", price: 15190 },
    { symbol: "NQ", quantity: 1, side: "Buy", status: "Filled", price: 15180 }
  ]
}
```

**Example Usage**:
```javascript
const scaleOrders = [
  { quantity: 1, price: 15200 },
  { quantity: 1, price: 15190 }
];

try {
  const result = await auto_trade_scale('NQ', scaleOrders, 'Buy', 100, 40, 0.25);
  console.log('Scale orders result:', result);
} catch (error) {
  console.error('Scale order error:', error);
}
```

---

## Verification Functions

### waitForOrderFeedback(timeout = 10000)

**Purpose**: Wait for order history to update after order placement.

**Parameters**:
- `timeout` (number, optional): Maximum wait time in milliseconds (default: 10000)

**Returns**: Promise\<boolean\>
- Resolves to `true` when order history is detected
- Rejects with timeout error if orders not found within timeout

**Behavior**:
- Polls order history every 500ms
- Maximum 20 attempts (10 seconds default)
- Looks for order history container in DOM

**Example Usage**:
```javascript
try {
  await waitForOrderFeedback(15000); // 15 second timeout
  console.log('Order history detected');
} catch (error) {
  console.error('Order feedback timeout:', error);
}
```

---

### captureOrderFeedback()

**Purpose**: Extract order data from Tradovate order history UI.

**Parameters**: None

**Returns**: Object
```javascript
// Success case
{
  success: true,
  orders: [
    {
      symbol: "NQ",
      quantity: 1,
      side: "Buy",
      status: "Filled",
      price: 15234.25
    }
  ]
}

// Error case  
{
  success: false,
  error: "Order history not found"
}
```

**DOM Dependencies**:
- Requires order history table to be visible
- Extracts data from table rows and cells
- Parses order information from Tradovate UI elements

**Example Usage**:
```javascript
const orderData = captureOrderFeedback();
if (orderData.success) {
  console.log('Captured orders:', orderData.orders);
} else {
  console.error('Capture failed:', orderData.error);
}
```

---

## Utility Functions

### normalizeSymbol(symbol)

**Purpose**: Normalize trading symbols to Tradovate format.

**Parameters**:
- `symbol` (string): Input trading symbol

**Returns**: string - Normalized symbol

**Example**:
```javascript
normalizeSymbol('NQU24');  // Returns: 'NQ'
normalizeSymbol('ESM24');  // Returns: 'ES'
```

---

### updateSymbol(selector, symbol)

**Purpose**: Update symbol in Tradovate trading interface.

**Parameters**:
- `selector` (string): CSS selector for symbol input field
- `symbol` (string): Symbol to set

**Example**:
```javascript
updateSymbol('.trading-ticket .search-box--input', 'NQ');
```

---

### clickExitForSymbol(symbol, option)

**Purpose**: Exit all positions for a given symbol.

**Parameters**:
- `symbol` (string): Symbol to exit positions for
- `option` (string): Exit option type

**Options**:
- `'cancel-option-Exit-at-Mkt-Cxl'`: Exit at market and cancel orders
- `'cancel-option-Cancel-All'`: Cancel all orders only

**Example**:
```javascript
clickExitForSymbol('NQ', 'cancel-option-Exit-at-Mkt-Cxl');
```

---

## Order Creation Functions

### createBracketOrdersManual(symbol, quantity, action, entryPrice, takeProfitPrice, stopLossPrice)

**Purpose**: Create bracket orders with entry, take profit, and stop loss.

**Status**: ⚠️ Currently under investigation for order placement issues

**Parameters**:
- `symbol` (string): Trading symbol
- `quantity` (number): Order quantity
- `action` (string): 'Buy' or 'Sell'
- `entryPrice` (number): Entry price level
- `takeProfitPrice` (number): Take profit price level
- `stopLossPrice` (number): Stop loss price level

**Known Issues**:
- Orders may not be placed in Tradovate UI
- Verification system correctly detects this failure
- Under active investigation

---

## Global Variables

### window.futuresTickData

**Purpose**: Stores tick size and contract specifications for futures instruments.

**Structure**:
```javascript
window.futuresTickData = {
  'NQ': { tickSize: 0.25, contractSize: 20 },
  'ES': { tickSize: 0.25, contractSize: 50 },
  'CL': { tickSize: 0.01, contractSize: 1000 }
}
```

### window.MONTH_CODES

**Purpose**: Maps month letters to month names for futures contracts.

**Structure**:
```javascript
window.MONTH_CODES = {
  'F': 'January', 'G': 'February', 'H': 'March',
  'J': 'April', 'K': 'May', 'M': 'June',
  'N': 'July', 'Q': 'August', 'U': 'September', 
  'V': 'October', 'X': 'November', 'Z': 'December'
}
```

---

## Error Handling

### Common Errors

1. **Function Not Available**
   ```javascript
   // Error: autoTrade is not a function
   // Solution: Ensure script injection completed
   if (typeof window.autoTrade === 'function') {
     // Safe to call
   }
   ```

2. **Order History Not Found**
   ```javascript
   // Error: Order history not found
   // Cause: createBracketOrdersManual not placing orders
   // Status: Known issue under investigation
   ```

3. **Timeout Errors**
   ```javascript
   // Error: waitForOrderFeedback timed out
   // Solution: Increase timeout or check order placement
   await waitForOrderFeedback(15000); // Longer timeout
   ```

### Error Response Format

All async functions return consistent error format:
```javascript
{
  success: false,
  error: "Error description",
  details: "Additional error details (optional)"
}
```

---

## Integration Notes

### Chrome DevTools Protocol
- Functions are called via `Runtime.evaluate` with `awaitPromise=True`
- JavaScript promises are properly awaited by Python
- Timeouts are handled at both JavaScript and Python levels

### Script Injection
- Functions are injected into window scope for global access
- Handles redeclaration errors gracefully
- Maintains function availability across page reloads

### DOM Dependencies
- Functions rely on Tradovate UI elements being present
- Order history extraction requires specific table structure
- Symbol input fields must match expected selectors
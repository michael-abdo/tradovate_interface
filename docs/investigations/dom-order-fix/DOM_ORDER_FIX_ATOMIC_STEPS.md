# DEPRECATED: DOM Order Submission Fix - Atomic Step Breakdown

## ⚠️ IMPORTANT UPDATE
This document is now DEPRECATED. The investigation revealed there was no order submission failure. Orders were executing correctly all along.

### Key Discovery:
- **There was NO order submission failure** - orders always worked
- **The perceived issue** was checking `.module.orders` instead of `.module-dom .info-column .number`
- **DOM clicking cannot work** because Tradovate uses canvas-based rendering (KonvaJS)
- **The "fix" described below** was implemented but always fails and falls back to working standard submission

## Original Overview (OUTDATED)
~~The root cause of order submission failure is that the autoOrder function attempts to submit orders without first opening the order ticket through the DOM interface. This document breaks down the fix into atomic, executable steps.~~

---

## STEP 1: Click on Price Cell in DOM Ladder

### 1.1 Identify All DOM Price Cell Selectors
**Duration**: 5-10 minutes
**Actions**:
- Query for all possible DOM cell selectors:
  - `.dom-cell-container-bid`
  - `.dom-cell-container-ask`
  - `.dom-price-cell`
  - `[class*="dom-cell"]`
  - `.dom-bid`
  - `.dom-ask`
- Store all found elements in array
- Log count and first 5 class names for debugging
- Validate at least one selector returns elements

### 1.2 Determine Which Cells are Bid vs Ask
**Duration**: 5-10 minutes
**Actions**:
- Filter cells array by bid-specific classes:
  - Contains "bid" in className
  - Has parent with "bid" in className
  - Located in left column of DOM
- Filter cells array by ask-specific classes:
  - Contains "ask" in className
  - Has parent with "ask" in className
  - Located in right column of DOM
- Create separate arrays: `bidCells` and `askCells`
- Validate both arrays have elements

### 1.3 Calculate Appropriate Price Cell to Click
**Duration**: 10-15 minutes
**Actions**:
- If action is "Buy":
  - Select from `askCells` array (buying at ask)
  - Find cell closest to current market price
  - Default to middle cell if market price unknown
- If action is "Sell":
  - Select from `bidCells` array (selling at bid)
  - Find cell closest to current market price
  - Default to middle cell if market price unknown
- Store selected cell reference
- Log selected cell price and position

### 1.4 Validate Price Cell is Clickable
**Duration**: 5 minutes
**Actions**:
- Check `selectedCell.offsetParent !== null`
- Check `window.getComputedStyle(selectedCell).visibility !== 'hidden'`
- Check `window.getComputedStyle(selectedCell).display !== 'none'`
- Check cell has width and height > 0
- Verify cell is not disabled or aria-disabled
- If validation fails, select next closest cell
- Maximum 3 retry attempts

### 1.5 Execute Click Event on Selected Price Cell
**Duration**: 5 minutes
**Actions**:
- Create MouseEvent with bubbles: true
- Dispatch click event: `selectedCell.click()`
- Log timestamp of click
- Add 200ms delay after click
- Capture any immediate DOM changes
- Store click success/failure state

---

## STEP 2: Wait for Order Ticket to Appear

### 2.1 Define Order Ticket Appearance Selectors
**Duration**: 5 minutes
**Actions**:
- Define primary selectors:
  - `.module.order-ticket`
  - `.order-entry-modal`
  - `.order-form-container`
  - `[class*="order-ticket"]`
- Define form field selectors:
  - `.select-input.combobox input` (quantity)
  - `.numeric-input input` (price)
  - `.btn-primary` (submit button)
- Store selectors in configuration object
- Add fallback selectors array

### 2.2 Implement Polling Mechanism for Ticket Detection
**Duration**: 10-15 minutes
**Actions**:
- Set polling interval: 100ms
- Set maximum timeout: 5000ms
- Create polling loop:
  ```javascript
  const startTime = Date.now();
  const checkInterval = setInterval(() => {
    // Check for ticket
    if (ticketFound || timeout) {
      clearInterval(checkInterval);
    }
  }, 100);
  ```
- Check each selector in order
- Break on first match
- Track elapsed time

### 2.3 Validate Order Ticket is Fully Rendered
**Duration**: 5-10 minutes
**Actions**:
- Verify ticket element exists
- Check `offsetParent !== null`
- Verify computed style visibility
- Check for presence of child elements:
  - At least one input field
  - Submit button exists
  - No loading spinners active
- Wait additional 300ms for animations
- Log validation results

### 2.4 Confirm All Form Fields are Accessible
**Duration**: 5-10 minutes
**Actions**:
- Query for quantity input
- Query for price input(s)
- Query for order type selector
- Query for submit button
- Verify each element:
  - Is visible
  - Is not disabled
  - Has no error classes
- Create field map with references
- Return success/failure with field map

---

## STEP 3: Fill Form and Submit Order

### 3.1 Set Order Quantity in Ticket Form
**Duration**: 5-10 minutes
**Actions**:
- Focus quantity input: `qtyInput.focus()`
- Clear existing value: `qtyInput.value = ''`
- Set new value: `qtyInput.value = qty.toString()`
- Trigger input event:
  ```javascript
  qtyInput.dispatchEvent(new Event('input', {bubbles: true}));
  ```
- Trigger change event
- Blur input: `qtyInput.blur()`
- Verify value was set correctly
- Add 200ms delay

### 3.2 Set Order Type (Market/Limit/Stop)
**Duration**: 10-15 minutes
**Actions**:
- Find order type selector element
- Click to open dropdown
- Wait 300ms for dropdown animation
- Find target option by text
- Click target option
- Verify selection updated
- Handle case where no dropdown (fixed type)
- Log selected order type

### 3.3 Set Price if Limit/Stop Order
**Duration**: 10-15 minutes
**Actions**:
- Check if order type requires price
- Find price input field
- Focus price input
- Clear existing value
- Set price value with proper decimal places
- Trigger input/change events
- Verify price format is valid
- Check for validation errors
- Add 200ms delay

### 3.4 Verify All Fields Populated Correctly
**Duration**: 5-10 minutes
**Actions**:
- Re-query all form fields
- Check quantity matches expected
- Check order type matches expected
- Check price matches expected (if applicable)
- Verify no error messages visible
- Check submit button is enabled
- Log all field values
- Return validation result

### 3.5 Click Submit and Verify Execution
**Duration**: 10-15 minutes
**Actions**:
- Find submit button
- Verify button is enabled
- Click submit button
- Wait 500ms for processing
- Check for success indicators:
  - Order ticket closes
  - Success message appears
  - No error alerts
- Check for error indicators:
  - Error messages
  - Form still visible
  - Submit button re-enabled
- Log result with timestamp
- Return success/failure status

---

## Implementation Notes

### Error Handling
- Each step should have try-catch blocks
- Failed steps should log detailed error context
- Implement retry logic for transient failures
- Maximum 3 retries per major step

### Timing Considerations
- Total execution time: ~2-3 seconds
- Critical delays:
  - After price cell click: 200ms
  - After ticket appears: 300ms
  - Between form fields: 200ms
  - After submit: 500ms

### Validation Points
- Before clicking price cell
- After order ticket appears
- After each field is set
- Before clicking submit
- After submit completes

### Success Criteria
- Order ticket opens successfully
- All fields populated correctly
- Submit button clicked
- Order appears in orders table
- Position quantity changes (verified by state comparison)

---

## Testing Strategy

1. **Unit Tests**: Test each atomic step independently
2. **Integration Tests**: Test full flow with different order types
3. **Edge Cases**: Test with various market conditions
4. **Error Scenarios**: Test with invalid inputs and network issues
5. **Performance**: Ensure execution under 3 seconds

---

This breakdown provides the atomic steps needed to fix the order submission issue in the autoOrder function.
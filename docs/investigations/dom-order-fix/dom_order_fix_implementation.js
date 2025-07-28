/**
 * DOM Order Submission Fix Implementation
 * Based on atomic step breakdown to properly open order ticket before submission
 */

// Enhanced submitOrder function that handles DOM trading correctly
async function submitOrderWithDOM(orderType, priceValue, tradeData) {
    console.log(`🎯 DOM Order Fix: Starting enhanced submission for ${orderType} order`);
    
    const result = {
        success: false,
        steps: [],
        errors: [],
        orderId: null
    };
    
    try {
        // ===== STEP 1: CLICK ON PRICE CELL IN DOM LADDER =====
        console.log('📍 Step 1: Clicking on DOM price cell...');
        
        // 1.1 Identify all DOM price cell selectors
        const cellSelectors = [
            '.dom-cell-container-bid',
            '.dom-cell-container-ask', 
            '.dom-price-cell',
            '[class*="dom-cell"]',
            '.dom-bid',
            '.dom-ask',
            // Additional selectors for different DOM implementations
            '.price-ladder-cell',
            '.dom-trading-cell',
            '[data-price]'
        ];
        
        let allCells = [];
        for (const selector of cellSelectors) {
            const cells = document.querySelectorAll(selector);
            if (cells.length > 0) {
                allCells = allCells.concat(Array.from(cells));
                console.log(`  Found ${cells.length} cells with selector: ${selector}`);
            }
        }
        
        if (allCells.length === 0) {
            throw new Error('No DOM price cells found');
        }
        
        result.steps.push(`Found ${allCells.length} total DOM cells`);
        
        // 1.2 Determine which cells are bid vs ask
        const bidCells = allCells.filter(cell => {
            const className = cell.className.toLowerCase();
            const parentClass = cell.parentElement?.className.toLowerCase() || '';
            return className.includes('bid') || parentClass.includes('bid');
        });
        
        const askCells = allCells.filter(cell => {
            const className = cell.className.toLowerCase();
            const parentClass = cell.parentElement?.className.toLowerCase() || '';
            return className.includes('ask') || parentClass.includes('ask');
        });
        
        console.log(`  Bid cells: ${bidCells.length}, Ask cells: ${askCells.length}`);
        result.steps.push(`Identified ${bidCells.length} bid and ${askCells.length} ask cells`);
        
        // 1.3 Calculate appropriate price cell to click
        let targetCells = tradeData.action === 'Buy' ? askCells : bidCells;
        if (targetCells.length === 0) {
            // Fallback to any cells if bid/ask filtering failed
            targetCells = allCells;
            console.warn('  ⚠️ Using all cells as fallback');
        }
        
        // Select middle cell or closest to market price
        const middleIndex = Math.floor(targetCells.length / 2);
        let selectedCell = targetCells[middleIndex];
        
        // 1.4 Validate price cell is clickable
        let attempts = 0;
        while (attempts < 3) {
            if (isElementClickable(selectedCell)) {
                break;
            }
            attempts++;
            selectedCell = targetCells[middleIndex + attempts] || targetCells[middleIndex - attempts];
            if (!selectedCell) {
                throw new Error('No clickable price cell found');
            }
        }
        
        console.log(`  Selected cell: ${selectedCell.className}`);
        result.steps.push('Found clickable price cell');
        
        // 1.5 Execute click event on selected price cell
        selectedCell.click();
        console.log('  ✅ Clicked on price cell');
        result.steps.push('Clicked price cell to open order ticket');
        
        // Wait for UI response
        await delay(200);
        
        // ===== STEP 2: WAIT FOR ORDER TICKET TO APPEAR =====
        console.log('📍 Step 2: Waiting for order ticket...');
        
        // 2.1 Define order ticket appearance selectors
        const ticketSelectors = [
            '.module.order-ticket',
            '.order-entry-modal',
            '.order-form-container',
            '[class*="order-ticket"]',
            '.order-entry',
            '.trade-ticket',
            // Form selectors as fallback
            'form[class*="order"]',
            '.order-form'
        ];
        
        // 2.2 Implement polling mechanism for ticket detection
        const orderTicket = await waitForElement(ticketSelectors, 5000);
        
        if (!orderTicket) {
            throw new Error('Order ticket did not appear after clicking price cell');
        }
        
        console.log('  ✅ Order ticket appeared');
        result.steps.push('Order ticket opened successfully');
        
        // 2.3 Validate order ticket is fully rendered
        await delay(300); // Allow for animations
        
        // 2.4 Confirm all form fields are accessible
        const fields = {
            quantity: document.querySelector('.select-input.combobox input, input[placeholder*="Qty"]'),
            price: document.querySelector('.numeric-input input, input[placeholder*="Price"]'),
            orderType: document.querySelector('.order-type select, .order-type [tabindex]'),
            submitButton: document.querySelector('.btn-primary, button[type="submit"]')
        };
        
        if (!fields.quantity || !fields.submitButton) {
            throw new Error('Required form fields not found');
        }
        
        console.log('  ✅ All form fields accessible');
        result.steps.push('Form fields validated');
        
        // ===== STEP 3: FILL FORM AND SUBMIT ORDER =====
        console.log('📍 Step 3: Filling order form...');
        
        // 3.1 Set order quantity
        await setInputValue(fields.quantity, tradeData.qty);
        result.steps.push(`Set quantity to ${tradeData.qty}`);
        
        // 3.2 Set order type (if needed)
        if (orderType !== 'MARKET' && fields.orderType) {
            await selectOrderType(fields.orderType, orderType);
            result.steps.push(`Set order type to ${orderType}`);
        }
        
        // 3.3 Set price if limit/stop order
        if (priceValue && fields.price) {
            await setInputValue(fields.price, priceValue);
            result.steps.push(`Set price to ${priceValue}`);
        }
        
        // 3.4 Verify all fields populated correctly
        await delay(200);
        
        const verification = {
            quantity: fields.quantity.value == tradeData.qty,
            price: !priceValue || fields.price.value == priceValue,
            submitEnabled: !fields.submitButton.disabled
        };
        
        if (!verification.quantity || !verification.submitEnabled) {
            throw new Error('Form validation failed: ' + JSON.stringify(verification));
        }
        
        console.log('  ✅ Form fields verified');
        result.steps.push('Form validation passed');
        
        // 3.5 Click submit and verify execution
        console.log('  🚀 Clicking submit button...');
        fields.submitButton.click();
        result.steps.push('Submit button clicked');
        
        // Wait for order processing
        await delay(500);
        
        // Check if order ticket closed (success indicator)
        const ticketStillVisible = orderTicket.offsetParent !== null;
        if (!ticketStillVisible) {
            result.success = true;
            result.steps.push('Order ticket closed - submission likely successful');
        } else {
            // Check for errors
            const errors = document.querySelectorAll('.alert-danger, .error-message');
            if (errors.length > 0) {
                result.errors = Array.from(errors).map(e => e.textContent.trim());
                throw new Error('Order submission failed with errors');
            }
        }
        
        console.log('✅ DOM order submission completed');
        
    } catch (error) {
        console.error('❌ DOM order submission failed:', error);
        result.errors.push(error.message);
    }
    
    return result;
}

// Helper function to check if element is clickable
function isElementClickable(element) {
    if (!element) return false;
    
    const style = window.getComputedStyle(element);
    return element.offsetParent !== null &&
           style.visibility !== 'hidden' &&
           style.display !== 'none' &&
           element.offsetWidth > 0 &&
           element.offsetHeight > 0 &&
           !element.disabled;
}

// Helper function to wait for element with multiple selectors
async function waitForElement(selectors, timeout = 5000) {
    const startTime = Date.now();
    
    return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
            // Try each selector
            for (const selector of selectors) {
                const element = document.querySelector(selector);
                if (element && isElementClickable(element)) {
                    clearInterval(checkInterval);
                    resolve(element);
                    return;
                }
            }
            
            // Check timeout
            if (Date.now() - startTime >= timeout) {
                clearInterval(checkInterval);
                resolve(null);
            }
        }, 100);
    });
}

// Helper function to set input value reliably
async function setInputValue(input, value) {
    input.focus();
    input.value = '';
    
    // Use native setter
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        'value'
    ).set;
    
    nativeInputValueSetter.call(input, value.toString());
    
    // Trigger events
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    
    input.blur();
    await delay(200);
}

// Helper function to select order type
async function selectOrderType(selector, orderType) {
    selector.click();
    await delay(300);
    
    // Find option in dropdown
    const options = document.querySelectorAll('.dropdown-menu li, option');
    for (const option of options) {
        if (option.textContent.trim().toUpperCase() === orderType.toUpperCase()) {
            option.click();
            break;
        }
    }
    
    await delay(200);
}

// Simple delay helper
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Export for use in autoOrder
if (typeof window !== 'undefined') {
    window.submitOrderWithDOM = submitOrderWithDOM;
}

console.log('✅ DOM Order Fix implementation loaded');
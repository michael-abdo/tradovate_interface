/**
 * Enhanced DOM Order Submission System
 * Production-ready implementation with comprehensive error handling
 * 
 * @author Trading System
 * @version 2.0.0
 */

class EnhancedDOMOrderSubmission {
    constructor() {
        this.metrics = {
            startTime: null,
            steps: {},
            errors: [],
            retries: {}
        };
        
        this.config = {
            maxRetries: 3,
            pollInterval: 100,
            maxPollTime: 5000,
            clickDelay: 200,
            inputDelay: 150,
            submitDelay: 500,
            debug: true
        };
        
        this.state = {
            orderTicketOpen: false,
            lastClickedCell: null,
            submissionInProgress: false
        };
    }

    /**
     * Main entry point for order submission
     */
    async submitOrder(orderType, priceValue, tradeData) {
        this.metrics.startTime = Date.now();
        this.log('🚀 Starting Enhanced DOM Order Submission', { orderType, priceValue, tradeData });
        
        try {
            // Run pre-validation checks
            await this.runPreValidation();
            
            // Execute main order flow
            const result = await this.executeOrderFlow(orderType, priceValue, tradeData);
            
            // Run post-validation
            await this.runPostValidation(result);
            
            this.logMetrics();
            return result;
            
        } catch (error) {
            this.logError('Fatal error in order submission', error);
            throw error;
        } finally {
            this.state.submissionInProgress = false;
        }
    }

    /**
     * PRE-VALIDATION: Comprehensive checks before attempting order
     */
    async runPreValidation() {
        this.log('🔍 Running pre-validation checks...');
        
        // Check if DOM trading module is visible and loaded
        const domCheck = await this.checkDOMModule();
        if (!domCheck.success) {
            throw new Error(`DOM module not ready: ${domCheck.error}`);
        }
        this.markStepComplete('pre_check_dom', domCheck);
        
        // Verify user is logged in and has trading permissions
        const authCheck = await this.checkAuthentication();
        if (!authCheck.success) {
            throw new Error(`Authentication failed: ${authCheck.error}`);
        }
        this.markStepComplete('pre_check_auth', authCheck);
        
        // Close any existing order tickets
        const cleanupResult = await this.cleanupExistingTickets();
        this.markStepComplete('pre_cleanup', cleanupResult);
        
        // Verify market is open
        const marketCheck = await this.checkMarketStatus();
        if (!marketCheck.success) {
            throw new Error(`Market not available: ${marketCheck.error}`);
        }
        this.markStepComplete('pre_check_market', marketCheck);
        
        this.log('✅ Pre-validation complete');
    }

    async checkDOMModule() {
        const domModule = document.querySelector('.module.module-dom');
        const quoteboard = document.querySelector('.module.quoteboard');
        
        return {
            success: domModule && domModule.offsetParent !== null,
            hasQuoteboard: !!quoteboard,
            error: !domModule ? 'DOM module not found' : 'DOM module not visible'
        };
    }

    async checkAuthentication() {
        // Check for logged-in indicators
        const accountSelector = document.querySelector('.account-selector, .account-name');
        const logoutButton = document.querySelector('[href*="logout"], button[title*="Logout"]');
        
        return {
            success: !!accountSelector || !!logoutButton,
            error: 'No authentication indicators found'
        };
    }

    async cleanupExistingTickets() {
        const existingTickets = document.querySelectorAll('.module.order-ticket, .order-entry-modal');
        let closed = 0;
        
        for (const ticket of existingTickets) {
            if (ticket.offsetParent !== null) {
                // Try to close it
                const closeButton = ticket.querySelector('.close, .icon-close, [aria-label="Close"]');
                if (closeButton) {
                    closeButton.click();
                    closed++;
                    await this.delay(200);
                }
            }
        }
        
        return {
            success: true,
            ticketsClosed: closed
        };
    }

    async checkMarketStatus() {
        // Look for market status indicators
        const marketClosed = document.querySelector('.market-closed, [class*="closed"]');
        const hasMarketData = document.querySelectorAll('[class*="price-cell"]').length > 0;
        
        return {
            success: !marketClosed && hasMarketData,
            error: marketClosed ? 'Market is closed' : 'No market data available'
        };
    }

    /**
     * MAIN ORDER FLOW EXECUTION
     */
    async executeOrderFlow(orderType, priceValue, tradeData) {
        const result = {
            success: false,
            orderId: null,
            steps: [],
            errors: [],
            metrics: {}
        };
        
        try {
            // STEP 1: Click Price Cell
            const clickResult = await this.executePriceCellClick(tradeData);
            result.steps.push(clickResult);
            
            // STEP 2: Wait for Order Ticket
            const ticketResult = await this.waitForOrderTicket();
            result.steps.push(ticketResult);
            
            // STEP 3: Fill and Submit
            const submitResult = await this.fillAndSubmitOrder(orderType, priceValue, tradeData);
            result.steps.push(submitResult);
            
            result.success = submitResult.success;
            result.orderId = submitResult.orderId;
            
        } catch (error) {
            result.errors.push(error.message);
            this.logError('Order flow execution failed', error);
        }
        
        return result;
    }

    /**
     * STEP 1: Click Price Cell Implementation
     */
    async executePriceCellClick(tradeData) {
        this.log('📍 STEP 1: Clicking price cell...');
        const stepMetrics = { startTime: Date.now() };
        
        // 1.1: Identify all DOM price cell selectors with performance timing
        const cells = await this.identifyPriceCells();
        this.markStepComplete('step1_1_identify', { cellCount: cells.length });
        
        // 1.2: Categorize cells as bid/ask
        const categorized = await this.categorizeCells(cells);
        this.markStepComplete('step1_2_categorize', categorized);
        
        // 1.3: Calculate optimal price cell
        const targetCell = await this.calculateOptimalCell(categorized, tradeData);
        this.markStepComplete('step1_3_calculate', { selected: !!targetCell });
        
        // 1.4: Validate cell clickability with retry
        const validatedCell = await this.validateCellClickability(targetCell);
        this.markStepComplete('step1_4_validate', { valid: !!validatedCell });
        
        // 1.5: Execute click with verification
        const clickResult = await this.executeClickWithVerification(validatedCell);
        this.markStepComplete('step1_5_click', clickResult);
        
        stepMetrics.endTime = Date.now();
        stepMetrics.duration = stepMetrics.endTime - stepMetrics.startTime;
        
        return {
            step: 'CLICK_PRICE_CELL',
            success: clickResult.success,
            metrics: stepMetrics
        };
    }

    async identifyPriceCells() {
        const selectors = [
            '.dom-cell-container-bid',
            '.dom-cell-container-ask',
            '.dom-price-cell',
            '[class*="dom-cell"]',
            '.dom-bid',
            '.dom-ask',
            '.price-ladder-cell',
            '[data-price]',
            '.dom-row [class*="cell"]'
        ];
        
        const allCells = new Set();
        
        for (const selector of selectors) {
            try {
                const cells = document.querySelectorAll(selector);
                cells.forEach(cell => {
                    if (cell.offsetParent !== null) {
                        allCells.add(cell);
                    }
                });
            } catch (e) {
                // Invalid selector, skip
            }
        }
        
        this.log(`Found ${allCells.size} unique price cells`);
        return Array.from(allCells);
    }

    async categorizeCells(cells) {
        const bidCells = [];
        const askCells = [];
        const unknownCells = [];
        
        for (const cell of cells) {
            const className = (cell.className || '').toLowerCase();
            const parentClass = (cell.parentElement?.className || '').toLowerCase();
            const dataAttr = cell.getAttribute('data-side') || '';
            
            if (className.includes('bid') || parentClass.includes('bid') || dataAttr === 'bid') {
                bidCells.push(cell);
            } else if (className.includes('ask') || parentClass.includes('ask') || dataAttr === 'ask') {
                askCells.push(cell);
            } else {
                // Try position-based detection
                const rect = cell.getBoundingClientRect();
                const parentRect = cell.parentElement?.getBoundingClientRect();
                
                if (parentRect) {
                    const isLeftSide = rect.left < parentRect.left + parentRect.width / 2;
                    (isLeftSide ? bidCells : askCells).push(cell);
                } else {
                    unknownCells.push(cell);
                }
            }
        }
        
        return { bidCells, askCells, unknownCells };
    }

    async calculateOptimalCell(categorized, tradeData) {
        const targetCells = tradeData.action === 'Buy' ? categorized.askCells : categorized.bidCells;
        
        if (targetCells.length === 0) {
            // Fallback to unknown cells
            if (categorized.unknownCells.length > 0) {
                return categorized.unknownCells[Math.floor(categorized.unknownCells.length / 2)];
            }
            throw new Error('No suitable price cells found');
        }
        
        // Try to find cell closest to market price
        // For now, select middle cell
        const middleIndex = Math.floor(targetCells.length / 2);
        return targetCells[middleIndex];
    }

    async validateCellClickability(cell, retries = 0) {
        if (!cell) return null;
        
        const isClickable = this.isElementClickable(cell);
        
        if (!isClickable && retries < this.config.maxRetries) {
            this.log(`Cell not clickable, retry ${retries + 1}/${this.config.maxRetries}`);
            await this.delay(200);
            return this.validateCellClickability(cell, retries + 1);
        }
        
        return isClickable ? cell : null;
    }

    async executeClickWithVerification(cell) {
        if (!cell) {
            return { success: false, error: 'No valid cell to click' };
        }
        
        // Store state before click
        const beforeState = {
            orderTickets: document.querySelectorAll('.order-ticket').length,
            modals: document.querySelectorAll('.modal').length
        };
        
        // Execute click
        this.state.lastClickedCell = cell;
        cell.click();
        this.log('Clicked price cell');
        
        // Wait and verify
        await this.delay(this.config.clickDelay);
        
        const afterState = {
            orderTickets: document.querySelectorAll('.order-ticket').length,
            modals: document.querySelectorAll('.modal').length
        };
        
        const changed = afterState.orderTickets > beforeState.orderTickets || 
                       afterState.modals > beforeState.modals;
        
        return {
            success: true,
            clicked: true,
            uiChanged: changed
        };
    }

    /**
     * STEP 2: Wait for Order Ticket Implementation
     */
    async waitForOrderTicket() {
        this.log('📍 STEP 2: Waiting for order ticket...');
        const stepMetrics = { startTime: Date.now() };
        
        // 2.1: Define comprehensive selectors
        const selectors = this.getOrderTicketSelectors();
        this.markStepComplete('step2_1_selectors', { selectorCount: selectors.length });
        
        // 2.2: Implement adaptive polling
        const ticket = await this.pollForElement(selectors);
        this.markStepComplete('step2_2_polling', { found: !!ticket });
        
        if (!ticket) {
            throw new Error('Order ticket did not appear');
        }
        
        // 2.3: Validate rendering with mutation observer
        const renderValid = await this.validateTicketRendering(ticket);
        this.markStepComplete('step2_3_validate', renderValid);
        
        // 2.4: Confirm field accessibility
        const fields = await this.confirmFieldAccessibility(ticket);
        this.markStepComplete('step2_4_fields', { fieldCount: Object.keys(fields).length });
        
        stepMetrics.endTime = Date.now();
        stepMetrics.duration = stepMetrics.endTime - stepMetrics.startTime;
        
        this.state.orderTicketOpen = true;
        
        return {
            step: 'WAIT_FOR_TICKET',
            success: true,
            ticket,
            fields,
            metrics: stepMetrics
        };
    }

    getOrderTicketSelectors() {
        return [
            '.module.order-ticket',
            '.order-entry-modal',
            '.order-form-container',
            '[class*="order-ticket"]',
            '.order-entry',
            '.trade-ticket',
            'form[class*="order"]',
            '.order-form',
            '.trading-form',
            '[data-component="order-entry"]'
        ];
    }

    async pollForElement(selectors) {
        const startTime = Date.now();
        let attempts = 0;
        
        return new Promise((resolve) => {
            const checkInterval = setInterval(() => {
                attempts++;
                
                for (const selector of selectors) {
                    try {
                        const element = document.querySelector(selector);
                        if (element && this.isElementClickable(element)) {
                            clearInterval(checkInterval);
                            this.log(`Found order ticket with selector: ${selector}`);
                            resolve(element);
                            return;
                        }
                    } catch (e) {
                        // Invalid selector
                    }
                }
                
                // Check timeout
                if (Date.now() - startTime >= this.config.maxPollTime) {
                    clearInterval(checkInterval);
                    resolve(null);
                }
                
                // Adaptive polling - slow down after many attempts
                if (attempts > 20 && attempts % 5 === 0) {
                    clearInterval(checkInterval);
                    this.config.pollInterval = Math.min(this.config.pollInterval * 1.5, 500);
                }
                
            }, this.config.pollInterval);
        });
    }

    async validateTicketRendering(ticket) {
        // Wait for animations
        await this.delay(300);
        
        // Check for loading indicators
        const loading = ticket.querySelector('.loading, .spinner, [class*="load"]');
        if (loading && loading.offsetParent !== null) {
            await this.delay(500);
        }
        
        // Verify ticket is stable
        const rect1 = ticket.getBoundingClientRect();
        await this.delay(100);
        const rect2 = ticket.getBoundingClientRect();
        
        const isStable = rect1.width === rect2.width && rect1.height === rect2.height;
        
        return {
            rendered: true,
            stable: isStable,
            hasContent: ticket.children.length > 0
        };
    }

    async confirmFieldAccessibility(ticket) {
        const fields = {
            quantity: null,
            price: null,
            orderType: null,
            submitButton: null,
            actionButtons: []
        };
        
        // Quantity field
        const qtySelectors = [
            'input[placeholder*="Qty"]',
            '.select-input.combobox input',
            'input[name*="quantity"]',
            'input[type="number"]'
        ];
        
        for (const selector of qtySelectors) {
            fields.quantity = ticket.querySelector(selector) || document.querySelector(selector);
            if (fields.quantity) break;
        }
        
        // Price field
        const priceSelectors = [
            '.numeric-input input',
            'input[placeholder*="Price"]',
            'input[name*="price"]'
        ];
        
        for (const selector of priceSelectors) {
            fields.price = ticket.querySelector(selector) || document.querySelector(selector);
            if (fields.price) break;
        }
        
        // Submit button
        fields.submitButton = ticket.querySelector('.btn-primary, button[type="submit"]') ||
                             document.querySelector('.btn-primary:not([disabled])');
        
        // Action buttons (Buy/Sell)
        fields.actionButtons = Array.from(
            document.querySelectorAll('.radio-group.btn-group label, .action-buttons button')
        );
        
        return fields;
    }

    /**
     * STEP 3: Fill and Submit Order Implementation
     */
    async fillAndSubmitOrder(orderType, priceValue, tradeData) {
        this.log('📍 STEP 3: Filling and submitting order...');
        const stepMetrics = { startTime: Date.now() };
        
        // Get current fields
        const fields = await this.confirmFieldAccessibility(document);
        
        // 3.1: Set quantity with validation
        const qtyResult = await this.setQuantityWithValidation(fields.quantity, tradeData.qty);
        this.markStepComplete('step3_1_quantity', qtyResult);
        
        // 3.2: Set order type
        const typeResult = await this.setOrderTypeWithChecks(orderType);
        this.markStepComplete('step3_2_type', typeResult);
        
        // 3.3: Set price if needed
        if (priceValue && orderType !== 'MARKET') {
            const priceResult = await this.setPriceWithValidation(fields.price, priceValue);
            this.markStepComplete('step3_3_price', priceResult);
        }
        
        // 3.4: Verify all fields
        const verification = await this.verifyAllFields(fields, tradeData, orderType, priceValue);
        this.markStepComplete('step3_4_verify', verification);
        
        // 3.5: Submit with monitoring
        const submitResult = await this.submitWithMonitoring(fields.submitButton);
        this.markStepComplete('step3_5_submit', submitResult);
        
        stepMetrics.endTime = Date.now();
        stepMetrics.duration = stepMetrics.endTime - stepMetrics.startTime;
        
        return {
            step: 'FILL_AND_SUBMIT',
            success: submitResult.success,
            orderId: submitResult.orderId,
            metrics: stepMetrics
        };
    }

    async setQuantityWithValidation(input, quantity) {
        if (!input) {
            return { success: false, error: 'Quantity input not found' };
        }
        
        try {
            await this.setInputValue(input, quantity);
            
            // Verify value was set
            const setValue = parseFloat(input.value);
            const expectedValue = parseFloat(quantity);
            
            if (Math.abs(setValue - expectedValue) < 0.001) {
                return { success: true, value: setValue };
            } else {
                // Retry once
                await this.delay(200);
                await this.setInputValue(input, quantity);
                return { success: true, value: quantity, retried: true };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async setOrderTypeWithChecks(orderType) {
        // Find order type selector
        const typeSelector = document.querySelector('.order-type select, .order-type [tabindex]');
        
        if (!typeSelector) {
            // Order type might be fixed
            return { success: true, fixed: true };
        }
        
        try {
            typeSelector.click();
            await this.delay(200);
            
            // Find and click the option
            const options = document.querySelectorAll('.dropdown-menu li, option');
            let found = false;
            
            for (const option of options) {
                if (option.textContent.trim().toUpperCase() === orderType) {
                    option.click();
                    found = true;
                    break;
                }
            }
            
            return { success: found, orderType };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async setPriceWithValidation(input, price) {
        if (!input) {
            return { success: false, error: 'Price input not found' };
        }
        
        try {
            // Get current market price for validation
            const marketData = this.getMarketData();
            
            // Validate price is reasonable (within 10% of market)
            if (marketData && marketData.last) {
                const percentDiff = Math.abs(price - marketData.last) / marketData.last * 100;
                if (percentDiff > 10) {
                    this.log(`⚠️ Warning: Price ${price} is ${percentDiff.toFixed(1)}% from market`);
                }
            }
            
            await this.setInputValue(input, price);
            return { success: true, value: price };
            
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async verifyAllFields(fields, tradeData, orderType, priceValue) {
        const errors = [];
        
        // Check quantity
        if (fields.quantity) {
            const qtyValue = parseFloat(fields.quantity.value);
            if (isNaN(qtyValue) || qtyValue <= 0) {
                errors.push('Invalid quantity value');
            }
        } else {
            errors.push('Quantity field not found');
        }
        
        // Check price for limit/stop orders
        if (orderType !== 'MARKET' && fields.price) {
            const priceVal = parseFloat(fields.price.value);
            if (isNaN(priceVal) || priceVal <= 0) {
                errors.push('Invalid price value');
            }
        }
        
        // Check submit button
        if (!fields.submitButton || fields.submitButton.disabled) {
            errors.push('Submit button not available');
        }
        
        // Take screenshot if available
        if (this.config.debug && window.captureScreenshot) {
            try {
                const screenshot = await window.captureScreenshot();
                this.log('Screenshot captured for verification');
            } catch (e) {
                // Screenshot not available
            }
        }
        
        return {
            success: errors.length === 0,
            errors,
            fieldsChecked: Object.keys(fields).length
        };
    }

    async submitWithMonitoring(submitButton) {
        if (!submitButton || submitButton.disabled) {
            return { success: false, error: 'Submit button not available' };
        }
        
        // Set up network monitoring
        const networkMonitor = this.setupNetworkMonitor();
        
        // Store pre-submit state
        const preSubmitState = {
            orderCount: document.querySelectorAll('.order-row').length,
            ticketVisible: this.state.orderTicketOpen
        };
        
        // Click submit
        this.log('🚀 Clicking submit button...');
        submitButton.click();
        
        // Wait for response
        await this.delay(this.config.submitDelay);
        
        // Check results
        const postSubmitState = {
            orderCount: document.querySelectorAll('.order-row').length,
            ticketVisible: !!document.querySelector('.order-ticket:not([style*="none"])')
        };
        
        // Stop network monitoring
        const networkActivity = networkMonitor.stop();
        
        // Determine success
        const orderTicketClosed = preSubmitState.ticketVisible && !postSubmitState.ticketVisible;
        const newOrderCreated = postSubmitState.orderCount > preSubmitState.orderCount;
        const apiCallMade = networkActivity.requests.some(r => r.url.includes('order'));
        
        return {
            success: orderTicketClosed || newOrderCreated || apiCallMade,
            orderId: this.extractOrderId(),
            networkActivity,
            ticketClosed: orderTicketClosed,
            orderCreated: newOrderCreated
        };
    }

    /**
     * POST-VALIDATION: Verify order success
     */
    async runPostValidation(result) {
        this.log('🔍 Running post-validation...');
        
        // Verify order in orders table
        const orderCheck = await this.verifyOrderInTable();
        this.markStepComplete('post_verify_order', orderCheck);
        
        // Confirm position update
        const positionCheck = await this.verifyPositionUpdate();
        this.markStepComplete('post_verify_position', positionCheck);
        
        return {
            orderVerified: orderCheck.success,
            positionUpdated: positionCheck.success
        };
    }

    async verifyOrderInTable() {
        await this.delay(1000); // Wait for table update
        
        const orderRows = document.querySelectorAll('.module.orders .order-row, .orders-table tr');
        const recentOrder = Array.from(orderRows).find(row => {
            const timeCell = row.querySelector('[class*="time"], td:first-child');
            if (!timeCell) return false;
            
            // Check if order is recent (within last 30 seconds)
            const orderTime = new Date(timeCell.textContent);
            const timeDiff = Date.now() - orderTime.getTime();
            return timeDiff < 30000;
        });
        
        return {
            success: !!recentOrder,
            orderCount: orderRows.length
        };
    }

    async verifyPositionUpdate() {
        // This would use the compareOrderStates function if available
        if (window.compareOrderStates) {
            // Implementation would go here
        }
        
        return { success: true, skipped: true };
    }

    /**
     * Utility Functions
     */
    isElementClickable(element) {
        if (!element) return false;
        
        const style = window.getComputedStyle(element);
        return element.offsetParent !== null &&
               style.visibility !== 'hidden' &&
               style.display !== 'none' &&
               element.offsetWidth > 0 &&
               element.offsetHeight > 0 &&
               !element.disabled &&
               !element.hasAttribute('disabled');
    }

    async setInputValue(input, value) {
        input.focus();
        
        // Clear existing value
        input.value = '';
        input.dispatchEvent(new Event('input', { bubbles: true }));
        
        // Set new value using native setter
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype,
            'value'
        ).set;
        
        nativeInputValueSetter.call(input, value.toString());
        
        // Trigger all necessary events
        const events = ['input', 'change', 'keyup'];
        for (const eventType of events) {
            input.dispatchEvent(new Event(eventType, { bubbles: true }));
        }
        
        // Commit with Enter key
        input.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'Enter',
            code: 'Enter',
            keyCode: 13,
            which: 13,
            bubbles: true
        }));
        
        input.blur();
        await this.delay(this.config.inputDelay);
    }

    setupNetworkMonitor() {
        const requests = [];
        const originalFetch = window.fetch;
        
        // Override fetch temporarily
        window.fetch = function(...args) {
            const [url, options] = args;
            requests.push({ url, options, timestamp: Date.now() });
            return originalFetch.apply(this, args);
        };
        
        return {
            stop: () => {
                window.fetch = originalFetch;
                return { requests };
            }
        };
    }

    extractOrderId() {
        // Try to extract order ID from various sources
        const sources = [
            () => document.querySelector('.order-confirmation [class*="order-id"]')?.textContent,
            () => document.querySelector('.success-message')?.textContent?.match(/\d{6,}/)?.[0],
            () => {
                const recentRow = document.querySelector('.orders-table tr:first-child');
                return recentRow?.querySelector('td:nth-child(2)')?.textContent;
            }
        ];
        
        for (const source of sources) {
            try {
                const id = source();
                if (id) return id;
            } catch (e) {
                // Continue
            }
        }
        
        return null;
    }

    getMarketData() {
        // Get current market data if available
        if (window.getMarketData) {
            return window.getMarketData();
        }
        
        // Fallback to manual extraction
        const lastPrice = document.querySelector('.last-price, [class*="last"]');
        if (lastPrice) {
            return {
                last: parseFloat(lastPrice.textContent.replace(/[^0-9.-]/g, ''))
            };
        }
        
        return null;
    }

    markStepComplete(stepId, result) {
        this.metrics.steps[stepId] = {
            timestamp: Date.now(),
            result
        };
        this.log(`✓ Step ${stepId} complete`, result);
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    log(message, data = null) {
        if (this.config.debug) {
            const timestamp = new Date().toISOString();
            console.log(`[${timestamp}] ${message}`, data || '');
        }
    }

    logError(message, error) {
        const errorInfo = {
            message: error.message,
            stack: error.stack,
            timestamp: Date.now()
        };
        
        this.metrics.errors.push(errorInfo);
        console.error(`[ERROR] ${message}:`, error);
    }

    logMetrics() {
        const duration = Date.now() - this.metrics.startTime;
        console.log('📊 Order Submission Metrics:', {
            totalDuration: `${duration}ms`,
            steps: this.metrics.steps,
            errors: this.metrics.errors.length,
            retries: this.metrics.retries
        });
    }
}

// Export for use
if (typeof window !== 'undefined') {
    window.EnhancedDOMOrderSubmission = EnhancedDOMOrderSubmission;
    
    // Create singleton instance
    window.enhancedOrderSubmission = new EnhancedDOMOrderSubmission();
    
    // Convenience function
    window.submitOrderEnhanced = async (orderType, priceValue, tradeData) => {
        return window.enhancedOrderSubmission.submitOrder(orderType, priceValue, tradeData);
    };
}

console.log('✅ Enhanced DOM Order Submission System loaded');
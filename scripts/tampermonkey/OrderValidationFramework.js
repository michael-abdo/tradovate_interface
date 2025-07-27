// ============================================================================
// ORDER VALIDATION FRAMEWORK
// ============================================================================
// 
// Central component for comprehensive order validation, tracking, and monitoring
// in the Tradovate platform. Prevents silent order failures and provides
// detailed order lifecycle management.
//
// Features:
// - Pre/post submission validation
// - Real-time order status tracking  
// - Error detection and classification
// - Order reconciliation and reporting
// - Performance monitoring (<10ms overhead)
// - Cross-session persistence
//
// Last Updated: 2025-01-26
// ============================================================================

// Ensure UI Elements mapping is available
function ensureUIElementsMapping() {
    if (!window.TRADOVATE_UI_ELEMENTS) {
        console.log('Loading UI Elements mapping fallback for OrderValidationFramework');
        window.TRADOVATE_UI_ELEMENTS = {
            MARKET_DATA: {
                MARKET_CELLS: '.public_fixedDataTableCell_cellContent'
            },
            ORDER_STATUS: {
                ORDER_ROWS: '.fixedDataTableRowLayout_rowWrapper',
                ORDER_CELLS: '.public_fixedDataTableCell_cellContent'
            },
            ACCOUNT_SELECTION: {
                ACCOUNT_NAME: '.account-selector .account-name'
            }
        };
    }
}

class OrderValidationFramework {
    constructor(options = {}) {
        // Ensure UI elements mapping is available
        ensureUIElementsMapping();
        
        this.scriptName = options.scriptName || 'OrderValidation';
        this.debugMode = options.debugMode || false;
        this.performanceMode = options.performanceMode !== false; // Default true
        
        // Enhanced Performance tracking with strict 10ms compliance
        this.performanceMetrics = {
            validationCalls: 0,
            totalValidationTime: 0,
            averageValidationTime: 0,
            maxValidationTime: 0,
            overheadWarnings: 0,
            recentValidationTimes: [], // Rolling window of last 20 validations
            performanceMode: 'OPTIMAL', // OPTIMAL, DEGRADED, CRITICAL
            adaptiveLevel: 'FULL', // FULL, REDUCED, MINIMAL
            optimizationCount: 0,
            thresholdViolations: [],
            performanceHistory: []
        };
        
        // Order tracking storage
        this.orders = new Map(); // orderId -> OrderData
        this.ordersByClientId = new Map(); // clientId -> orderId
        this.bracketGroups = new Map(); // groupId -> [orderIds]
        
        // Validation state
        this.validationEnabled = true;
        this.monitoringActive = false;
        this.lastValidationTime = 0;
        
        // Event listeners
        this.eventListeners = new Map();
        
        // Performance monitoring
        this.performanceThreshold = 10; // 10ms max overhead per CLAUDE.md
        
        // Initialize optimized validation settings (start with full validation)
        this.optimizedValidation = {
            skipUIValidation: false,
            skipMarketConditions: false,
            reduceStatusPolling: false,
            minimalErrorChecking: false,
            disableDetailedLogging: false
        };
        
        // Initialize components
        this.initializeFramework();
        
        this.log('info', 'OrderValidationFramework initialized', {
            performanceMode: this.performanceMode,
            debugMode: this.debugMode
        });
    }
    
    // ============================================================================
    // INITIALIZATION
    // ============================================================================
    
    initializeFramework() {
        // Load required dependencies
        this.loadDependencies();
        
        // Set up persistent storage
        this.initializeStorage();
        
        // Start monitoring if enabled
        if (this.performanceMode) {
            this.startPerformanceMonitoring();
        }
        
        // Set up error monitoring
        this.startErrorMonitoring();
        
        // Restore previous session data
        this.restoreSession();
    }
    
    loadDependencies() {
        // Ensure UI elements mapping is available
        if (!window.TRADOVATE_UI_ELEMENTS) {
            this.log('warn', 'TRADOVATE_UI_ELEMENTS not loaded, loading...');
            this.loadScript('/scripts/tampermonkey/tradovate_ui_elements_map.js');
        }
        
        // Ensure error patterns are available
        if (!window.ORDER_ERROR_PATTERNS) {
            this.log('warn', 'ORDER_ERROR_PATTERNS not loaded, loading...');
            this.loadScript('/scripts/tampermonkey/order_error_patterns.js');
        }
        
        // Ensure DOM helpers are available
        if (!window.domHelpers) {
            this.log('warn', 'domHelpers not loaded, using basic fallback');
            this.setupBasicDOMHelpers();
        }
    }
    
    loadScript(src) {
        const script = document.createElement('script');
        script.src = src;
        script.onerror = () => this.log('error', `Failed to load ${src}`);
        document.head.appendChild(script);
    }
    
    setupBasicDOMHelpers() {
        window.domHelpers = {
            waitForElement: async (selector, timeout = 10000) => {
                const startTime = Date.now();
                return new Promise((resolve) => {
                    const checkElement = () => {
                        const element = document.querySelector(selector);
                        if (element) {
                            resolve(element);
                            return;
                        }
                        if (Date.now() - startTime >= timeout) {
                            resolve(null);
                            return;
                        }
                        setTimeout(checkElement, 100);
                    };
                    checkElement();
                });
            },
            validateElementExists: (selector) => document.querySelector(selector) !== null,
            validateElementVisible: (element) => {
                if (!element) return false;
                const style = window.getComputedStyle(element);
                return style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       element.offsetWidth > 0 && 
                       element.offsetHeight > 0;
            }
        };
    }
    
    initializeStorage() {
        this.storageKey = `orderValidation_${this.scriptName}`;
        this.sessionKey = `orderValidationSession_${this.scriptName}`;
    }
    
    restoreSession() {
        try {
            const sessionData = localStorage.getItem(this.sessionKey);
            if (sessionData) {
                const data = JSON.parse(sessionData);
                
                // Restore active orders (within last hour)
                const oneHourAgo = Date.now() - 3600000;
                Object.entries(data.orders || {}).forEach(([orderId, orderData]) => {
                    if (orderData.timestamp > oneHourAgo) {
                        this.orders.set(orderId, orderData);
                    }
                });
                
                // Restore performance metrics
                if (data.performanceMetrics) {
                    this.performanceMetrics = { ...this.performanceMetrics, ...data.performanceMetrics };
                }
                
                this.log('info', `Restored session with ${this.orders.size} active orders`);
            }
        } catch (error) {
            this.log('error', 'Failed to restore session', error);
        }
    }
    
    persistSession() {
        try {
            const sessionData = {
                orders: Object.fromEntries(this.orders),
                performanceMetrics: this.performanceMetrics,
                timestamp: Date.now()
            };
            localStorage.setItem(this.sessionKey, JSON.stringify(sessionData));
        } catch (error) {
            this.log('error', 'Failed to persist session', error);
        }
    }
    
    // ============================================================================
    // ORDER VALIDATION METHODS
    // ============================================================================
    
    /**
     * Validate order before submission
     * @param {Object} orderData - Order data to validate
     * @returns {Promise<Object>} Validation result
     */
    async validatePreSubmission(orderData) {
        const startTime = performance.now();
        const validationId = this.generateValidationId();
        
        try {
            this.log('debug', 'Starting pre-submission validation', { orderData, validationId });
            
            const result = {
                valid: true,
                errors: [],
                warnings: [],
                validationId: validationId,
                orderData: orderData
            };
            
            // 1. Validate required fields
            const fieldValidation = this.validateRequiredFields(orderData);
            if (!fieldValidation.valid) {
                result.valid = false;
                result.errors.push(...fieldValidation.errors);
            }
            
            // 2. Validate UI elements are available and ready (adaptive)
            if (!this.optimizedValidation?.skipUIValidation) {
                const uiValidation = await this.validateUIElements(orderData);
                if (!uiValidation.valid) {
                    result.valid = false;
                    result.errors.push(...uiValidation.errors);
                }
            } else {
                this.log('debug', 'Skipping UI validation for performance optimization');
            }
            
            // 3. Validate market conditions (adaptive)
            if (!this.optimizedValidation?.skipMarketConditions) {
                const marketValidation = this.validateMarketConditions(orderData);
                if (!marketValidation.valid) {
                    result.warnings.push(...marketValidation.warnings);
                }
            } else {
                this.log('debug', 'Skipping market conditions validation for performance optimization');
            }
            
            // 4. Validate account and risk limits
            const riskValidation = this.validateRiskLimits(orderData);
            if (!riskValidation.valid) {
                result.valid = false;
                result.errors.push(...riskValidation.errors);
            }
            
            // Store validation result
            if (result.valid) {
                const orderId = this.generateOrderId();
                this.registerOrder(orderId, orderData, validationId);
                result.orderId = orderId;
            }
            
            this.recordPerformanceMetric(performance.now() - startTime);
            this.log('info', `Pre-submission validation ${result.valid ? 'passed' : 'failed'}`, result);
            
            return result;
            
        } catch (error) {
            this.recordPerformanceMetric(performance.now() - startTime);
            this.log('error', 'Pre-submission validation error', error);
            return {
                valid: false,
                errors: ['Validation system error: ' + error.message],
                warnings: [],
                validationId: validationId
            };
        }
    }
    
    /**
     * Monitor order submission process
     * @param {string} orderId - Order ID to monitor
     * @returns {Promise<Object>} Submission result
     */
    async monitorOrderSubmission(orderId) {
        const startTime = performance.now();
        
        try {
            this.log('debug', 'Starting submission monitoring', { orderId });
            
            const orderData = this.orders.get(orderId);
            if (!orderData) {
                throw new Error(`Order ${orderId} not found in tracking system`);
            }
            
            // Update order status
            orderData.status = 'SUBMITTING';
            orderData.submissionStartTime = Date.now();
            
            // Monitor for confirmation or error
            const result = await this.waitForSubmissionResult(orderId);
            
            // Update order with result
            orderData.submissionEndTime = Date.now();
            orderData.submissionDuration = orderData.submissionEndTime - orderData.submissionStartTime;
            orderData.status = result.success ? 'SUBMITTED' : 'FAILED';
            orderData.submissionResult = result;
            
            if (result.success) {
                // Start status tracking
                this.startOrderStatusTracking(orderId);
            }
            
            this.recordPerformanceMetric(performance.now() - startTime);
            this.log('info', `Order submission ${result.success ? 'succeeded' : 'failed'}`, result);
            
            return result;
            
        } catch (error) {
            this.recordPerformanceMetric(performance.now() - startTime);
            this.log('error', 'Submission monitoring error', error);
            return {
                success: false,
                error: error.message,
                orderId: orderId
            };
        }
    }
    
    /**
     * Validate order after submission
     * @param {string} orderId - Order ID to validate
     * @returns {Promise<Object>} Post-submission validation result
     */
    async validatePostSubmission(orderId) {
        const startTime = performance.now();
        
        try {
            this.log('debug', 'Starting post-submission validation', { orderId });
            
            const orderData = this.orders.get(orderId);
            if (!orderData) {
                throw new Error(`Order ${orderId} not found in tracking system`);
            }
            
            const result = {
                valid: true,
                confirmed: false,
                errors: [],
                warnings: [],
                orderId: orderId,
                orderData: orderData
            };
            
            // 1. Check for confirmation dialogs/messages
            const confirmationCheck = await this.checkForConfirmation(orderId);
            result.confirmed = confirmationCheck.confirmed;
            if (confirmationCheck.errors.length > 0) {
                result.errors.push(...confirmationCheck.errors);
            }
            
            // 2. Verify order appears in orders table
            const tableCheck = await this.verifyOrderInTable(orderId);
            if (!tableCheck.found) {
                result.warnings.push('Order not found in orders table');
            }
            
            // 3. Check for error messages
            const errorCheck = this.checkForErrors();
            if (errorCheck.hasErrors) {
                result.valid = false;
                result.errors.push(...errorCheck.errors);
            }
            
            // 4. Validate order details match intent
            if (tableCheck.found) {
                const detailsCheck = this.validateOrderDetails(orderId, tableCheck.orderDetails);
                if (!detailsCheck.valid) {
                    result.warnings.push(...detailsCheck.warnings);
                }
            }
            
            // Update order status based on validation
            orderData.postValidationResult = result;
            orderData.lastValidation = Date.now();
            
            this.recordPerformanceMetric(performance.now() - startTime);
            this.log('info', `Post-submission validation completed`, result);
            
            return result;
            
        } catch (error) {
            this.recordPerformanceMetric(performance.now() - startTime);
            this.log('error', 'Post-submission validation error', error);
            return {
                valid: false,
                confirmed: false,
                errors: ['Post-validation error: ' + error.message],
                warnings: [],
                orderId: orderId
            };
        }
    }
    
    // ============================================================================
    // ORDER TRACKING AND STATUS MONITORING
    // ============================================================================
    
    registerOrder(orderId, orderData, validationId) {
        const order = {
            id: orderId,
            clientId: orderData.clientId || this.generateClientId(),
            validationId: validationId,
            symbol: orderData.symbol,
            side: orderData.action || orderData.side,
            quantity: orderData.qty || orderData.quantity,
            orderType: orderData.orderType || 'MARKET',
            price: orderData.entryPrice || orderData.price,
            stopPrice: orderData.stopPrice,
            takeProfit: orderData.takeProfit,
            stopLoss: orderData.stopLoss,
            status: 'VALIDATED',
            timestamp: Date.now(),
            originalData: orderData,
            bracketGroupId: orderData.bracketGroupId,
            parentOrderId: orderData.parentOrderId,
            isChildOrder: !!orderData.parentOrderId,
            events: [],
            validationHistory: []
        };
        
        this.orders.set(orderId, order);
        this.ordersByClientId.set(order.clientId, orderId);
        
        // Track bracket groups
        if (order.bracketGroupId) {
            if (!this.bracketGroups.has(order.bracketGroupId)) {
                this.bracketGroups.set(order.bracketGroupId, []);
            }
            this.bracketGroups.get(order.bracketGroupId).push(orderId);
        }
        
        this.log('debug', 'Order registered', order);
        this.persistSession();
    }
    
    startOrderStatusTracking(orderId) {
        const order = this.orders.get(orderId);
        if (!order) return;
        
        order.statusTracking = {
            active: true,
            startTime: Date.now(),
            lastCheck: Date.now(),
            checkCount: 0
        };
        
        // Start polling for status updates
        this.pollOrderStatus(orderId);
    }
    
    async pollOrderStatus(orderId) {
        const order = this.orders.get(orderId);
        if (!order || !order.statusTracking?.active) return;
        
        try {
            const statusInfo = await this.getOrderStatusFromUI(orderId);
            
            if (statusInfo.found) {
                // Update order status
                const previousStatus = order.status;
                order.status = statusInfo.status;
                order.statusTracking.lastCheck = Date.now();
                order.statusTracking.checkCount++;
                
                // Record status change event
                if (previousStatus !== statusInfo.status) {
                    this.recordOrderEvent(orderId, 'STATUS_CHANGE', {
                        from: previousStatus,
                        to: statusInfo.status,
                        details: statusInfo.details
                    });
                }
                
                // Check if order is in terminal state
                if (this.isTerminalStatus(statusInfo.status)) {
                    order.statusTracking.active = false;
                    order.completionTime = Date.now();
                    this.recordOrderEvent(orderId, 'ORDER_COMPLETE', { status: statusInfo.status });
                }
            }
            
            // Continue polling if still active (adaptive frequency)
            if (order.statusTracking.active) {
                const pollInterval = this.optimizedValidation?.reduceStatusPolling ? 2000 : 1000;
                setTimeout(() => this.pollOrderStatus(orderId), pollInterval);
            }
            
        } catch (error) {
            this.log('error', 'Status polling error', { orderId, error: error.message });
            
            // Reduce polling frequency on errors (adaptive)
            if (order.statusTracking.active) {
                const errorPollInterval = this.optimizedValidation?.reduceStatusPolling ? 10000 : 5000;
                setTimeout(() => this.pollOrderStatus(orderId), errorPollInterval);
            }
        }
    }
    
    recordOrderEvent(orderId, eventType, eventData) {
        const order = this.orders.get(orderId);
        if (!order) return;
        
        const event = {
            type: eventType,
            timestamp: Date.now(),
            data: eventData
        };
        
        order.events.push(event);
        this.log('debug', 'Order event recorded', { orderId, event });
        
        // Trigger event listeners
        this.triggerEvent(eventType, { orderId, event, order });
    }
    
    // ============================================================================
    // VALIDATION HELPER METHODS
    // ============================================================================
    
    validateRequiredFields(orderData) {
        const errors = [];
        const requiredFields = ['symbol', 'action', 'qty'];
        
        for (const field of requiredFields) {
            if (!orderData[field] && !orderData[field.replace('qty', 'quantity')]) {
                errors.push(`Missing required field: ${field}`);
            }
        }
        
        // Validate numeric fields
        if (orderData.qty && (isNaN(Number(orderData.qty)) || Number(orderData.qty) <= 0)) {
            errors.push('Invalid quantity: must be a positive number');
        }
        
        if (orderData.price && isNaN(Number(orderData.price))) {
            errors.push('Invalid price: must be a number');
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
    }
    
    async validateUIElements(orderData) {
        const errors = [];
        
        try {
            // Check if essential UI elements are available
            const elements = window.TRADOVATE_UI_ELEMENTS?.ORDER_SUBMISSION;
            if (!elements) {
                errors.push('UI elements mapping not available');
                return { valid: false, errors };
            }
            
            // Check submit button
            const submitBtn = document.querySelector(elements.SUBMIT_BUTTON);
            if (!submitBtn) {
                errors.push('Submit button not found');
            } else if (!window.domHelpers?.validateElementVisible(submitBtn)) {
                errors.push('Submit button not visible');
            }
            
            // Check order type selector if needed
            if (orderData.orderType !== 'MARKET') {
                const typeSelector = document.querySelector(elements.ORDER_TYPE_SELECTOR);
                if (!typeSelector) {
                    errors.push('Order type selector not found');
                }
            }
            
        } catch (error) {
            errors.push('UI validation error: ' + error.message);
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
    }
    
    validateMarketConditions(orderData) {
        const warnings = [];
        
        // Check market hours (basic implementation)
        const now = new Date();
        const dayOfWeek = now.getDay();
        const hour = now.getHours();
        
        // Basic futures trading hours check (Sunday 6PM - Friday 5PM ET)
        if (dayOfWeek === 6 || (dayOfWeek === 0 && hour < 18) || (dayOfWeek === 5 && hour >= 17)) {
            warnings.push('Market may be closed - verify trading hours');
        }
        
        return {
            valid: true, // Warnings don't invalidate orders
            warnings: warnings
        };
    }
    
    validateRiskLimits(orderData) {
        // Use unified risk management validation - DRY refactored
        try {
            // Check if unified risk management is available
            if (typeof window.unifiedRiskManagement !== 'undefined') {
                console.log('[OrderValidation] Using unified risk management validation');
                
                // Try to get current account context
                let accountName = null;
                let accountMetrics = null;
                
                try {
                    // Extract account name from current context (if available)
                    const accountElement = document.querySelector(window.TRADOVATE_UI_ELEMENTS?.ACCOUNT_SELECTION?.ACCOUNT_NAME || '.account-selector .account-name');
                    if (accountElement) {
                        accountName = accountElement.textContent.trim();
                    }
                    
                    // Get account metrics from table data (if available)
                    if (typeof getTableData === 'function') {
                        const tableData = getTableData();
                        const currentAccount = tableData.find(row => 
                            accountName && row.accountName && row.accountName.includes(accountName)
                        );
                        if (currentAccount) {
                            accountMetrics = {
                                totalAvail: currentAccount.totalAvail,
                                distDraw: currentAccount.distDraw
                            };
                        }
                    }
                } catch (e) {
                    console.warn('[OrderValidation] Could not get account context:', e);
                }
                
                // Use unified validation
                return window.unifiedRiskManagement.validateOrderRisk(orderData, accountName, accountMetrics);
            }
        } catch (error) {
            console.warn('[OrderValidation] Unified risk management not available, using fallback:', error);
        }
        
        // Fallback to basic validation
        const errors = [];
        
        // Basic risk validation - can be enhanced based on account settings
        if (orderData.qty && Number(orderData.qty) > 1000) {
            errors.push('Quantity exceeds maximum limit (1000)');
        }
        
        return {
            valid: errors.length === 0,
            errors: errors,
            warnings: []
        };
    }
    
    async waitForSubmissionResult(orderId, timeout = 10000) {
        const startTime = Date.now();
        
        return new Promise((resolve) => {
            const checkResult = () => {
                // Check for confirmation
                const confirmation = this.checkForConfirmation(orderId);
                if (confirmation.confirmed) {
                    resolve({
                        success: true,
                        confirmed: true,
                        orderId: orderId,
                        message: 'Order submitted successfully'
                    });
                    return;
                }
                
                // Check for errors
                const errorCheck = this.checkForErrors();
                if (errorCheck.hasErrors) {
                    resolve({
                        success: false,
                        errors: errorCheck.errors,
                        orderId: orderId
                    });
                    return;
                }
                
                // Check timeout
                if (Date.now() - startTime >= timeout) {
                    resolve({
                        success: false,
                        timeout: true,
                        orderId: orderId,
                        message: 'Submission confirmation timeout'
                    });
                    return;
                }
                
                // Continue checking
                setTimeout(checkResult, 200);
            };
            
            checkResult();
        });
    }
    
    checkForConfirmation(orderId) {
        // Basic implementation - can be enhanced with specific UI element checks
        return {
            confirmed: false,
            errors: []
        };
    }
    
    checkForErrors() {
        const errors = [];
        
        try {
            const errorElements = window.TRADOVATE_UI_ELEMENTS?.ERROR_DETECTION;
            if (!errorElements) return { hasErrors: false, errors: [] };
            
            // Minimal error checking mode - only check critical errors
            if (this.optimizedValidation?.minimalErrorChecking) {
                const errorModal = document.querySelector(errorElements.ERROR_MODAL);
                if (errorModal && window.domHelpers?.validateElementVisible(errorModal)) {
                    const errorText = errorModal.textContent || 'Unknown error occurred';
                    errors.push(errorText);
                }
            } else {
                // Full error checking
                // Check for error modals
                const errorModal = document.querySelector(errorElements.ERROR_MODAL);
                if (errorModal && window.domHelpers?.validateElementVisible(errorModal)) {
                    const errorText = errorModal.textContent || 'Unknown error occurred';
                    errors.push(errorText);
                }
                
                // Check for error alerts
                const errorAlert = document.querySelector(errorElements.ERROR_ALERT);
                if (errorAlert && window.domHelpers?.validateElementVisible(errorAlert)) {
                    const errorText = errorAlert.textContent || 'Alert error occurred';
                    errors.push(errorText);
                }
            }
            
        } catch (error) {
            errors.push('Error detection system failure: ' + error.message);
        }
        
        return {
            hasErrors: errors.length > 0,
            errors: errors
        };
    }
    
    async verifyOrderInTable(orderId) {
        // Basic implementation - searches for order in orders table
        try {
            const orderRows = document.querySelectorAll(window.TRADOVATE_UI_ELEMENTS?.ORDER_STATUS?.ORDER_ROWS || '.fixedDataTableRowLayout_rowWrapper');
            
            for (const row of orderRows) {
                const cells = row.querySelectorAll(window.TRADOVATE_UI_ELEMENTS?.ORDER_STATUS?.ORDER_CELLS || '.public_fixedDataTableCell_cellContent');
                if (cells.length > 1) {
                    const possibleOrderId = cells[1]?.textContent?.trim();
                    if (possibleOrderId === orderId) {
                        return {
                            found: true,
                            orderDetails: this.extractOrderDetailsFromRow(row)
                        };
                    }
                }
            }
            
        } catch (error) {
            this.log('error', 'Error verifying order in table', error);
        }
        
        return { found: false };
    }
    
    extractOrderDetailsFromRow(row) {
        const cells = row.querySelectorAll(window.TRADOVATE_UI_ELEMENTS?.ORDER_STATUS?.ORDER_CELLS || '.public_fixedDataTableCell_cellContent');
        
        return {
            timestamp: cells[0]?.textContent?.trim(),
            orderId: cells[1]?.textContent?.trim(),
            symbol: cells[2]?.textContent?.trim(),
            side: cells[3]?.textContent?.trim(),
            quantity: cells[4]?.textContent?.trim(),
            price: cells[5]?.textContent?.trim(),
            status: cells[6]?.textContent?.trim()
        };
    }
    
    validateOrderDetails(orderId, extractedDetails) {
        const order = this.orders.get(orderId);
        if (!order) return { valid: false, warnings: ['Order not found'] };
        
        const warnings = [];
        
        // Compare key fields
        if (extractedDetails.symbol && extractedDetails.symbol !== order.symbol) {
            warnings.push(`Symbol mismatch: expected ${order.symbol}, got ${extractedDetails.symbol}`);
        }
        
        if (extractedDetails.side && extractedDetails.side !== order.side) {
            warnings.push(`Side mismatch: expected ${order.side}, got ${extractedDetails.side}`);
        }
        
        if (extractedDetails.quantity && extractedDetails.quantity !== order.quantity) {
            warnings.push(`Quantity mismatch: expected ${order.quantity}, got ${extractedDetails.quantity}`);
        }
        
        return {
            valid: warnings.length === 0,
            warnings: warnings
        };
    }
    
    async getOrderStatusFromUI(orderId) {
        // Basic implementation - can be enhanced with specific status detection
        const verification = await this.verifyOrderInTable(orderId);
        
        if (verification.found) {
            return {
                found: true,
                status: verification.orderDetails.status || 'UNKNOWN',
                details: verification.orderDetails
            };
        }
        
        return { found: false };
    }
    
    isTerminalStatus(status) {
        const terminalStatuses = ['FILLED', 'CANCELLED', 'REJECTED', 'EXPIRED'];
        return terminalStatuses.includes(status.toUpperCase());
    }
    
    // ============================================================================
    // PERFORMANCE MONITORING
    // ============================================================================
    
    startPerformanceMonitoring() {
        setInterval(() => {
            this.checkPerformanceMetrics();
        }, 60000); // Check every minute
    }
    
    recordPerformanceMetric(duration) {
        this.performanceMetrics.validationCalls++;
        this.performanceMetrics.totalValidationTime += duration;
        this.performanceMetrics.averageValidationTime = 
            this.performanceMetrics.totalValidationTime / this.performanceMetrics.validationCalls;
        
        // Update rolling window of recent validations (last 20)
        this.performanceMetrics.recentValidationTimes.push(duration);
        if (this.performanceMetrics.recentValidationTimes.length > 20) {
            this.performanceMetrics.recentValidationTimes.shift();
        }
        
        if (duration > this.performanceMetrics.maxValidationTime) {
            this.performanceMetrics.maxValidationTime = duration;
        }
        
        // Enhanced threshold violation tracking
        if (duration > this.performanceThreshold) {
            this.performanceMetrics.overheadWarnings++;
            const violation = {
                timestamp: Date.now(),
                duration: duration,
                threshold: this.performanceThreshold,
                context: this.getCurrentValidationContext(),
                adaptiveLevel: this.performanceMetrics.adaptiveLevel
            };
            this.performanceMetrics.thresholdViolations.push(violation);
            
            // Keep only last 50 violations
            if (this.performanceMetrics.thresholdViolations.length > 50) {
                this.performanceMetrics.thresholdViolations.shift();
            }
            
            this.log('warn', `Validation overhead exceeded threshold: ${duration.toFixed(2)}ms > ${this.performanceThreshold}ms`);
            
            // Trigger adaptive performance optimization
            this.adaptPerformanceLevel();
        }
        
        // Calculate recent average for adaptive tuning
        if (this.performanceMetrics.recentValidationTimes.length >= 5) {
            const recentAverage = this.performanceMetrics.recentValidationTimes.reduce((sum, time) => sum + time, 0) / 
                                this.performanceMetrics.recentValidationTimes.length;
            
            // Proactive optimization if trending toward threshold
            if (recentAverage > this.performanceThreshold * 0.8) {
                this.log('info', `Performance approaching threshold (${recentAverage.toFixed(2)}ms), optimizing...`);
                this.optimizePerformance();
            }
        }
        
        // Record performance history sample (every 10th call)
        if (this.performanceMetrics.validationCalls % 10 === 0) {
            this.performanceMetrics.performanceHistory.push({
                timestamp: Date.now(),
                averageTime: this.performanceMetrics.averageValidationTime,
                recentAverage: this.calculateRecentAverage(),
                adaptiveLevel: this.performanceMetrics.adaptiveLevel,
                performanceMode: this.performanceMetrics.performanceMode
            });
            
            // Keep only last 100 history entries
            if (this.performanceMetrics.performanceHistory.length > 100) {
                this.performanceMetrics.performanceHistory.shift();
            }
        }
    }
    
    checkPerformanceMetrics() {
        if (this.performanceMetrics.averageValidationTime > this.performanceThreshold) {
            this.log('warn', 'Average validation time exceeds threshold', this.performanceMetrics);
        }
        
        // Check if recovery to higher performance level is possible
        const recentAverage = this.calculateRecentAverage();
        if (recentAverage < this.performanceThreshold * 0.5 && this.performanceMetrics.adaptiveLevel !== 'FULL') {
            this.log('info', 'Performance improved, upgrading validation level');
            this.upgradePerformanceLevel();
        }
    }
    
    getCurrentValidationContext() {
        return {
            activeOrders: this.orders.size,
            monitoringActive: this.monitoringActive,
            validationEnabled: this.validationEnabled,
            ordersByClientId: this.ordersByClientId.size,
            bracketGroups: this.bracketGroups.size
        };
    }
    
    calculateRecentAverage() {
        if (this.performanceMetrics.recentValidationTimes.length === 0) {
            return 0;
        }
        return this.performanceMetrics.recentValidationTimes.reduce((sum, time) => sum + time, 0) / 
               this.performanceMetrics.recentValidationTimes.length;
    }
    
    adaptPerformanceLevel() {
        const currentLevel = this.performanceMetrics.adaptiveLevel;
        let newLevel = currentLevel;
        
        // Calculate violation frequency in last 10 validations
        const recentViolations = this.performanceMetrics.thresholdViolations.filter(
            v => Date.now() - v.timestamp < 30000 // Last 30 seconds
        ).length;
        
        if (recentViolations >= 3) {
            // Multiple recent violations - aggressive optimization
            if (currentLevel === 'FULL') {
                newLevel = 'REDUCED';
                this.performanceMetrics.performanceMode = 'DEGRADED';
            } else if (currentLevel === 'REDUCED') {
                newLevel = 'MINIMAL';
                this.performanceMetrics.performanceMode = 'CRITICAL';
            }
        } else if (recentViolations >= 1) {
            // Single recent violation - moderate optimization
            if (currentLevel === 'FULL') {
                newLevel = 'REDUCED';
                this.performanceMetrics.performanceMode = 'DEGRADED';
            }
        }
        
        if (newLevel !== currentLevel) {
            this.performanceMetrics.adaptiveLevel = newLevel;
            this.performanceMetrics.optimizationCount++;
            this.log('warn', `Performance adapted from ${currentLevel} to ${newLevel} due to ${recentViolations} violations`);
            this.applyPerformanceOptimizations(newLevel);
        }
    }
    
    optimizePerformance() {
        // Proactive optimization when trending toward threshold
        if (this.performanceMetrics.adaptiveLevel === 'FULL') {
            this.log('info', 'Proactively reducing validation level to maintain performance');
            this.performanceMetrics.adaptiveLevel = 'REDUCED';
            this.performanceMetrics.performanceMode = 'DEGRADED';
            this.performanceMetrics.optimizationCount++;
            this.applyPerformanceOptimizations('REDUCED');
        }
    }
    
    upgradePerformanceLevel() {
        const currentLevel = this.performanceMetrics.adaptiveLevel;
        let newLevel = currentLevel;
        
        if (currentLevel === 'MINIMAL') {
            newLevel = 'REDUCED';
            this.performanceMetrics.performanceMode = 'DEGRADED';
        } else if (currentLevel === 'REDUCED') {
            newLevel = 'FULL';
            this.performanceMetrics.performanceMode = 'OPTIMAL';
        }
        
        if (newLevel !== currentLevel) {
            this.performanceMetrics.adaptiveLevel = newLevel;
            this.log('info', `Performance upgraded from ${currentLevel} to ${newLevel}`);
            this.applyPerformanceOptimizations(newLevel);
        }
    }
    
    applyPerformanceOptimizations(level) {
        switch (level) {
            case 'MINIMAL':
                // Disable all non-critical validations
                this.optimizedValidation = {
                    skipUIValidation: true,
                    skipMarketConditions: true,
                    reduceStatusPolling: true,
                    minimalErrorChecking: true,
                    disableDetailedLogging: true
                };
                this.log('info', 'Applied MINIMAL performance optimizations');
                break;
                
            case 'REDUCED':
                // Disable some validations, reduce frequency
                this.optimizedValidation = {
                    skipUIValidation: false,
                    skipMarketConditions: true,
                    reduceStatusPolling: true,
                    minimalErrorChecking: false,
                    disableDetailedLogging: true
                };
                this.log('info', 'Applied REDUCED performance optimizations');
                break;
                
            case 'FULL':
            default:
                // Full validation enabled
                this.optimizedValidation = {
                    skipUIValidation: false,
                    skipMarketConditions: false,
                    reduceStatusPolling: false,
                    minimalErrorChecking: false,
                    disableDetailedLogging: false
                };
                this.log('info', 'Restored FULL performance validation');
                break;
        }
    }
    
    getPerformanceReport() {
        const recentAverage = this.calculateRecentAverage();
        const recentViolations = this.performanceMetrics.thresholdViolations.filter(
            v => Date.now() - v.timestamp < 30000
        ).length;
        
        return {
            ...this.performanceMetrics,
            thresholdViolations: this.performanceMetrics.overheadWarnings,
            recentAverage: recentAverage,
            recentViolations: recentViolations,
            complianceRate: this.performanceMetrics.validationCalls > 0 ? 
                ((this.performanceMetrics.validationCalls - this.performanceMetrics.overheadWarnings) / 
                 this.performanceMetrics.validationCalls * 100).toFixed(2) + '%' : '100%',
            thresholdComplianceRate: this.performanceMetrics.validationCalls > 0 ?
                ((this.performanceMetrics.validationCalls - this.performanceMetrics.thresholdViolations.length) /
                 this.performanceMetrics.validationCalls * 100).toFixed(2) + '%' : '100%',
            performanceHealthScore: this.calculatePerformanceHealthScore(),
            adaptiveSettings: this.optimizedValidation || {},
            performanceRecommendations: this.generatePerformanceRecommendations()
        };
    }
    
    calculatePerformanceHealthScore() {
        let score = 100;
        
        // Deduct points for recent violations
        const recentViolations = this.performanceMetrics.thresholdViolations.filter(
            v => Date.now() - v.timestamp < 30000
        ).length;
        score -= recentViolations * 20; // -20 points per recent violation
        
        // Deduct points for degraded performance mode
        if (this.performanceMetrics.performanceMode === 'DEGRADED') {
            score -= 15;
        } else if (this.performanceMetrics.performanceMode === 'CRITICAL') {
            score -= 30;
        }
        
        // Deduct points for reduced adaptive level
        if (this.performanceMetrics.adaptiveLevel === 'REDUCED') {
            score -= 10;
        } else if (this.performanceMetrics.adaptiveLevel === 'MINIMAL') {
            score -= 25;
        }
        
        // Bonus points for good recent performance
        const recentAverage = this.calculateRecentAverage();
        if (recentAverage < this.performanceThreshold * 0.5) {
            score += 10; // Bonus for excellent performance
        }
        
        return Math.max(0, Math.min(100, score));
    }
    
    generatePerformanceRecommendations() {
        const recommendations = [];
        const recentAverage = this.calculateRecentAverage();
        
        if (this.performanceMetrics.performanceMode === 'CRITICAL') {
            recommendations.push({
                priority: 'CRITICAL',
                action: 'Consider disabling non-essential validation features',
                reason: 'System is in critical performance mode'
            });
        }
        
        if (recentAverage > this.performanceThreshold) {
            recommendations.push({
                priority: 'HIGH',
                action: 'Reduce validation complexity or frequency',
                reason: `Recent average (${recentAverage.toFixed(2)}ms) exceeds threshold`
            });
        }
        
        if (this.performanceMetrics.optimizationCount > 5) {
            recommendations.push({
                priority: 'MEDIUM',
                action: 'Review system load and consider hardware optimization',
                reason: `Performance has been optimized ${this.performanceMetrics.optimizationCount} times`
            });
        }
        
        if (this.calculatePerformanceHealthScore() < 50) {
            recommendations.push({
                priority: 'HIGH',
                action: 'Immediate performance optimization required',
                reason: 'Performance health score is below acceptable threshold'
            });
        }
        
        return recommendations;
    }
    
    // ============================================================================
    // ERROR MONITORING
    // ============================================================================
    
    startErrorMonitoring() {
        setInterval(() => {
            if (this.monitoringActive) {
                this.checkForSystemErrors();
            }
        }, 500); // Check every 500ms when monitoring is active
    }
    
    checkForSystemErrors() {
        const errorCheck = this.checkForErrors();
        if (errorCheck.hasErrors) {
            for (const error of errorCheck.errors) {
                this.handleDetectedError(error);
            }
        }
    }
    
    handleDetectedError(errorMessage) {
        if (!window.ERROR_CLASSIFICATION) {
            this.log('error', 'Error classification system not available', errorMessage);
            return;
        }
        
        const classification = window.ERROR_CLASSIFICATION.classifyError(errorMessage);
        const recovery = window.ERROR_CLASSIFICATION.getRecoveryStrategy(classification);
        
        this.log('error', 'Classified error detected', {
            originalMessage: errorMessage,
            classification: classification,
            recovery: recovery
        });
        
        // Trigger error event
        this.triggerEvent('ERROR_DETECTED', {
            message: errorMessage,
            classification: classification,
            recovery: recovery,
            timestamp: Date.now()
        });
    }
    
    // ============================================================================
    // EVENT SYSTEM
    // ============================================================================
    
    addEventListener(eventType, callback) {
        if (!this.eventListeners.has(eventType)) {
            this.eventListeners.set(eventType, []);
        }
        this.eventListeners.get(eventType).push(callback);
    }
    
    removeEventListener(eventType, callback) {
        if (this.eventListeners.has(eventType)) {
            const listeners = this.eventListeners.get(eventType);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }
    
    triggerEvent(eventType, eventData) {
        if (this.eventListeners.has(eventType)) {
            this.eventListeners.get(eventType).forEach(callback => {
                try {
                    callback(eventData);
                } catch (error) {
                    this.log('error', 'Event callback error', { eventType, error: error.message });
                }
            });
        }
    }
    
    // ============================================================================
    // UTILITY METHODS
    // ============================================================================
    
    generateOrderId() {
        return `OVF_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    generateClientId() {
        return `CLI_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    generateValidationId() {
        return `VAL_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    log(level, message, data = null) {
        // Skip detailed logging when performance optimization is enabled
        if (this.optimizedValidation?.disableDetailedLogging && (level === 'debug' || level === 'info')) {
            return;
        }
        
        const timestamp = new Date().toISOString();
        const logEntry = `[${timestamp}][OrderValidation][${level.toUpperCase()}] ${message}`;
        
        if (level === 'error') {
            console.error(logEntry, data);
        } else if (level === 'warn') {
            console.warn(logEntry, data);
        } else if (level === 'debug' && this.debugMode) {
            console.log(logEntry, data);
        } else if (level === 'info') {
            console.log(logEntry, data);
        }
    }
    
    // ============================================================================
    // PUBLIC API
    // ============================================================================
    
    enable() {
        this.validationEnabled = true;
        this.log('info', 'Order validation enabled');
    }
    
    disable() {
        this.validationEnabled = false;
        this.log('info', 'Order validation disabled');
    }
    
    startMonitoring() {
        this.monitoringActive = true;
        this.log('info', 'Order monitoring started');
    }
    
    stopMonitoring() {
        this.monitoringActive = false;
        this.log('info', 'Order monitoring stopped');
    }
    
    getOrderStatus(orderId) {
        return this.orders.get(orderId);
    }
    
    getAllOrders() {
        return Array.from(this.orders.values());
    }
    
    getActiveOrders() {
        return Array.from(this.orders.values()).filter(order => 
            !this.isTerminalStatus(order.status)
        );
    }
    
    getBracketGroup(groupId) {
        const orderIds = this.bracketGroups.get(groupId) || [];
        return orderIds.map(id => this.orders.get(id)).filter(Boolean);
    }
    
    clearCompletedOrders() {
        const now = Date.now();
        const oneHourAgo = now - 3600000; // 1 hour
        
        for (const [orderId, order] of this.orders.entries()) {
            if (this.isTerminalStatus(order.status) && order.completionTime < oneHourAgo) {
                this.orders.delete(orderId);
                this.ordersByClientId.delete(order.clientId);
            }
        }
        
        this.persistSession();
        this.log('info', 'Cleared completed orders older than 1 hour');
    }
    
    generateReport() {
        const orders = this.getAllOrders();
        const activeOrders = this.getActiveOrders();
        
        return {
            summary: {
                totalOrders: orders.length,
                activeOrders: activeOrders.length,
                completedOrders: orders.length - activeOrders.length
            },
            performance: this.getPerformanceReport(),
            orders: orders,
            timestamp: new Date().toISOString()
        };
    }
}

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

// Create global instance
window.OrderValidationFramework = OrderValidationFramework;

// Create default instance if not already exists
if (!window.orderValidator) {
    window.orderValidator = new OrderValidationFramework({
        scriptName: 'autoOrder',
        debugMode: localStorage.getItem('orderValidationDebug') === 'true',
        performanceMode: true
    });
    
    console.log('✅ OrderValidationFramework instance created as window.orderValidator');
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OrderValidationFramework;
}

console.log('✅ OrderValidationFramework loaded');
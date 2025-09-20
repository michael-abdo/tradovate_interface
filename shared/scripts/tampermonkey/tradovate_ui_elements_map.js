// ============================================================================
// TRADOVATE UI ELEMENTS MAPPING FOR ORDER VALIDATION
// ============================================================================
// 
// This file documents all UI elements needed for comprehensive order validation
// in the Tradovate platform. Used by the Order Validation Framework.
//
// Last Updated: 2025-01-26
// ============================================================================

const TRADOVATE_UI_ELEMENTS = {
    
    // ============================================================================
    // ORDER SUBMISSION ELEMENTS
    // ============================================================================
    ORDER_SUBMISSION: {
        // Order type selector
        ORDER_TYPE_SELECTOR: '.group.order-type .select-input div[tabindex]',
        ORDER_TYPE_DROPDOWN: 'ul.dropdown-menu li',
        
        // Price input fields
        PRICE_INPUT: '.numeric-input.feedback-wrapper input',
        PRICE_INPUT_ALT: 'input.form-control',
        
        // Quantity input
        QUANTITY_INPUT: '.select-input.combobox input',
        
        // Action buttons (Buy/Sell)
        ACTION_BUTTONS: '.radio-group.btn-group label',
        
        // Submit button - CRITICAL
        SUBMIT_BUTTON: '.btn-group .btn-primary',
        SUBMIT_BUTTON_ALT: 'button[type="submit"]',
        
        // Navigation
        BACK_BUTTON: '.icon.icon-back',
        BACK_BUTTON_ALT: '.navigation-back'
    },
    
    // ============================================================================
    // ORDER CONFIRMATION ELEMENTS
    // ============================================================================
    ORDER_CONFIRMATION: {
        // Success confirmation dialogs
        SUCCESS_MODAL: '.modal.confirmation-dialog',
        SUCCESS_MESSAGE: '.alert.alert-success',
        CONFIRMATION_TEXT: '.confirmation-message',
        
        // Order ID displays
        ORDER_ID_DISPLAY: '.order-id',
        ORDER_NUMBER: '.order-number',
        
        // Confirmation buttons
        OK_BUTTON: '.modal-footer .btn-primary',
        CLOSE_BUTTON: '.modal-header .close',
        DISMISS_BUTTON: '[data-dismiss="modal"]'
    },
    
    // ============================================================================
    // ORDER STATUS INDICATORS
    // ============================================================================
    ORDER_STATUS: {
        // Order tables and lists
        ORDERS_TABLE: '.module.orders .data-table',
        ORDERS_TABLE_ALT: '.orders-grid',
        ORDER_ROWS: '.fixedDataTableRowLayout_rowWrapper',
        ORDER_CELLS: '.public_fixedDataTableCell_cellContent',
        
        // Order history
        ORDER_HISTORY: '.order-history-content',
        ORDER_HISTORY_ROWS: '.order-history-content .public_fixedDataTable_bodyRow',
        
        // Status indicators
        ORDER_STATUS_PENDING: '.status-pending',
        ORDER_STATUS_FILLED: '.status-filled',
        ORDER_STATUS_CANCELLED: '.status-cancelled',
        ORDER_STATUS_REJECTED: '.status-rejected',
        
        // Position updates
        POSITIONS_TABLE: '.module.positions.data-table',
        POSITION_ROWS: '.positions .fixedDataTableRowLayout_rowWrapper',
        
        // Account balance updates
        ACCOUNT_BALANCE: '.account-balance',
        MARGIN_AVAILABLE: '.margin-available',
        PNL_DISPLAY: '.pnl-display'
    },
    
    // ============================================================================
    // ERROR AND FAILURE ELEMENTS
    // ============================================================================
    ERROR_DETECTION: {
        // Error modals and alerts
        ERROR_MODAL: '.modal.error-dialog',
        ERROR_ALERT: '.alert.alert-danger',
        ERROR_MESSAGE: '.error-message',
        WARNING_ALERT: '.alert.alert-warning',
        
        // Specific error types
        INSUFFICIENT_FUNDS: '[data-error="insufficient-funds"]',
        MARKET_CLOSED: '[data-error="market-closed"]',
        INVALID_SYMBOL: '[data-error="invalid-symbol"]',
        CONNECTION_ERROR: '[data-error="connection"]',
        
        // Input validation errors
        FIELD_ERROR: '.field-error',
        VALIDATION_ERROR: '.validation-error',
        INPUT_ERROR: '.input-error',
        
        // General error indicators
        ERROR_ICON: '.icon-error',
        WARNING_ICON: '.icon-warning',
        DANGER_BUTTON: '.btn.btn-danger'
    },
    
    // ============================================================================
    // LOADING AND PROCESSING STATES
    // ============================================================================
    LOADING_STATES: {
        // Loading indicators
        SPINNER: '.spinner',
        LOADING_OVERLAY: '.loading-overlay',
        PROCESSING: '.processing',
        
        // Disabled states during processing
        DISABLED_INPUT: 'input[disabled]',
        DISABLED_BUTTON: 'button[disabled]',
        
        // Progress indicators
        PROGRESS_BAR: '.progress-bar',
        PROGRESS_INDICATOR: '.progress-indicator'
    },
    
    // ============================================================================
    // MARKET DATA ELEMENTS  
    // ============================================================================
    MARKET_DATA: {
        // Symbol displays
        SYMBOL_DISPLAY: '.symbol-main',
        SYMBOL_ALT: '.contract-symbol span',
        
        // Price displays
        BID_PRICE: '.bid-price',
        OFFER_PRICE: '.offer-price',
        LAST_PRICE: '.last-price',
        
        // Market data tables
        MARKET_TABLE: '.public_fixedDataTable_main',
        MARKET_ROWS: '.fixedDataTableRowLayout_rowWrapper',
        MARKET_CELLS: '.public_fixedDataTableCell_cellContent'
    },
    
    // ============================================================================
    // ACCOUNT SELECTION ELEMENTS
    // ============================================================================
    ACCOUNT_SELECTION: {
        // Account selector dropdown
        ACCOUNT_DROPDOWN: '.pane.account-selector.dropdown [data-toggle="dropdown"]',
        ACCOUNT_MENU: '.dropdown-menu li a.account',
        ACCOUNT_SELECTED: '.account-selected',
        
        // Account information
        ACCOUNT_NAME: '.account-name',
        ACCOUNT_BALANCE: '.account-balance',
        ACCOUNT_MARGIN: '.account-margin'
    },
    
    // ============================================================================
    // BRACKET ORDER SPECIFIC ELEMENTS
    // ============================================================================
    BRACKET_ORDERS: {
        // Parent order indicators
        PARENT_ORDER: '.parent-order',
        CHILD_ORDERS: '.child-orders',
        
        // TP/SL indicators
        TAKE_PROFIT_ORDER: '.take-profit',
        STOP_LOSS_ORDER: '.stop-loss',
        
        // Bracket status
        BRACKET_COMPLETE: '.bracket-complete',
        BRACKET_PARTIAL: '.bracket-partial'
    },
    
    // ============================================================================
    // UNIFIED TRADING DATA PROCESSING FUNCTIONS
    // ============================================================================
    TRADING_DATA_PROCESSORS: {
        // Symbol processing functions - eliminates duplication across autoOrder scripts
        
        normalizeSymbol: function(s) {
            console.log(`normalizeSymbol called with: "${s}"`);
            const isRootSymbol = /^[A-Z]{1,3}$/.test(s);
            console.log(`Is root symbol: ${isRootSymbol}`);
            const result = isRootSymbol ? TRADOVATE_UI_ELEMENTS.TRADING_DATA_PROCESSORS.getFrontQuarter(s) : s.toUpperCase();
            console.log(`Normalized symbol: "${result}"`);
            return result;
        },
        
        getFrontQuarter: function(root) {
            console.log(`getFrontQuarter called for root: "${root}"`);
            const { letter, yearDigit } = TRADOVATE_UI_ELEMENTS.TRADING_DATA_PROCESSORS.getQuarterlyCode();
            console.log(`Got quarterly code: letter=${letter}, yearDigit=${yearDigit}`);
            const result = `${root.toUpperCase()}${letter}${yearDigit}`;
            console.log(`Returning front quarter symbol: "${result}"`);
            return result;
        },
        
        getQuarterlyCode: function() {
            const MONTH_CODES = {
                0: 'F', 1: 'G', 2: 'H', 3: 'J', 4: 'K', 5: 'M',
                6: 'N', 7: 'Q', 8: 'U', 9: 'V', 10: 'X', 11: 'Z'
            };
            
            const now = new Date();
            const month = now.getMonth();
            const year = now.getFullYear();
            const letter = MONTH_CODES[month];
            const yearDigit = year % 10;
            
            return { letter, yearDigit };
        },
        
        // Symbol validation and formatting
        validateSymbol: function(symbol) {
            if (!symbol || typeof symbol !== 'string') {
                return false;
            }
            
            // Check if it's a valid futures symbol format
            const rootPattern = /^[A-Z]{1,3}$/;
            const fullPattern = /^[A-Z]{1,3}[A-Z]\d$/;
            
            return rootPattern.test(symbol) || fullPattern.test(symbol);
        },
        
        extractRootSymbol: function(symbol) {
            if (!symbol) return null;
            
            // Extract root symbol from full futures symbol (e.g., ESH5 -> ES)
            const match = symbol.match(/^([A-Z]{1,3})[A-Z]?\d?$/);
            return match ? match[1] : symbol.toUpperCase();
        }
    },
    
    // ============================================================================
    // VALIDATION HELPER FUNCTIONS
    // ============================================================================
    VALIDATION_HELPERS: {
        // Functions to check element states
        isElementVisible: (element) => {
            if (!element) return false;
            const style = window.getComputedStyle(element);
            return style.display !== 'none' && 
                   style.visibility !== 'hidden' && 
                   element.offsetWidth > 0 && 
                   element.offsetHeight > 0;
        },
        
        isElementEnabled: (element) => {
            return element && !element.disabled && !element.hasAttribute('disabled');
        },
        
        isElementClickable: (element) => {
            return TRADOVATE_UI_ELEMENTS.VALIDATION_HELPERS.isElementVisible(element) && 
                   TRADOVATE_UI_ELEMENTS.VALIDATION_HELPERS.isElementEnabled(element);
        },
        
        waitForElement: async (selector, timeout = 10000) => {
            const startTime = Date.now();
            return new Promise((resolve) => {
                const checkElement = () => {
                    const element = document.querySelector(selector);
                    if (element && TRADOVATE_UI_ELEMENTS.VALIDATION_HELPERS.isElementVisible(element)) {
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
        
        // Extract order information from UI elements
        extractOrderFromRow: (row) => {
            const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
            if (cells.length < 6) return null;
            
            return {
                timestamp: cells[0]?.textContent.trim(),
                orderId: cells[1]?.textContent.trim(),
                symbol: cells[2]?.textContent.trim(),
                side: cells[3]?.textContent.trim(),
                quantity: cells[4]?.textContent.trim(),
                price: cells[5]?.textContent.trim(),
                status: cells[6]?.textContent.trim()
            };
        },
        
        // Check for error states
        hasErrors: () => {
            const errorSelectors = [
                TRADOVATE_UI_ELEMENTS.ERROR_DETECTION.ERROR_MODAL,
                TRADOVATE_UI_ELEMENTS.ERROR_DETECTION.ERROR_ALERT,
                TRADOVATE_UI_ELEMENTS.ERROR_DETECTION.ERROR_MESSAGE
            ];
            
            return errorSelectors.some(selector => 
                document.querySelector(selector) !== null
            );
        },
        
        // Get current loading state
        isLoading: () => {
            const loadingSelectors = [
                TRADOVATE_UI_ELEMENTS.LOADING_STATES.SPINNER,
                TRADOVATE_UI_ELEMENTS.LOADING_STATES.LOADING_OVERLAY,
                TRADOVATE_UI_ELEMENTS.LOADING_STATES.PROCESSING
            ];
            
            return loadingSelectors.some(selector => {
                const element = document.querySelector(selector);
                return element && TRADOVATE_UI_ELEMENTS.VALIDATION_HELPERS.isElementVisible(element);
            });
        }
    }
};

// ============================================================================
// ORDER VALIDATION PATTERNS
// ============================================================================

const ORDER_VALIDATION_PATTERNS = {
    // Text patterns for order confirmation
    CONFIRMATION_PATTERNS: [
        /order\s+submitted/i,
        /order\s+placed/i,
        /order\s+accepted/i,
        /trade\s+executed/i,
        /order\s+filled/i
    ],
    
    // Text patterns for order rejection
    REJECTION_PATTERNS: [
        /order\s+rejected/i,
        /insufficient\s+funds/i,
        /market\s+closed/i,
        /invalid\s+symbol/i,
        /connection\s+error/i,
        /order\s+failed/i
    ],
    
    // Order ID patterns
    ORDER_ID_PATTERNS: [
        /order\s+id\s*:\s*(\d+)/i,
        /order\s+#(\d+)/i,
        /id\s*:\s*(\d+)/i
    ],
    
    // Price patterns
    PRICE_PATTERNS: [
        /\$?(\d+\.?\d*)/,
        /(\d+\.\d{2})/
    ],
    
    // Status patterns
    STATUS_PATTERNS: {
        PENDING: /pending|submitted|working/i,
        FILLED: /filled|executed|complete/i,
        CANCELLED: /cancelled|canceled/i,
        REJECTED: /rejected|failed|error/i
    }
};

// ============================================================================
// TIMING CONFIGURATIONS
// ============================================================================

const ORDER_VALIDATION_TIMING = {
    // How long to wait for confirmations
    CONFIRMATION_TIMEOUT: 10000,  // 10 seconds
    
    // How often to poll for status updates
    POLLING_INTERVAL: 500,        // 500ms
    
    // How long to wait for UI updates after actions
    UI_SETTLE_DELAY: 300,         // 300ms
    
    // Maximum time to wait for order to appear in tables
    ORDER_APPEARANCE_TIMEOUT: 15000, // 15 seconds
    
    // How long to wait between submission steps
    SUBMISSION_STEP_DELAY: 200    // 200ms
};

// ============================================================================
// UNIFIED TRADING SYSTEM CONFIGURATION
// ============================================================================

const UNIFIED_TRADING_CONFIG = {
    // Consolidated timeout configuration - eliminates duplicated timeout values
    TIMEOUTS: {
        // DOM operation timeouts (replaces scattered 10000ms values)
        ELEMENT_WAIT_DEFAULT: 10000,        // Standard element wait
        ELEMENT_WAIT_QUICK: 5000,           // Quick validation checks
        ELEMENT_WAIT_EXTENDED: 15000,       // Complex form operations
        DROPDOWN_SELECTION: 3000,           // Dropdown menu operations
        MODAL_TRANSITION: 2000,             // Modal dialog transitions
        FORM_VALIDATION: 5000,              // Form field validation
        
        // Operation delays (replaces scattered setTimeout values)
        CLICK_DELAY: 100,                   // Standard click delay
        DROPDOWN_DELAY: 300,                // Dropdown interaction delay  
        MODAL_DELAY: 500,                   // Modal operation delay
        FORM_INPUT_DELAY: 200,              // Form input setting delay
        NAVIGATION_DELAY: 500,              // Page navigation delay
        
        // Trading-specific timeouts
        ORDER_SUBMISSION_TIMEOUT: 15000,    // Order submission operations
        POSITION_EXIT_TIMEOUT: 20000,       // Position exit operations
        ACCOUNT_SWITCH_TIMEOUT: 10000,      // Account switching operations
        LOGIN_OPERATION_TIMEOUT: 30000      // Authentication operations
    },
    
    // Circuit breaker and performance thresholds
    PERFORMANCE: {
        // Circuit breaker settings
        CIRCUIT_BREAKER_FAILURE_THRESHOLD: 5,      // Failures before tripping
        CIRCUIT_BREAKER_RECOVERY_TIMEOUT: 30,      // Seconds before retry
        CIRCUIT_BREAKER_HALF_OPEN_LIMIT: 3,        // Test attempts when recovering
        
        // Performance monitoring thresholds
        SLOW_OPERATION_THRESHOLD: 2.0,             // Seconds for slow operation warning
        CRITICAL_OPERATION_THRESHOLD: 5.0,         // Seconds for critical slowness
        MAX_CONCURRENT_OPERATIONS: 3,              // Concurrent operation limit
        MAX_QUEUE_SIZE: 10,                        // Operation queue size limit
        
        // Health check intervals  
        HEALTH_CHECK_INTERVAL: 30,                 // Seconds between health checks
        LOGIN_STATUS_CHECK_INTERVAL: 30,           // Seconds between login checks
        CONNECTION_HEALTH_INTERVAL: 60             // Seconds between connection checks
    },
    
    // Risk management configuration
    RISK_MANAGEMENT: {
        // Position sizing limits
        MAX_QUANTITY_LIMIT: 1000,                  // Maximum single order quantity
        DEFAULT_TEST_QUANTITIES: [1, 5, 10, 20],   // Standard test quantities
        POSITION_SIZE_LIMITS: [1, 5, 10, 20, 50, 100], // Available position sizes
        
        // Risk validation thresholds
        MAX_DOLLAR_RISK_PER_TRADE: 1000,          // Maximum dollar risk per trade
        MAX_PORTFOLIO_RISK_PERCENT: 10,           // Maximum portfolio risk percentage
        ACCOUNT_BALANCE_BUFFER: 0.1,              // 10% buffer on account balance
        
        // Default risk parameters by account phase
        ACCOUNT_PHASES: {
            'conservative': { max_risk_per_trade: 100, max_position_size: 5 },
            'moderate': { max_risk_per_trade: 500, max_position_size: 20 },
            'aggressive': { max_risk_per_trade: 1000, max_position_size: 50 }
        }
    },
    
    // Debug and logging configuration
    DEBUG: {
        // Feature flags for debugging
        ENABLE_ORDER_VALIDATION_DEBUG: false,      // Order validation debugging
        ENABLE_DOM_INTELLIGENCE_DEBUG: false,      // DOM operation debugging  
        ENABLE_ACCOUNT_DATA_DEBUG: false,          // Account data debugging
        ENABLE_PERFORMANCE_MONITORING: true,       // Performance monitoring
        
        // Logging levels
        DEFAULT_LOG_LEVEL: 'INFO',                 // Default logging level
        VERBOSE_LOGGING: false,                    // Verbose operation logging
        CONSOLE_LOGGING: true,                     // Browser console logging
        PERSIST_DEBUG_LOGS: false                  // Persist debug logs locally
    },
    
    // Helper functions for configuration access
    getTimeout: function(operation) {
        const timeouts = UNIFIED_TRADING_CONFIG.TIMEOUTS;
        return timeouts[operation.toUpperCase()] || timeouts.ELEMENT_WAIT_DEFAULT;
    },
    
    getPerformanceThreshold: function(metric) {
        const perf = UNIFIED_TRADING_CONFIG.PERFORMANCE;
        return perf[metric.toUpperCase()] || null;
    },
    
    getRiskLimit: function(limitType) {
        const risk = UNIFIED_TRADING_CONFIG.RISK_MANAGEMENT;
        return risk[limitType.toUpperCase()] || null;
    },
    
    isDebugEnabled: function(feature) {
        const debug = UNIFIED_TRADING_CONFIG.DEBUG;
        return debug[`ENABLE_${feature.toUpperCase()}_DEBUG`] || false;
    }
};

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.TRADOVATE_UI_ELEMENTS = TRADOVATE_UI_ELEMENTS;
    window.ORDER_VALIDATION_PATTERNS = ORDER_VALIDATION_PATTERNS;
    window.ORDER_VALIDATION_TIMING = ORDER_VALIDATION_TIMING;
}

// ============================================================================
// UNIFIED TRADING EXECUTION FRAMEWORK
// ============================================================================

const UNIFIED_TRADING_FRAMEWORK = {
    // Consolidated futures tick data - eliminates duplication across autoOrder scripts
    FUTURES_TICK_DATA: {
        MNQ: { tickSize: 0.25, tickValue: 0.5, defaultSL: 40, defaultTP: 100, precision: 2 },
        NQ: { tickSize: 0.25, tickValue: 5.0, defaultSL: 40, defaultTP: 100, precision: 2 },
        ES: { tickSize: 0.25, tickValue: 12.5, defaultSL: 20, defaultTP: 50, precision: 2 },
        MES: { tickSize: 0.25, tickValue: 1.25, defaultSL: 20, defaultTP: 50, precision: 2 },
        RTY: { tickSize: 0.1, tickValue: 5.0, defaultSL: 10, defaultTP: 25, precision: 1 },
        M2K: { tickSize: 0.1, tickValue: 0.5, defaultSL: 10, defaultTP: 25, precision: 1 },
        YM: { tickSize: 1.0, tickValue: 5.0, defaultSL: 100, defaultTP: 200, precision: 0 },
        MYM: { tickSize: 1.0, tickValue: 0.5, defaultSL: 100, defaultTP: 200, precision: 0 },
        CL: { tickSize: 0.01, tickValue: 10.0, defaultSL: 0.50, defaultTP: 1.00, precision: 2 },
        MCL: { tickSize: 0.01, tickValue: 1.0, defaultSL: 0.50, defaultTP: 1.00, precision: 2 },
        GC: { tickSize: 0.1, tickValue: 10.0, defaultSL: 10, defaultTP: 20, precision: 1 },
        MGC: { tickSize: 0.1, tickValue: 1.0, defaultSL: 10, defaultTP: 20, precision: 1 },
        SI: { tickSize: 0.005, tickValue: 25.0, defaultSL: 0.5, defaultTP: 1.0, precision: 3 },
        SIL: { tickSize: 0.005, tickValue: 12.5, defaultSL: 0.5, defaultTP: 1.0, precision: 3 }
    },

    // Unified retry utility function - eliminates duplicated retry logic across scripts
    retryWithBackoff: function(operation, maxRetries, intervalMs, successCondition, description) {
        let retryCount = 0;
        const startTime = Date.now();
        
        return new Promise((resolve, reject) => {
            function attempt() {
                try {
                    const result = operation();
                    
                    if (successCondition(result)) {
                        console.log(`${description} succeeded after ${retryCount} retries in ${Date.now() - startTime}ms`);
                        resolve(result);
                    } else {
                        retryCount++;
                        if (retryCount >= maxRetries) {
                            const errorMsg = `${description} failed after ${maxRetries} attempts`;
                            console.error(errorMsg);
                            reject(new Error(errorMsg));
                        } else {
                            console.log(`${description} retry ${retryCount}/${maxRetries}`);
                            setTimeout(attempt, intervalMs);
                        }
                    }
                } catch (error) {
                    console.error(`${description} error:`, error);
                    retryCount++;
                    if (retryCount >= maxRetries) {
                        reject(error);
                    } else {
                        setTimeout(attempt, intervalMs);
                    }
                }
            }
            
            attempt();
        });
    },

    // Unified delay utility function - eliminates duplicated setTimeout patterns
    delay: function(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    // Unified order submission with comprehensive validation
    submitOrder: async function(orderType, priceValue, validationOptions = {}) {
        const startTime = Date.now();
        const submissionId = `ORDER_${startTime}_${Math.random().toString(36).substr(2, 6)}`;
        
        try {
            console.log(`[${submissionId}] Starting unified order submission: ${orderType} at ${priceValue}`);
            
            // Pre-submission validation using OrderValidationFramework if available
            if (window.autoOrderValidator && validationOptions.enableValidation !== false) {
                const orderData = {
                    orderType,
                    price: priceValue,
                    submissionId,
                    timestamp: new Date().toISOString()
                };
                
                const validationResult = await window.autoOrderValidator.validatePreSubmission(orderData);
                if (!validationResult.success) {
                    console.error(`[${submissionId}] Pre-submission validation failed:`, validationResult.errors);
                    return {
                        success: false,
                        submissionId,
                        error: 'Validation failed',
                        details: validationResult.errors
                    };
                }
            }
            
            // Apply common fields using framework method
            await UNIFIED_TRADING_FRAMEWORK.setCommonFields(validationOptions.tradeData || {});
            
            // Set order type with validation
            const typeSelector = TRADOVATE_UI_ELEMENTS.ORDER_SUBMISSION.ORDER_TYPE_SELECTOR;
            const typeSel = document.querySelector(typeSelector);
            
            if (!typeSel) {
                console.error(`[${submissionId}] Order type selector not found: ${typeSelector}`);
                return { success: false, submissionId, error: 'Order type selector not found' };
            }
            
            // DOM Intelligence validation if available
            if (window.domHelpers?.validateElementClickable && !window.domHelpers.validateElementClickable(typeSel)) {
                console.error(`[${submissionId}] Order type selector not clickable`);
                return { success: false, submissionId, error: 'Order type selector not clickable' };
            }
            
            typeSel.click();
            await UNIFIED_TRADING_FRAMEWORK.delay(UNIFIED_TRADING_CONFIG.TIMEOUTS.DROPDOWN_DELAY);
            
            // Select order type from dropdown
            const dropdownItems = document.querySelectorAll(TRADOVATE_UI_ELEMENTS.ORDER_SUBMISSION.ORDER_TYPE_DROPDOWN);
            const targetItem = Array.from(dropdownItems).find(li => li.textContent.trim() === orderType);
            
            if (!targetItem) {
                console.error(`[${submissionId}] Order type not found: ${orderType}`);
                return { success: false, submissionId, error: `Order type not found: ${orderType}` };
            }
            
            targetItem.click();
            await UNIFIED_TRADING_FRAMEWORK.delay(UNIFIED_TRADING_CONFIG.TIMEOUTS.DROPDOWN_DELAY);
            
            // Set price if provided
            if (priceValue) {
                const priceSet = await UNIFIED_TRADING_FRAMEWORK.updateInputValue(
                    TRADOVATE_UI_ELEMENTS.ORDER_SUBMISSION.PRICE_INPUT,
                    priceValue
                );
                
                if (!priceSet) {
                    console.error(`[${submissionId}] Failed to set price: ${priceValue}`);
                    return { success: false, submissionId, error: 'Failed to set price' };
                }
            }
            
            // Click submit button with validation
            const submitButton = document.querySelector(TRADOVATE_UI_ELEMENTS.ORDER_SUBMISSION.SUBMIT_BUTTON);
            if (!submitButton) {
                console.error(`[${submissionId}] Submit button not found`);
                return { success: false, submissionId, error: 'Submit button not found' };
            }
            
            if (window.domHelpers?.validateElementClickable && !window.domHelpers.validateElementClickable(submitButton)) {
                console.error(`[${submissionId}] Submit button not clickable`);
                return { success: false, submissionId, error: 'Submit button not clickable' };
            }
            
            submitButton.click();
            await UNIFIED_TRADING_FRAMEWORK.delay(500);
            
            // Post-submission validation
            const orderEvents = UNIFIED_TRADING_FRAMEWORK.getOrderEvents();
            const executionTime = Date.now() - startTime;
            
            console.log(`[${submissionId}] Order submission completed in ${executionTime}ms`);
            console.log(`[${submissionId}] Order events:`, orderEvents);
            
            // Navigate back
            const backButton = document.querySelector(TRADOVATE_UI_ELEMENTS.ORDER_SUBMISSION.BACK_BUTTON);
            if (backButton && window.domHelpers?.validateElementClickable(backButton)) {
                backButton.click();
                await UNIFIED_TRADING_FRAMEWORK.delay(UNIFIED_TRADING_CONFIG.TIMEOUTS.NAVIGATION_DELAY);
            }
            
            return {
                success: true,
                submissionId,
                orderType,
                price: priceValue,
                executionTime,
                orderEvents
            };
            
        } catch (error) {
            const executionTime = Date.now() - startTime;
            console.error(`[${submissionId}] Order submission failed after ${executionTime}ms:`, error);
            return {
                success: false,
                submissionId,
                error: error.message || 'Unknown error',
                executionTime
            };
        }
    },

    // Unified field setting with validation
    setCommonFields: async function(tradeData) {
        console.log('Setting common order fields with unified framework');
        
        // Set action (Buy/Sell) if provided
        if (tradeData.action) {
            console.log(`Setting action to: ${tradeData.action}`);
            const actionLabels = document.querySelectorAll('.radio-group.btn-group label');
            
            for (const label of actionLabels) {
                if (label.textContent.trim() === tradeData.action) {
                    if (!window.domHelpers?.validateElementClickable || window.domHelpers.validateElementClickable(label)) {
                        label.click();
                        console.log(`Clicked ${tradeData.action} label`);
                        break;
                    }
                }
            }
        }
        
        // Set quantity if provided
        if (tradeData.qty) {
            console.log(`Setting quantity to: ${tradeData.qty}`);
            await UNIFIED_TRADING_FRAMEWORK.updateInputValue(
                TRADOVATE_UI_ELEMENTS.ORDER_SUBMISSION.QUANTITY_INPUT,
                tradeData.qty
            );
        }
    },

    // Unified input value updating with validation
    updateInputValue: async function(selector, value) {
        console.log(`Updating input ${selector} to value: ${value}`);
        
        // Wait for live, visible field
        let input;
        for (let i = 0; i < 25; i++) {
            const candidates = Array.from(document.querySelectorAll(selector));
            input = candidates.find(el => el.offsetParent && !el.disabled);
            if (input) break;
            await UNIFIED_TRADING_FRAMEWORK.delay(UNIFIED_TRADING_CONFIG.TIMEOUTS.CLICK_DELAY);
        }
        
        if (!input) {
            console.error(`No live input found for selector: ${selector}`);
            return false;
        }
        
        // Use native setter for reliable value setting
        const setVal = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        
        // Write-verify loop with Enter commit
        for (let tries = 0; tries < 3; tries++) {
            input.focus();
            setVal.call(input, value);
            
            // Dispatch input and change events
            ['input', 'change'].forEach(eventType =>
                input.dispatchEvent(new Event(eventType, { bubbles: true }))
            );
            
            // Commit with Enter key
            input.dispatchEvent(new KeyboardEvent('keydown', {
                key: 'Enter',
                code: 'Enter',
                keyCode: 13,
                which: 13,
                bubbles: true
            }));
            
            input.blur();
            await UNIFIED_TRADING_FRAMEWORK.delay(UNIFIED_TRADING_CONFIG.TIMEOUTS.FORM_INPUT_DELAY);
            
            // Verify value was set correctly
            if (Number(input.value) === Number(value)) {
                console.log(`Successfully set ${selector} to ${value}`);
                return true;
            }
        }
        
        console.error(`Failed to set ${selector} to ${value} after 3 attempts`);
        return false;
    },

    // Unified order events extraction - eliminates duplication
    getOrderEvents: function(container = document) {
        const rows = container.querySelectorAll('.order-history-content .public_fixedDataTable_bodyRow');
        return Array.from(rows, row => {
            const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
            return {
                timestamp: cells[0]?.textContent.trim() || '',
                id: cells[1]?.textContent.trim() || '',
                event: cells[2]?.textContent.trim() || '',
                symbol: cells[3]?.textContent.trim() || '',
                side: cells[4]?.textContent.trim() || '',
                quantity: cells[5]?.textContent.trim() || '',
                price: cells[6]?.textContent.trim() || '',
                status: cells[7]?.textContent.trim() || ''
            };
        });
    },

    // Unified bracket order creation
    createBracketOrder: async function(tradeData, options = {}) {
        const bracketId = `BRACKET_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
        console.log(`[${bracketId}] Creating unified bracket order with data:`, tradeData);
        
        try {
            // Generate tracking ID for validation framework
            if (options.enableValidation !== false) {
                tradeData.bracketGroupId = bracketId;
                tradeData.submissionTimestamp = new Date().toISOString();
            }
            
            // Submit main order
            const mainOrderResult = await UNIFIED_TRADING_FRAMEWORK.submitOrder(
                tradeData.orderType || 'MARKET',
                tradeData.price,
                { tradeData, enableValidation: options.enableValidation }
            );
            
            if (!mainOrderResult.success) {
                console.error(`[${bracketId}] Main order failed:`, mainOrderResult.error);
                return { success: false, bracketId, error: mainOrderResult.error };
            }
            
            // Submit stop-loss order if configured
            if (tradeData.slEnabled && tradeData.slPrice) {
                console.log(`[${bracketId}] Submitting stop-loss order at ${tradeData.slPrice}`);
                const slResult = await UNIFIED_TRADING_FRAMEWORK.submitOrder(
                    'STP',
                    tradeData.slPrice,
                    { tradeData, enableValidation: options.enableValidation }
                );
                
                if (!slResult.success) {
                    console.warn(`[${bracketId}] Stop-loss order failed:`, slResult.error);
                }
            }
            
            // Submit take-profit order if configured
            if (tradeData.tpEnabled && tradeData.tpPrice) {
                console.log(`[${bracketId}] Submitting take-profit order at ${tradeData.tpPrice}`);
                const tpResult = await UNIFIED_TRADING_FRAMEWORK.submitOrder(
                    'LMT',
                    tradeData.tpPrice,
                    { tradeData, enableValidation: options.enableValidation }
                );
                
                if (!tpResult.success) {
                    console.warn(`[${bracketId}] Take-profit order failed:`, tpResult.error);
                }
            }
            
            console.log(`[${bracketId}] Bracket order creation completed`);
            return {
                success: true,
                bracketId,
                mainOrder: mainOrderResult,
                timestamp: new Date().toISOString()
            };
            
        } catch (error) {
            console.error(`[${bracketId}] Bracket order creation failed:`, error);
            return {
                success: false,
                bracketId,
                error: error.message || 'Unknown error'
            };
        }
    },


    // Get tick data for a symbol
    getTickData: function(symbol) {
        const rootSymbol = TRADOVATE_UI_ELEMENTS.TRADING_DATA_PROCESSORS.extractRootSymbol(symbol);
        return UNIFIED_TRADING_FRAMEWORK.FUTURES_TICK_DATA[rootSymbol] || null;
    }
};

// Also export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        TRADOVATE_UI_ELEMENTS,
        ORDER_VALIDATION_PATTERNS,
        ORDER_VALIDATION_TIMING,
        UNIFIED_TRADING_FRAMEWORK,
        UNIFIED_TRADING_CONFIG
    };
}

// Export unified framework to window
if (typeof window !== 'undefined') {
    window.TRADOVATE_UI_ELEMENTS = TRADOVATE_UI_ELEMENTS;
    window.ORDER_VALIDATION_PATTERNS = ORDER_VALIDATION_PATTERNS;
    window.ORDER_VALIDATION_TIMING = ORDER_VALIDATION_TIMING;
    window.UNIFIED_TRADING_FRAMEWORK = UNIFIED_TRADING_FRAMEWORK;
    window.UNIFIED_TRADING_CONFIG = UNIFIED_TRADING_CONFIG;
}

console.log('✅ Tradovate UI Elements mapping loaded');
console.log('✅ Unified Trading Execution Framework loaded');
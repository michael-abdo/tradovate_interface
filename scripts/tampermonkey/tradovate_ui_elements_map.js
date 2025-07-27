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

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.TRADOVATE_UI_ELEMENTS = TRADOVATE_UI_ELEMENTS;
    window.ORDER_VALIDATION_PATTERNS = ORDER_VALIDATION_PATTERNS;
    window.ORDER_VALIDATION_TIMING = ORDER_VALIDATION_TIMING;
}

// Also export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        TRADOVATE_UI_ELEMENTS,
        ORDER_VALIDATION_PATTERNS,
        ORDER_VALIDATION_TIMING
    };
}

console.log('✅ Tradovate UI Elements mapping loaded');
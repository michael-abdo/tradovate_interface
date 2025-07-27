// ============================================================================
// ORDER ERROR PATTERNS AND FAILURE SCENARIOS DOCUMENTATION
// ============================================================================
// 
// This file documents all known error patterns, failure scenarios, and 
// recovery strategies for Tradovate order submission and management.
//
// Used by the Order Validation Framework for comprehensive error detection
// and classification.
//
// Last Updated: 2025-01-26
// ============================================================================

const ORDER_ERROR_PATTERNS = {
    
    // ============================================================================
    // SUBMISSION ERRORS (Pre-execution failures)
    // ============================================================================
    SUBMISSION_ERRORS: {
        // Account and Authorization Errors
        INSUFFICIENT_FUNDS: {
            patterns: [
                /insufficient\s+funds/i,
                /not\s+enough\s+margin/i,
                /margin\s+requirement\s+not\s+met/i,
                /buying\s+power\s+exceeded/i,
                /insufficient\s+balance/i
            ],
            severity: 'HIGH',
            category: 'ACCOUNT_FUNDS',
            recovery: 'REDUCE_QUANTITY_OR_CANCEL',
            userAction: 'Check account balance and margin requirements'
        },
        
        ACCOUNT_LOCKED: {
            patterns: [
                /account\s+locked/i,
                /account\s+suspended/i,
                /trading\s+disabled/i,
                /account\s+restriction/i
            ],
            severity: 'CRITICAL',
            category: 'ACCOUNT_ACCESS',
            recovery: 'ABORT_ALL_TRADING',
            userAction: 'Contact broker support'
        },
        
        UNAUTHORIZED_SYMBOL: {
            patterns: [
                /not\s+authorized\s+to\s+trade/i,
                /symbol\s+not\s+permitted/i,
                /trading\s+permission\s+denied/i,
                /unauthorized\s+instrument/i
            ],
            severity: 'HIGH',
            category: 'PERMISSIONS',
            recovery: 'SKIP_SYMBOL',
            userAction: 'Check symbol permissions'
        },
        
        // Market and Timing Errors
        MARKET_CLOSED: {
            patterns: [
                /market\s+closed/i,
                /trading\s+session\s+closed/i,
                /outside\s+trading\s+hours/i,
                /market\s+not\s+open/i,
                /session\s+ended/i
            ],
            severity: 'MEDIUM',
            category: 'MARKET_HOURS',
            recovery: 'QUEUE_FOR_NEXT_SESSION',
            userAction: 'Check market hours'
        },
        
        MARKET_HALTED: {
            patterns: [
                /trading\s+halted/i,
                /market\s+suspended/i,
                /circuit\s+breaker/i,
                /trading\s+paused/i
            ],
            severity: 'HIGH',
            category: 'MARKET_CONDITION',
            recovery: 'WAIT_AND_RETRY',
            userAction: 'Wait for market to resume'
        },
        
        // Symbol and Contract Errors
        INVALID_SYMBOL: {
            patterns: [
                /invalid\s+symbol/i,
                /symbol\s+not\s+found/i,
                /unknown\s+instrument/i,
                /contract\s+not\s+available/i,
                /symbol\s+expired/i
            ],
            severity: 'HIGH',
            category: 'SYMBOL_VALIDATION',
            recovery: 'UPDATE_SYMBOL',
            userAction: 'Verify symbol format and availability'
        },
        
        CONTRACT_EXPIRED: {
            patterns: [
                /contract\s+expired/i,
                /expiration\s+date\s+passed/i,
                /expired\s+instrument/i,
                /no\s+longer\s+active/i
            ],
            severity: 'HIGH',
            category: 'CONTRACT_LIFECYCLE',
            recovery: 'ROLL_TO_FRONT_MONTH',
            userAction: 'Update to active contract month'
        },
        
        // Price and Quantity Errors
        INVALID_PRICE: {
            patterns: [
                /invalid\s+price/i,
                /price\s+out\s+of\s+range/i,
                /limit\s+up|limit\s+down/i,
                /price\s+too\s+far\s+from\s+market/i,
                /minimum\s+price\s+increment/i
            ],
            severity: 'MEDIUM',
            category: 'PRICE_VALIDATION',
            recovery: 'ADJUST_PRICE',
            userAction: 'Check price limits and increments'
        },
        
        INVALID_QUANTITY: {
            patterns: [
                /invalid\s+quantity/i,
                /minimum\s+quantity\s+not\s+met/i,
                /quantity\s+exceeds\s+limit/i,
                /position\s+limit\s+exceeded/i,
                /lot\s+size\s+violation/i
            ],
            severity: 'MEDIUM',
            category: 'QUANTITY_VALIDATION',
            recovery: 'ADJUST_QUANTITY',
            userAction: 'Check minimum and maximum quantity limits'
        }
    },
    
    // ============================================================================
    // EXECUTION ERRORS (During order processing)
    // ============================================================================
    EXECUTION_ERRORS: {
        PARTIAL_FILL_TIMEOUT: {
            patterns: [
                /partially\s+filled/i,
                /partial\s+execution/i,
                /incomplete\s+fill/i
            ],
            severity: 'MEDIUM',
            category: 'FILL_STATUS',
            recovery: 'MONITOR_REMAINING',
            userAction: 'Decide whether to cancel remaining quantity'
        },
        
        NO_LIQUIDITY: {
            patterns: [
                /no\s+liquidity/i,
                /insufficient\s+market\s+depth/i,
                /no\s+available\s+contracts/i,
                /thin\s+market/i
            ],
            severity: 'MEDIUM',
            category: 'MARKET_LIQUIDITY',
            recovery: 'ADJUST_PRICE_OR_WAIT',
            userAction: 'Consider adjusting price or waiting for liquidity'
        },
        
        PRICE_MOVED: {
            patterns: [
                /price\s+has\s+moved/i,
                /market\s+price\s+changed/i,
                /stale\s+price/i,
                /price\s+no\s+longer\s+valid/i
            ],
            severity: 'LOW',
            category: 'PRICE_MOVEMENT',
            recovery: 'UPDATE_AND_RESUBMIT',
            userAction: 'Update price and resubmit'
        }
    },
    
    // ============================================================================
    // TECHNICAL ERRORS (System and connectivity issues)
    // ============================================================================
    TECHNICAL_ERRORS: {
        CONNECTION_LOST: {
            patterns: [
                /connection\s+lost/i,
                /network\s+error/i,
                /disconnected/i,
                /timeout/i,
                /server\s+unavailable/i
            ],
            severity: 'CRITICAL',
            category: 'CONNECTIVITY',
            recovery: 'RECONNECT_AND_VERIFY',
            userAction: 'Check internet connection'
        },
        
        SERVER_ERROR: {
            patterns: [
                /server\s+error/i,
                /internal\s+error/i,
                /system\s+unavailable/i,
                /service\s+temporarily\s+unavailable/i,
                /500\s+error/i
            ],
            severity: 'HIGH',
            category: 'SERVER_ISSUE',
            recovery: 'RETRY_WITH_BACKOFF',
            userAction: 'Wait and retry, contact support if persistent'
        },
        
        RATE_LIMITED: {
            patterns: [
                /rate\s+limit\s+exceeded/i,
                /too\s+many\s+requests/i,
                /throttled/i,
                /order\s+frequency\s+limit/i
            ],
            severity: 'MEDIUM',
            category: 'RATE_LIMITING',
            recovery: 'DELAY_AND_RETRY',
            userAction: 'Reduce order frequency'
        },
        
        SYSTEM_MAINTENANCE: {
            patterns: [
                /system\s+maintenance/i,
                /scheduled\s+downtime/i,
                /platform\s+update/i,
                /temporarily\s+unavailable/i
            ],
            severity: 'HIGH',
            category: 'MAINTENANCE',
            recovery: 'WAIT_FOR_COMPLETION',
            userAction: 'Wait for maintenance to complete'
        }
    },
    
    // ============================================================================
    // BRACKET ORDER SPECIFIC ERRORS
    // ============================================================================
    BRACKET_ERRORS: {
        PARENT_ORDER_FAILED: {
            patterns: [
                /parent\s+order\s+failed/i,
                /entry\s+order\s+rejected/i,
                /bracket\s+setup\s+failed/i
            ],
            severity: 'HIGH',
            category: 'BRACKET_COORDINATION',
            recovery: 'CANCEL_ALL_CHILD_ORDERS',
            userAction: 'Review bracket order configuration'
        },
        
        CHILD_ORDER_ORPHANED: {
            patterns: [
                /orphaned\s+order/i,
                /parent\s+not\s+found/i,
                /bracket\s+relationship\s+broken/i
            ],
            severity: 'HIGH',
            category: 'BRACKET_COORDINATION',
            recovery: 'MANUAL_CLEANUP_REQUIRED',
            userAction: 'Manually cancel orphaned orders'
        },
        
        OCO_SETUP_FAILED: {
            patterns: [
                /oco\s+failed/i,
                /one\s+cancels\s+other\s+error/i,
                /bracket\s+linking\s+failed/i
            ],
            severity: 'HIGH',
            category: 'BRACKET_COORDINATION',
            recovery: 'PLACE_ORDERS_INDIVIDUALLY',
            userAction: 'Place TP/SL orders manually'
        }
    },
    
    // ============================================================================
    // RISK MANAGEMENT ERRORS
    // ============================================================================
    RISK_MANAGEMENT_ERRORS: {
        POSITION_LIMIT_EXCEEDED: {
            patterns: [
                /position\s+limit\s+exceeded/i,
                /maximum\s+position\s+size/i,
                /exposure\s+limit\s+reached/i
            ],
            severity: 'HIGH',
            category: 'RISK_LIMITS',
            recovery: 'REDUCE_POSITION_SIZE',
            userAction: 'Review position sizing'
        },
        
        DAILY_LOSS_LIMIT: {
            patterns: [
                /daily\s+loss\s+limit/i,
                /maximum\s+daily\s+loss/i,
                /loss\s+limit\s+reached/i
            ],
            severity: 'CRITICAL',
            category: 'RISK_LIMITS',
            recovery: 'STOP_ALL_TRADING',
            userAction: 'Review risk management settings'
        },
        
        MARGIN_CALL: {
            patterns: [
                /margin\s+call/i,
                /liquidation\s+warning/i,
                /margin\s+requirement\s+breach/i
            ],
            severity: 'CRITICAL',
            category: 'MARGIN_MANAGEMENT',
            recovery: 'REDUCE_POSITIONS',
            userAction: 'Add funds or reduce positions'
        }
    }
};

// ============================================================================
// ERROR CLASSIFICATION UTILITIES
// ============================================================================

const ERROR_CLASSIFICATION = {
    
    /**
     * Classify an error message
     * @param {string} errorMessage - The error message to classify
     * @returns {Object} Classification result with category, severity, and recovery strategy
     */
    classifyError: (errorMessage) => {
        if (!errorMessage || typeof errorMessage !== 'string') {
            return {
                category: 'UNKNOWN',
                severity: 'MEDIUM',
                recovery: 'MANUAL_REVIEW',
                patterns: [],
                userAction: 'Review error manually'
            };
        }
        
        // Search through all error categories
        const allCategories = [
            ...Object.values(ORDER_ERROR_PATTERNS.SUBMISSION_ERRORS),
            ...Object.values(ORDER_ERROR_PATTERNS.EXECUTION_ERRORS),
            ...Object.values(ORDER_ERROR_PATTERNS.TECHNICAL_ERRORS),
            ...Object.values(ORDER_ERROR_PATTERNS.BRACKET_ERRORS),
            ...Object.values(ORDER_ERROR_PATTERNS.RISK_MANAGEMENT_ERRORS)
        ];
        
        for (const errorType of allCategories) {
            for (const pattern of errorType.patterns) {
                if (pattern.test(errorMessage)) {
                    return {
                        ...errorType,
                        matchedPattern: pattern.toString(),
                        originalMessage: errorMessage
                    };
                }
            }
        }
        
        // No pattern matched - return unknown classification
        return {
            category: 'UNKNOWN',
            severity: 'MEDIUM',
            recovery: 'MANUAL_REVIEW',
            patterns: [],
            userAction: 'Review error manually',
            originalMessage: errorMessage
        };
    },
    
    /**
     * Get recovery strategy for a classified error
     * @param {Object} classification - Result from classifyError
     * @returns {Object} Recovery strategy with actions and timing
     */
    getRecoveryStrategy: (classification) => {
        const recoveryStrategies = {
            'REDUCE_QUANTITY_OR_CANCEL': {
                actions: ['reduce_quantity', 'cancel_order'],
                timing: 'IMMEDIATE',
                priority: 'HIGH'
            },
            'ABORT_ALL_TRADING': {
                actions: ['cancel_all_orders', 'close_all_positions'],
                timing: 'IMMEDIATE',
                priority: 'CRITICAL'
            },
            'SKIP_SYMBOL': {
                actions: ['update_symbol_list', 'notify_user'],
                timing: 'IMMEDIATE',
                priority: 'MEDIUM'
            },
            'QUEUE_FOR_NEXT_SESSION': {
                actions: ['schedule_order', 'wait_for_market_open'],
                timing: 'DELAYED',
                priority: 'LOW'
            },
            'WAIT_AND_RETRY': {
                actions: ['wait', 'retry_order'],
                timing: 'DELAYED',
                priority: 'MEDIUM',
                retryDelay: 30000 // 30 seconds
            },
            'UPDATE_SYMBOL': {
                actions: ['get_front_month', 'update_order_symbol'],
                timing: 'IMMEDIATE',
                priority: 'HIGH'
            },
            'ROLL_TO_FRONT_MONTH': {
                actions: ['calculate_front_month', 'update_symbol', 'resubmit_order'],
                timing: 'IMMEDIATE',
                priority: 'HIGH'
            },
            'ADJUST_PRICE': {
                actions: ['get_current_market', 'calculate_valid_price', 'update_order'],
                timing: 'IMMEDIATE',
                priority: 'MEDIUM'
            },
            'ADJUST_QUANTITY': {
                actions: ['calculate_max_quantity', 'update_order'],
                timing: 'IMMEDIATE',
                priority: 'MEDIUM'
            },
            'RECONNECT_AND_VERIFY': {
                actions: ['check_connection', 'reconnect', 'verify_order_status'],
                timing: 'IMMEDIATE',
                priority: 'CRITICAL'
            },
            'RETRY_WITH_BACKOFF': {
                actions: ['exponential_backoff', 'retry_order'],
                timing: 'DELAYED',
                priority: 'MEDIUM',
                maxRetries: 3,
                baseDelay: 1000
            },
            'DELAY_AND_RETRY': {
                actions: ['wait', 'retry_order'],
                timing: 'DELAYED',
                priority: 'LOW',
                retryDelay: 5000 // 5 seconds
            },
            'CANCEL_ALL_CHILD_ORDERS': {
                actions: ['find_child_orders', 'cancel_orders', 'cleanup_bracket'],
                timing: 'IMMEDIATE',
                priority: 'HIGH'
            },
            'MANUAL_CLEANUP_REQUIRED': {
                actions: ['notify_user', 'log_for_manual_review'],
                timing: 'IMMEDIATE',
                priority: 'HIGH'
            },
            'STOP_ALL_TRADING': {
                actions: ['cancel_all_orders', 'close_all_positions', 'disable_trading'],
                timing: 'IMMEDIATE',
                priority: 'CRITICAL'
            },
            'MANUAL_REVIEW': {
                actions: ['log_error', 'notify_user', 'request_manual_review'],
                timing: 'IMMEDIATE',
                priority: 'MEDIUM'
            }
        };
        
        return recoveryStrategies[classification.recovery] || recoveryStrategies['MANUAL_REVIEW'];
    },
    
    /**
     * Check if an error is retryable
     * @param {Object} classification - Error classification
     * @returns {boolean} Whether the error can be retried
     */
    isRetryable: (classification) => {
        const retryableCategories = [
            'CONNECTIVITY',
            'SERVER_ISSUE',
            'RATE_LIMITING',
            'MARKET_LIQUIDITY',
            'PRICE_MOVEMENT'
        ];
        
        return retryableCategories.includes(classification.category);
    },
    
    /**
     * Check if an error requires immediate attention
     * @param {Object} classification - Error classification
     * @returns {boolean} Whether the error is critical
     */
    isCritical: (classification) => {
        return classification.severity === 'CRITICAL';
    }
};

// ============================================================================
// ERROR MONITORING CONFIGURATION
// ============================================================================

const ERROR_MONITORING_CONFIG = {
    // How often to check for error dialogs
    ERROR_CHECK_INTERVAL: 500, // 500ms
    
    // How long to wait for error dialogs to appear after order submission
    ERROR_DETECTION_TIMEOUT: 5000, // 5 seconds
    
    // Maximum number of retry attempts for recoverable errors
    MAX_RETRY_ATTEMPTS: 3,
    
    // Base delay for exponential backoff (milliseconds)
    RETRY_BASE_DELAY: 1000, // 1 second
    
    // Maximum delay between retries (milliseconds)
    MAX_RETRY_DELAY: 30000, // 30 seconds
    
    // How long to keep error history (milliseconds)
    ERROR_HISTORY_RETENTION: 3600000, // 1 hour
    
    // Error severity levels
    SEVERITY_LEVELS: {
        LOW: 1,
        MEDIUM: 2,
        HIGH: 3,
        CRITICAL: 4
    }
};

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.ORDER_ERROR_PATTERNS = ORDER_ERROR_PATTERNS;
    window.ERROR_CLASSIFICATION = ERROR_CLASSIFICATION;
    window.ERROR_MONITORING_CONFIG = ERROR_MONITORING_CONFIG;
}

// Also export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ORDER_ERROR_PATTERNS,
        ERROR_CLASSIFICATION,
        ERROR_MONITORING_CONFIG
    };
}

console.log('✅ Order Error Patterns and Classification loaded');
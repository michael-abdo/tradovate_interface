// ============================================================================
// ERROR RECOVERY FRAMEWORK
// ============================================================================
// 
// Enterprise-level error recovery and resilience patterns for Tradovate
// trading operations. Provides standardized error handling, retry logic,
// circuit breaker patterns, and graceful degradation strategies.
//
// Usage:
//   const recovery = new ErrorRecoveryFramework({
//       scriptName: 'autoOrder',
//       maxRetries: 3,
//       circuitBreakerThreshold: 5
//   });
//   
//   const result = await recovery.executeWithRecovery(async () => {
//       return await someTradingOperation();
//   }, 'Order Submission');
//
// ============================================================================

/**
 * Error Recovery Framework for Tradovate Trading Operations
 * Provides standardized error handling, retry logic, and circuit breaker patterns
 */
class ErrorRecoveryFramework {
    constructor(options = {}) {
        this.scriptName = options.scriptName || 'Unknown';
        this.maxRetries = options.maxRetries || 3;
        this.baseDelay = options.baseDelay || 1000;
        this.maxDelay = options.maxDelay || 10000;
        this.circuitBreakerThreshold = options.circuitBreakerThreshold || 5;
        this.circuitBreakerTimeout = options.circuitBreakerTimeout || 60000;
        this.debugMode = options.debugMode || false;
        
        // Circuit breaker state
        this.circuitBreakers = new Map();
        
        // Error statistics
        this.errorStats = {
            totalOperations: 0,
            totalErrors: 0,
            errorsByType: new Map(),
            errorsByOperation: new Map(),
            recoverySuccesses: 0,
            recoveryFailures: 0
        };
        
        // Recovery strategies registry
        this.recoveryStrategies = new Map();
        this.registerDefaultStrategies();
        
        console.log(`✅ Error Recovery Framework initialized for ${this.scriptName}`);
    }
    
    /**
     * Register default recovery strategies for common error patterns
     */
    registerDefaultStrategies() {
        // DOM Element Not Found Recovery
        this.addRecoveryStrategy('ElementNotFound', {
            canHandle: (error) => {
                return error.message.includes('not found') || 
                       error.message.includes('querySelector') ||
                       error.name === 'ElementNotFoundError';
            },
            recover: async (operation, context) => {
                console.log('🔄 Recovery Strategy: ElementNotFound - Waiting for DOM updates');
                await this.delay(2000);
                
                // Try alternative selectors if provided
                if (context.alternativeSelectors) {
                    for (const selector of context.alternativeSelectors) {
                        if (document.querySelector(selector)) {
                            console.log(`✅ Recovery successful with alternative selector: ${selector}`);
                            return await operation();
                        }
                    }
                }
                
                // Try page refresh as last resort
                if (context.allowRefresh) {
                    console.log('🔄 Recovery Strategy: Refreshing page as last resort');
                    location.reload();
                    return null; // Will be handled by retry logic
                }
                
                throw error;
            }
        });
        
        // Network/Connection Error Recovery
        this.addRecoveryStrategy('NetworkError', {
            canHandle: (error) => {
                return error.message.includes('network') ||
                       error.message.includes('timeout') ||
                       error.message.includes('fetch') ||
                       error.name === 'NetworkError';
            },
            recover: async (operation, context) => {
                console.log('🔄 Recovery Strategy: NetworkError - Checking connection and retrying');
                
                // Wait longer for network issues
                await this.delay(5000);
                
                // Check if we can reach Tradovate
                try {
                    await fetch('https://trader.tradovate.com/ping', { method: 'HEAD' });
                    console.log('✅ Network connection restored');
                    return await operation();
                } catch (networkError) {
                    console.error('❌ Network still unavailable');
                    throw error;
                }
            }
        });
        
        // Modal/Dialog Error Recovery
        this.addRecoveryStrategy('ModalError', {
            canHandle: (error) => {
                return error.message.includes('modal') ||
                       error.message.includes('dialog') ||
                       error.message.includes('popup');
            },
            recover: async (operation, context) => {
                console.log('🔄 Recovery Strategy: ModalError - Attempting to close modals and retry');
                
                // Close any open modals
                const modalCloseButtons = document.querySelectorAll(
                    '.modal .close, .modal-header .close, [aria-label="close"], .btn-close'
                );
                for (const button of modalCloseButtons) {
                    try {
                        button.click();
                        await this.delay(500);
                    } catch (e) {
                        // Ignore click errors
                    }
                }
                
                // Press Escape key
                document.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Escape',
                    code: 'Escape',
                    keyCode: 27
                }));
                
                await this.delay(1000);
                return await operation();
            }
        });
        
        // Form Validation Error Recovery
        this.addRecoveryStrategy('FormValidation', {
            canHandle: (error) => {
                return error.message.includes('validation') ||
                       error.message.includes('required') ||
                       error.message.includes('invalid value');
            },
            recover: async (operation, context) => {
                console.log('🔄 Recovery Strategy: FormValidation - Clearing and re-filling form');
                
                // Clear all form fields first
                if (context.formSelector) {
                    const form = document.querySelector(context.formSelector);
                    if (form) {
                        const inputs = form.querySelectorAll('input, select, textarea');
                        for (const input of inputs) {
                            input.value = '';
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                        await this.delay(500);
                    }
                }
                
                // Retry the operation
                return await operation();
            }
        });
        
        // Trading Hours Error Recovery
        this.addRecoveryStrategy('TradingHours', {
            canHandle: (error) => {
                return error.message.includes('market') ||
                       error.message.includes('trading hours') ||
                       error.message.includes('closed');
            },
            recover: async (operation, context) => {
                console.log('🔄 Recovery Strategy: TradingHours - Market is closed, scheduling for later');
                
                // Don't retry immediately for market hours issues
                throw new Error('Market is closed - operation cannot be completed now');
            }
        });
    }
    
    /**
     * Add a custom recovery strategy
     * @param {string} name - Strategy name
     * @param {Object} strategy - Strategy object with canHandle and recover functions
     */
    addRecoveryStrategy(name, strategy) {
        if (!strategy.canHandle || !strategy.recover) {
            throw new Error('Recovery strategy must have canHandle and recover functions');
        }
        this.recoveryStrategies.set(name, strategy);
        console.log(`✅ Recovery strategy registered: ${name}`);
    }
    
    /**
     * Execute an operation with comprehensive error recovery
     * @param {Function} operation - Async function to execute
     * @param {string} operationName - Human readable operation name
     * @param {Object} context - Additional context for recovery strategies
     * @returns {Promise} Operation result or throws after all recovery attempts
     */
    async executeWithRecovery(operation, operationName = 'Unknown Operation', context = {}) {
        const operationId = `${operationName}_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
        
        console.log(`🔍 Error Recovery: Starting operation "${operationName}" (ID: ${operationId})`);
        
        this.errorStats.totalOperations++;
        
        // Check circuit breaker
        if (this.isCircuitOpen(operationName)) {
            const error = new Error(`Circuit breaker OPEN for ${operationName} - too many recent failures`);
            this.recordError(error, operationName);
            throw error;
        }
        
        let lastError = null;
        
        for (let attempt = 1; attempt <= this.maxRetries + 1; attempt++) {
            try {
                console.log(`🔍 Attempt ${attempt}/${this.maxRetries + 1} for operation: ${operationName}`);
                
                const result = await operation();
                
                // Success - reset circuit breaker
                this.recordSuccess(operationName);
                
                if (attempt > 1) {
                    console.log(`✅ Operation "${operationName}" succeeded after ${attempt} attempts`);
                    this.errorStats.recoverySuccesses++;
                } else {
                    console.log(`✅ Operation "${operationName}" succeeded on first attempt`);
                }
                
                return result;
                
            } catch (error) {
                lastError = error;
                console.error(`❌ Attempt ${attempt} failed for "${operationName}":`, error.message);
                
                this.recordError(error, operationName);
                
                // Don't retry on the last attempt
                if (attempt > this.maxRetries) {
                    break;
                }
                
                // Try to recover using registered strategies
                let recoveryAttempted = false;
                
                for (const [strategyName, strategy] of this.recoveryStrategies) {
                    if (strategy.canHandle(error)) {
                        console.log(`🔄 Attempting recovery with strategy: ${strategyName}`);
                        
                        try {
                            const recoveredResult = await strategy.recover(operation, {
                                ...context,
                                attempt,
                                operationName,
                                error
                            });
                            
                            // If recovery returned a result, consider it successful
                            if (recoveredResult !== undefined) {
                                console.log(`✅ Recovery successful with strategy: ${strategyName}`);
                                this.recordSuccess(operationName);
                                this.errorStats.recoverySuccesses++;
                                return recoveredResult;
                            }
                            
                            recoveryAttempted = true;
                            console.log(`🔄 Recovery strategy ${strategyName} prepared for retry`);
                            break;
                            
                        } catch (recoveryError) {
                            console.warn(`⚠️ Recovery strategy ${strategyName} failed:`, recoveryError.message);
                            // Continue to next strategy
                        }
                    }
                }
                
                // If no recovery was attempted, wait with exponential backoff
                if (!recoveryAttempted) {
                    const delay = Math.min(
                        this.baseDelay * Math.pow(2, attempt - 1),
                        this.maxDelay
                    );
                    console.log(`⏳ Waiting ${delay}ms before retry (exponential backoff)`);
                    await this.delay(delay);
                }
            }
        }
        
        // All attempts failed
        console.error(`❌ Operation "${operationName}" failed after ${this.maxRetries + 1} attempts`);
        this.errorStats.recoveryFailures++;
        
        // Potentially open circuit breaker
        this.checkCircuitBreaker(operationName);
        
        throw lastError;
    }
    
    /**
     * Record successful operation for circuit breaker
     */
    recordSuccess(operationName) {
        if (this.circuitBreakers.has(operationName)) {
            const circuitState = this.circuitBreakers.get(operationName);
            circuitState.consecutiveFailures = 0;
            circuitState.state = 'CLOSED';
            console.log(`🔄 Circuit breaker CLOSED for ${operationName} after successful operation`);
        }
    }
    
    /**
     * Record error for statistics and circuit breaker
     */
    recordError(error, operationName) {
        this.errorStats.totalErrors++;
        
        // Track by error type
        const errorType = error.name || 'UnknownError';
        this.errorStats.errorsByType.set(
            errorType,
            (this.errorStats.errorsByType.get(errorType) || 0) + 1
        );
        
        // Track by operation
        this.errorStats.errorsByOperation.set(
            operationName,
            (this.errorStats.errorsByOperation.get(operationName) || 0) + 1
        );
        
        // Update circuit breaker
        if (!this.circuitBreakers.has(operationName)) {
            this.circuitBreakers.set(operationName, {
                state: 'CLOSED',
                consecutiveFailures: 0,
                lastFailureTime: null
            });
        }
        
        const circuitState = this.circuitBreakers.get(operationName);
        circuitState.consecutiveFailures++;
        circuitState.lastFailureTime = Date.now();
    }
    
    /**
     * Check if circuit breaker should be opened
     */
    checkCircuitBreaker(operationName) {
        const circuitState = this.circuitBreakers.get(operationName);
        if (!circuitState) return;
        
        if (circuitState.consecutiveFailures >= this.circuitBreakerThreshold) {
            circuitState.state = 'OPEN';
            console.warn(`⚠️ Circuit breaker OPEN for ${operationName} after ${circuitState.consecutiveFailures} consecutive failures`);
        }
    }
    
    /**
     * Check if circuit breaker is open for an operation
     */
    isCircuitOpen(operationName) {
        const circuitState = this.circuitBreakers.get(operationName);
        if (!circuitState || circuitState.state !== 'OPEN') {
            return false;
        }
        
        // Check if timeout has passed (half-open state)
        const timeSinceFailure = Date.now() - circuitState.lastFailureTime;
        if (timeSinceFailure >= this.circuitBreakerTimeout) {
            circuitState.state = 'HALF_OPEN';
            console.log(`🔄 Circuit breaker HALF_OPEN for ${operationName} - allowing one test attempt`);
            return false;
        }
        
        return true;
    }
    
    /**
     * Get error statistics
     */
    getErrorStats() {
        const successRate = this.errorStats.totalOperations > 0 
            ? ((this.errorStats.totalOperations - this.errorStats.totalErrors) / this.errorStats.totalOperations * 100).toFixed(2)
            : 100;
            
        const recoveryRate = this.errorStats.recoveryFailures + this.errorStats.recoverySuccesses > 0
            ? (this.errorStats.recoverySuccesses / (this.errorStats.recoveryFailures + this.errorStats.recoverySuccesses) * 100).toFixed(2)
            : 100;
        
        return {
            totalOperations: this.errorStats.totalOperations,
            totalErrors: this.errorStats.totalErrors,
            successRate: `${successRate}%`,
            recoverySuccesses: this.errorStats.recoverySuccesses,
            recoveryFailures: this.errorStats.recoveryFailures,
            recoveryRate: `${recoveryRate}%`,
            errorsByType: Object.fromEntries(this.errorStats.errorsByType),
            errorsByOperation: Object.fromEntries(this.errorStats.errorsByOperation),
            circuitBreakers: Object.fromEntries(
                Array.from(this.circuitBreakers.entries()).map(([name, state]) => [
                    name, 
                    {
                        state: state.state,
                        consecutiveFailures: state.consecutiveFailures
                    }
                ])
            )
        };
    }
    
    /**
     * Utility delay function
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Reset circuit breaker for specific operation
     */
    resetCircuitBreaker(operationName) {
        if (this.circuitBreakers.has(operationName)) {
            this.circuitBreakers.get(operationName).state = 'CLOSED';
            this.circuitBreakers.get(operationName).consecutiveFailures = 0;
            console.log(`🔄 Circuit breaker manually reset for ${operationName}`);
        }
    }
    
    /**
     * Reset all circuit breakers
     */
    resetAllCircuitBreakers() {
        for (const [operationName, state] of this.circuitBreakers) {
            state.state = 'CLOSED';
            state.consecutiveFailures = 0;
        }
        console.log('🔄 All circuit breakers manually reset');
    }
}

// ============================================================================
// GLOBAL AVAILABILITY
// ============================================================================

// Make ErrorRecoveryFramework available globally
if (typeof window !== 'undefined') {
    window.ErrorRecoveryFramework = ErrorRecoveryFramework;
    console.log('✅ Error Recovery Framework loaded and available globally');
}

// Also export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorRecoveryFramework;
}
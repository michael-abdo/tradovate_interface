// ============================================================================
// DOM INTELLIGENCE CLIENT LIBRARY FOR TAMPERMONKEY SCRIPTS
// ============================================================================
// 
// This library provides Tampermonkey scripts with access to DOM Intelligence
// System capabilities including validated selectors, fallback strategies,
// performance monitoring, and health checking.
//
// Usage:
//   const domClient = new DOMIntelligenceClient();
//   const element = await domClient.findElement('symbol_input');
//   await domClient.click('order_submit_button');
//
// ============================================================================

class DOMIntelligenceClient {
    constructor(options = {}) {
        this.scriptName = options.scriptName || 'unknown_script';
        this.debugMode = options.debugMode || false;
        this.logger = new TampermonkeyLogger(this.scriptName, this.debugMode);
        
        // Performance tracking
        this.operationMetrics = [];
        this.maxMetricsHistory = 100;
        
        // Element registry cache
        this.elementCache = new Map();
        this.cacheTimeout = 30000; // 30 seconds
        
        // Health monitoring
        this.healthStatus = 'healthy';
        this.lastHealthCheck = Date.now();
        this.healthCheckInterval = 30000; // 30 seconds
        
        this.logger.info('DOM Intelligence Client initialized');
    }
    
    // ============================================================================
    // ELEMENT FINDING WITH INTELLIGENCE
    // ============================================================================
    
    async findElement(elementType, options = {}) {
        const startTime = performance.now();
        const operation = {
            type: 'findElement',
            elementType: elementType,
            timestamp: Date.now(),
            startTime: startTime
        };
        
        try {
            this.logger.debug(`Finding element: ${elementType}`);
            
            // Check cache first
            const cached = this.getCachedElement(elementType);
            if (cached && this.isElementValid(cached.element)) {
                operation.success = true;
                operation.duration = performance.now() - startTime;
                operation.method = 'cache';
                operation.selector = cached.selector;
                this.recordMetric(operation);
                return cached.element;
            }
            
            // Get element strategy from registry
            const strategy = this.getElementStrategy(elementType);
            if (!strategy) {
                throw new Error(`Unknown element type: ${elementType}`);
            }
            
            // Try selectors in order of priority
            const allSelectors = [...strategy.primarySelectors, ...strategy.fallbackSelectors];
            let element = null;
            let usedSelector = null;
            let fallbackDepth = 0;
            
            for (const selector of allSelectors) {
                try {
                    element = await this.waitForElement(selector, {
                        timeout: options.timeout || strategy.timeout || 5000,
                        checkVisibility: options.checkVisibility !== false
                    });
                    
                    if (element) {
                        usedSelector = selector;
                        
                        // Validate element using strategy validators
                        if (this.validateElement(element, strategy)) {
                            // Cache successful find
                            this.cacheElement(elementType, element, selector);
                            break;
                        } else {
                            this.logger.warning(`Element found but failed validation: ${selector}`);
                            element = null;
                        }
                    }
                } catch (e) {
                    this.logger.debug(`Selector failed: ${selector} - ${e.message}`);
                }
                
                fallbackDepth++;
            }
            
            if (!element) {
                throw new Error(`Element not found: ${elementType}`);
            }
            
            operation.success = true;
            operation.duration = performance.now() - startTime;
            operation.method = 'selector';
            operation.selector = usedSelector;
            operation.fallbackDepth = fallbackDepth;
            this.recordMetric(operation);
            
            this.logger.info(`Found element ${elementType} using selector: ${usedSelector}`);
            return element;
            
        } catch (error) {
            operation.success = false;
            operation.duration = performance.now() - startTime;
            operation.error = error.message;
            this.recordMetric(operation);
            
            this.logger.error(`Failed to find element ${elementType}: ${error.message}`);
            throw error;
        }
    }
    
    // ============================================================================
    // DOM OPERATIONS WITH VALIDATION
    // ============================================================================
    
    async click(elementType, options = {}) {
        const startTime = performance.now();
        const operation = {
            type: 'click',
            elementType: elementType,
            timestamp: Date.now(),
            startTime: startTime
        };
        
        try {
            const element = await this.findElement(elementType, options);
            
            // Pre-click validation
            if (!element.offsetParent && !options.allowHidden) {
                throw new Error('Element is not visible');
            }
            
            if (element.disabled && !options.allowDisabled) {
                throw new Error('Element is disabled');
            }
            
            // Perform click with event simulation
            const clickEvent = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window
            });
            
            element.dispatchEvent(clickEvent);
            
            operation.success = true;
            operation.duration = performance.now() - startTime;
            this.recordMetric(operation);
            
            this.logger.info(`Clicked element: ${elementType}`);
            return true;
            
        } catch (error) {
            operation.success = false;
            operation.duration = performance.now() - startTime;
            operation.error = error.message;
            this.recordMetric(operation);
            
            this.logger.error(`Failed to click ${elementType}: ${error.message}`);
            throw error;
        }
    }
    
    async input(elementType, value, options = {}) {
        const startTime = performance.now();
        const operation = {
            type: 'input',
            elementType: elementType,
            timestamp: Date.now(),
            startTime: startTime,
            value: value
        };
        
        try {
            const element = await this.findElement(elementType, options);
            
            // Input validation
            if (element.type === 'number' && isNaN(Number(value))) {
                throw new Error('Invalid numeric value');
            }
            
            if (element.readOnly && !options.allowReadOnly) {
                throw new Error('Element is read-only');
            }
            
            // Set value using React-compatible method
            element.focus();
            
            // For React components, we need to use the property descriptor setter
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            
            if (nativeInputValueSetter) {
                nativeInputValueSetter.call(element, value);
            } else {
                element.value = value;
            }
            
            // Trigger React events
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));
            
            operation.success = true;
            operation.duration = performance.now() - startTime;
            this.recordMetric(operation);
            
            this.logger.info(`Input to ${elementType}: ${value}`);
            return true;
            
        } catch (error) {
            operation.success = false;
            operation.duration = performance.now() - startTime;
            operation.error = error.message;
            this.recordMetric(operation);
            
            this.logger.error(`Failed to input to ${elementType}: ${error.message}`);
            throw error;
        }
    }
    
    async extractData(elementType, options = {}) {
        const startTime = performance.now();
        const operation = {
            type: 'extractData',
            elementType: elementType,
            timestamp: Date.now(),
            startTime: startTime
        };
        
        try {
            const element = await this.findElement(elementType, options);
            
            let data = null;
            
            if (options.attribute) {
                data = element.getAttribute(options.attribute);
            } else if (options.property) {
                data = element[options.property];
            } else if (element.tagName.toLowerCase() === 'input') {
                data = element.value;
            } else if (element.tagName.toLowerCase() === 'table') {
                data = this.extractTableData(element, options);
            } else {
                data = options.innerHTML ? element.innerHTML : element.textContent;
            }
            
            operation.success = true;
            operation.duration = performance.now() - startTime;
            operation.dataLength = data ? data.toString().length : 0;
            this.recordMetric(operation);
            
            this.logger.debug(`Extracted data from ${elementType}: ${data?.toString().substring(0, 100)}...`);
            return data;
            
        } catch (error) {
            operation.success = false;
            operation.duration = performance.now() - startTime;
            operation.error = error.message;
            this.recordMetric(operation);
            
            this.logger.error(`Failed to extract data from ${elementType}: ${error.message}`);
            throw error;
        }
    }
    
    // ============================================================================
    // UTILITY METHODS
    // ============================================================================
    
    async waitForElement(selector, options = {}) {
        const timeout = options.timeout || 10000;
        const interval = options.interval || 100;
        const checkVisibility = options.checkVisibility !== false;
        
        return new Promise((resolve, reject) => {
            let elapsed = 0;
            
            const check = () => {
                const element = document.querySelector(selector);
                
                if (element) {
                    // Check visibility if required
                    if (!checkVisibility || element.offsetParent !== null) {
                        return resolve(element);
                    }
                }
                
                elapsed += interval;
                if (elapsed >= timeout) {
                    return reject(new Error(`Element not found: ${selector}`));
                }
                
                setTimeout(check, interval);
            };
            
            check();
        });
    }
    
    validateElement(element, strategy) {
        try {
            // Run context validators
            if (strategy.contextValidators) {
                for (const validator of strategy.contextValidators) {
                    if (!validator(element)) {
                        return false;
                    }
                }
            }
            
            // Run functional validators
            if (strategy.functionalValidators) {
                for (const validator of strategy.functionalValidators) {
                    if (!validator(element)) {
                        return false;
                    }
                }
            }
            
            return true;
        } catch (e) {
            this.logger.warning(`Element validation error: ${e.message}`);
            return false;
        }
    }
    
    isElementValid(element) {
        return element && 
               element.parentNode && 
               document.contains(element);
    }
    
    cacheElement(elementType, element, selector) {
        this.elementCache.set(elementType, {
            element: element,
            selector: selector,
            timestamp: Date.now()
        });
    }
    
    getCachedElement(elementType) {
        const cached = this.elementCache.get(elementType);
        if (cached && (Date.now() - cached.timestamp) < this.cacheTimeout) {
            return cached;
        }
        
        // Clean up expired cache
        if (cached) {
            this.elementCache.delete(elementType);
        }
        
        return null;
    }
    
    extractTableData(table, options = {}) {
        const headers = [];
        const rows = [];
        
        // Extract headers
        const headerElements = table.querySelectorAll('th, [role="columnheader"]');
        headerElements.forEach(header => {
            headers.push(header.textContent.trim());
        });
        
        // Extract rows
        const rowElements = table.querySelectorAll('tr, .public_fixedDataTable_bodyRow');
        rowElements.forEach(row => {
            const cells = row.querySelectorAll('td, [role="gridcell"]');
            if (cells.length > 0) {
                const rowData = {};
                cells.forEach((cell, index) => {
                    const headerName = headers[index] || `column_${index}`;
                    rowData[headerName] = cell.textContent.trim();
                });
                rows.push(rowData);
            }
        });
        
        return {
            headers: headers,
            rows: rows,
            rowCount: rows.length
        };
    }
    
    // ============================================================================
    // ELEMENT REGISTRY
    // ============================================================================
    
    getElementStrategy(elementType) {
        // Simplified element registry for Tampermonkey scripts
        // This mirrors the TradovateElementRegistry from the Python side
        const elementRegistry = {
            'symbol_input': {
                primarySelectors: ['#symbolInput', '.search-box--input[placeholder*="symbol" i]'],
                fallbackSelectors: ['.symbol-search input', '.instrument-selector input'],
                timeout: 3000,
                contextValidators: [
                    elem => elem.type.toLowerCase() === 'text',
                    elem => elem.placeholder.toLowerCase().includes('symbol') || elem.placeholder.toLowerCase().includes('instrument')
                ]
            },
            
            'order_submit_button': {
                primarySelectors: ['.btn-group .btn-primary', 'button[type="submit"].order-submit'],
                fallbackSelectors: ['.trading-panel button.btn-primary', '.order-entry button:last-child'],
                timeout: 2000,
                functionalValidators: [
                    elem => elem.tagName.toLowerCase() === 'button',
                    elem => elem.closest('.order, .trading, .trade') !== null,
                    elem => !elem.disabled
                ]
            },
            
            'account_selector': {
                primarySelectors: ['.pane.account-selector.dropdown [data-toggle="dropdown"]', '.account-switcher button'],
                fallbackSelectors: ['.user-account .dropdown', 'button:has(.account-name)'],
                timeout: 3000,
                contextValidators: [
                    elem => elem.closest('.account, .user, .profile') !== null
                ]
            },
            
            'login_username': {
                primarySelectors: ['#name-input', 'input[name="username"]'],
                fallbackSelectors: ['input[placeholder*="username" i]', '.login-form input[type="text"]:first-child'],
                timeout: 5000
            },
            
            'login_password': {
                primarySelectors: ['#password-input', 'input[name="password"]'],
                fallbackSelectors: ['input[placeholder*="password" i]', '.login-form input[type="password"]'],
                timeout: 5000
            },
            
            'market_data_table': {
                primarySelectors: ['.module.positions.data-table', '.public_fixedDataTable_main'],
                fallbackSelectors: ['.trading-table', '.data-grid.market'],
                timeout: 5000
            },
            
            'risk_settings_modal': {
                primarySelectors: ['.risk-settings-modal', '.modal.risk-config'],
                fallbackSelectors: ['.modal-dialog.settings', '.config-modal'],
                timeout: 10000
            },
            
            'risk_settings_button': {
                primarySelectors: ['button:contains("Risk Settings")', '[title*="Risk Settings"]'],
                fallbackSelectors: ['.risk-btn', 'button[class*="risk"]'],
                timeout: 5000
            }
        };
        
        return elementRegistry[elementType];
    }
    
    // ============================================================================
    // PERFORMANCE MONITORING
    // ============================================================================
    
    recordMetric(operation) {
        this.operationMetrics.push(operation);
        
        // Keep metrics history limited
        if (this.operationMetrics.length > this.maxMetricsHistory) {
            this.operationMetrics = this.operationMetrics.slice(-this.maxMetricsHistory);
        }
        
        // Update health status
        this.updateHealthStatus();
    }
    
    updateHealthStatus() {
        const now = Date.now();
        if (now - this.lastHealthCheck < this.healthCheckInterval) {
            return;
        }
        
        this.lastHealthCheck = now;
        
        if (this.operationMetrics.length < 5) {
            return; // Not enough data
        }
        
        // Check recent performance (last 10 operations)
        const recentOps = this.operationMetrics.slice(-10);
        const successRate = recentOps.filter(op => op.success).length / recentOps.length;
        const avgDuration = recentOps.reduce((sum, op) => sum + op.duration, 0) / recentOps.length;
        
        // Determine health status
        if (successRate < 0.5) {
            this.healthStatus = 'critical';
        } else if (successRate < 0.7 || avgDuration > 5000) {
            this.healthStatus = 'degraded';
        } else if (successRate < 0.9 || avgDuration > 2000) {
            this.healthStatus = 'warning';
        } else {
            this.healthStatus = 'healthy';
        }
        
        this.logger.debug(`Health status: ${this.healthStatus} (success: ${(successRate * 100).toFixed(1)}%, avg: ${avgDuration.toFixed(0)}ms)`);
    }
    
    getPerformanceReport() {
        if (this.operationMetrics.length === 0) {
            return { message: 'No operations recorded' };
        }
        
        const totalOps = this.operationMetrics.length;
        const successfulOps = this.operationMetrics.filter(op => op.success).length;
        const successRate = successfulOps / totalOps;
        
        const durations = this.operationMetrics.map(op => op.duration);
        const avgDuration = durations.reduce((sum, d) => sum + d, 0) / durations.length;
        const maxDuration = Math.max(...durations);
        const minDuration = Math.min(...durations);
        
        const elementTypes = [...new Set(this.operationMetrics.map(op => op.elementType))];
        const operationTypes = [...new Set(this.operationMetrics.map(op => op.type))];
        
        return {
            healthStatus: this.healthStatus,
            totalOperations: totalOps,
            successfulOperations: successfulOps,
            successRate: successRate,
            averageDuration: avgDuration,
            maxDuration: maxDuration,
            minDuration: minDuration,
            elementTypes: elementTypes,
            operationTypes: operationTypes,
            lastUpdate: new Date().toISOString()
        };
    }
}

// ============================================================================
// LOGGER FOR TAMPERMONKEY SCRIPTS
// ============================================================================

class TampermonkeyLogger {
    constructor(scriptName, debugMode = false) {
        this.scriptName = scriptName;
        this.debugMode = debugMode;
        this.prefix = `[${scriptName}][DOM-Intelligence]`;
    }
    
    debug(message) {
        if (this.debugMode) {
            console.log(`${this.prefix}[DEBUG] ${message}`);
        }
    }
    
    info(message) {
        console.log(`${this.prefix}[INFO] ${message}`);
    }
    
    warning(message) {
        console.warn(`${this.prefix}[WARN] ${message}`);
    }
    
    error(message) {
        console.error(`${this.prefix}[ERROR] ${message}`);
    }
}

// ============================================================================
// HELPER FUNCTIONS FOR BACKWARD COMPATIBILITY
// ============================================================================

// Enhanced waitForElement function that uses DOM Intelligence
function waitForElementIntelligent(elementType, options = {}) {
    const client = new DOMIntelligenceClient({ scriptName: 'legacy_script' });
    return client.findElement(elementType, options);
}

// Enhanced click function with validation
function clickElementIntelligent(elementType, options = {}) {
    const client = new DOMIntelligenceClient({ scriptName: 'legacy_script' });
    return client.click(elementType, options);
}

// Enhanced input function with validation
function inputToElementIntelligent(elementType, value, options = {}) {
    const client = new DOMIntelligenceClient({ scriptName: 'legacy_script' });
    return client.input(elementType, value, options);
}

// Global instance for scripts that want to share a client
window.DOMIntelligence = new DOMIntelligenceClient({ 
    scriptName: 'global_client',
    debugMode: localStorage.getItem('dom_intelligence_debug') === 'true'
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DOMIntelligenceClient, TampermonkeyLogger };
}
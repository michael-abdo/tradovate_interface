// ==UserScript==
// @name         Validation Test Utilities
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Controlled error simulation and stress testing for Order Validation Framework
// @author       Trading System
// @match        https://trader.tradovate.com/
// @icon         https://www.google.com/s2/favicons?sz=64&domain=tradovate.com
// @grant        none
// @updateURL    http://localhost:8080/validation_test_utilities.js
// @downloadURL  http://localhost:8080/validation_test_utilities.js
// ==/UserScript==

(function() {
    'use strict';
    
    console.log('Validation Test Utilities initializing...');
    
    // Error Simulation Module
    window.ValidationErrorSimulator = class ValidationErrorSimulator {
        constructor() {
            this.activeSimulations = new Map();
            this.simulationHistory = [];
            this.originalFunctions = new Map();
        }
        
        // Simulate different error scenarios
        simulateError(errorType, duration = 5000) {
            console.log(`🔴 Simulating error: ${errorType} for ${duration}ms`);
            
            switch (errorType) {
                case 'INSUFFICIENT_FUNDS':
                    this.simulateInsufficientFunds(duration);
                    break;
                case 'MARKET_CLOSED':
                    this.simulateMarketClosed(duration);
                    break;
                case 'CONNECTION_TIMEOUT':
                    this.simulateConnectionTimeout(duration);
                    break;
                case 'INVALID_CONTRACT':
                    this.simulateInvalidContract(duration);
                    break;
                case 'ORDER_REJECTION':
                    this.simulateOrderRejection(duration);
                    break;
                case 'DOM_ELEMENT_MISSING':
                    this.simulateDOMElementMissing(duration);
                    break;
                case 'NETWORK_FAILURE':
                    this.simulateNetworkFailure(duration);
                    break;
                default:
                    console.error(`Unknown error type: ${errorType}`);
                    return false;
            }
            
            // Record simulation
            this.simulationHistory.push({
                type: errorType,
                startTime: Date.now(),
                duration: duration,
                active: true
            });
            
            // Auto-clear after duration
            setTimeout(() => this.clearSimulation(errorType), duration);
            
            return true;
        }
        
        // Simulate insufficient funds error
        simulateInsufficientFunds(duration) {
            const simulationId = 'insufficient_funds';
            
            // Override order submission to inject error
            if (window.autoOrderValidator && !this.originalFunctions.has(simulationId)) {
                const original = window.autoOrderValidator.validatePreSubmission;
                this.originalFunctions.set(simulationId, original);
                
                window.autoOrderValidator.validatePreSubmission = async function(orderData) {
                    // Call original validation first
                    const result = await original.call(this, orderData);
                    
                    // Inject insufficient funds error
                    result.valid = false;
                    result.errors.push('Insufficient funds to place order');
                    result.simulatedError = true;
                    
                    return result;
                };
                
                this.activeSimulations.set(simulationId, true);
            }
        }
        
        // Simulate market closed error
        simulateMarketClosed(duration) {
            const simulationId = 'market_closed';
            
            // Create fake error modal
            const errorModal = document.createElement('div');
            errorModal.className = 'error-modal error-simulation';
            errorModal.innerHTML = `
                <div style="
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: #f44336;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    z-index: 10001;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                ">
                    <h3>Market Closed</h3>
                    <p>The market is currently closed. Orders cannot be placed at this time.</p>
                    <small>This is a simulated error for testing</small>
                </div>
            `;
            document.body.appendChild(errorModal);
            
            this.activeSimulations.set(simulationId, errorModal);
        }
        
        // Simulate connection timeout
        simulateConnectionTimeout(duration) {
            const simulationId = 'connection_timeout';
            
            // Override network requests to simulate timeout
            if (!this.originalFunctions.has(simulationId)) {
                const originalFetch = window.fetch;
                this.originalFunctions.set(simulationId, originalFetch);
                
                window.fetch = function(...args) {
                    // Simulate timeout for trading endpoints
                    if (args[0] && args[0].includes('/order')) {
                        return new Promise((resolve, reject) => {
                            setTimeout(() => {
                                reject(new Error('Connection timeout (simulated)'));
                            }, 3000);
                        });
                    }
                    return originalFetch.apply(this, args);
                };
                
                this.activeSimulations.set(simulationId, true);
            }
        }
        
        // Simulate invalid contract error
        simulateInvalidContract(duration) {
            const simulationId = 'invalid_contract';
            
            if (window.autoOrderValidator && !this.originalFunctions.has(simulationId)) {
                const original = window.autoOrderValidator.validatePreSubmission;
                this.originalFunctions.set(simulationId, original);
                
                window.autoOrderValidator.validatePreSubmission = async function(orderData) {
                    const result = await original.call(this, orderData);
                    
                    // Inject invalid contract error
                    result.valid = false;
                    result.errors.push('Invalid contract specification: Contract not found');
                    result.simulatedError = true;
                    
                    return result;
                };
                
                this.activeSimulations.set(simulationId, true);
            }
        }
        
        // Simulate order rejection
        simulateOrderRejection(duration) {
            const simulationId = 'order_rejection';
            
            if (window.autoOrderValidator && !this.originalFunctions.has(simulationId)) {
                const original = window.autoOrderValidator.validatePostSubmission;
                this.originalFunctions.set(simulationId, original);
                
                window.autoOrderValidator.validatePostSubmission = async function(orderId) {
                    // Simulate rejection after short delay
                    await new Promise(resolve => setTimeout(resolve, 500));
                    
                    return {
                        success: false,
                        confirmed: false,
                        errors: ['Order rejected by exchange: Price outside valid range'],
                        simulatedError: true
                    };
                };
                
                this.activeSimulations.set(simulationId, true);
            }
        }
        
        // Simulate missing DOM elements
        simulateDOMElementMissing(duration) {
            const simulationId = 'dom_missing';
            
            // Temporarily hide critical elements
            const elements = [
                '.btn-primary',
                '.numeric-input',
                '.order-type'
            ];
            
            const hiddenElements = [];
            elements.forEach(selector => {
                const elem = document.querySelector(selector);
                if (elem) {
                    elem.style.display = 'none';
                    hiddenElements.push(elem);
                }
            });
            
            this.activeSimulations.set(simulationId, hiddenElements);
        }
        
        // Simulate network failure
        simulateNetworkFailure(duration) {
            const simulationId = 'network_failure';
            
            // Override XMLHttpRequest
            if (!this.originalFunctions.has(simulationId)) {
                const originalXHR = window.XMLHttpRequest;
                this.originalFunctions.set(simulationId, originalXHR);
                
                window.XMLHttpRequest = function() {
                    const xhr = new originalXHR();
                    const originalOpen = xhr.open;
                    
                    xhr.open = function(method, url, ...args) {
                        // Fail trading-related requests
                        if (url && (url.includes('/order') || url.includes('/trade'))) {
                            setTimeout(() => {
                                xhr.dispatchEvent(new Event('error'));
                            }, 100);
                        }
                        return originalOpen.call(this, method, url, ...args);
                    };
                    
                    return xhr;
                };
                
                this.activeSimulations.set(simulationId, true);
            }
        }
        
        // Clear specific simulation
        clearSimulation(errorType) {
            console.log(`🟢 Clearing error simulation: ${errorType}`);
            
            const simulationMap = {
                'INSUFFICIENT_FUNDS': 'insufficient_funds',
                'MARKET_CLOSED': 'market_closed',
                'CONNECTION_TIMEOUT': 'connection_timeout',
                'INVALID_CONTRACT': 'invalid_contract',
                'ORDER_REJECTION': 'order_rejection',
                'DOM_ELEMENT_MISSING': 'dom_missing',
                'NETWORK_FAILURE': 'network_failure'
            };
            
            const simulationId = simulationMap[errorType];
            if (!simulationId) return;
            
            // Restore original functions
            if (this.originalFunctions.has(simulationId)) {
                switch (simulationId) {
                    case 'insufficient_funds':
                    case 'invalid_contract':
                        if (window.autoOrderValidator) {
                            window.autoOrderValidator.validatePreSubmission = this.originalFunctions.get(simulationId);
                        }
                        break;
                    case 'order_rejection':
                        if (window.autoOrderValidator) {
                            window.autoOrderValidator.validatePostSubmission = this.originalFunctions.get(simulationId);
                        }
                        break;
                    case 'connection_timeout':
                        window.fetch = this.originalFunctions.get(simulationId);
                        break;
                    case 'network_failure':
                        window.XMLHttpRequest = this.originalFunctions.get(simulationId);
                        break;
                }
                this.originalFunctions.delete(simulationId);
            }
            
            // Clean up DOM elements
            if (simulationId === 'market_closed') {
                const modal = this.activeSimulations.get(simulationId);
                if (modal && modal.parentNode) {
                    modal.parentNode.removeChild(modal);
                }
            } else if (simulationId === 'dom_missing') {
                const elements = this.activeSimulations.get(simulationId);
                if (elements) {
                    elements.forEach(elem => {
                        elem.style.display = '';
                    });
                }
            }
            
            this.activeSimulations.delete(simulationId);
            
            // Update history
            const historyEntry = this.simulationHistory.find(
                h => h.type === errorType && h.active
            );
            if (historyEntry) {
                historyEntry.active = false;
                historyEntry.endTime = Date.now();
            }
        }
        
        // Clear all simulations
        clearAllSimulations() {
            console.log('🟢 Clearing all error simulations');
            
            const activeTypes = [
                'INSUFFICIENT_FUNDS',
                'MARKET_CLOSED',
                'CONNECTION_TIMEOUT',
                'INVALID_CONTRACT',
                'ORDER_REJECTION',
                'DOM_ELEMENT_MISSING',
                'NETWORK_FAILURE'
            ];
            
            activeTypes.forEach(type => this.clearSimulation(type));
        }
        
        // Get simulation status
        getStatus() {
            return {
                activeSimulations: Array.from(this.activeSimulations.keys()),
                simulationHistory: this.simulationHistory,
                isActive: this.activeSimulations.size > 0
            };
        }
    };
    
    // Performance Load Simulator
    window.PerformanceLoadSimulator = class PerformanceLoadSimulator {
        constructor() {
            this.loadTests = [];
            this.isRunning = false;
        }
        
        // Simulate high-frequency validation load
        async simulateHighFrequencyLoad(duration = 10000, frequency = 50) {
            console.log(`🔥 Starting high-frequency load test: ${frequency} validations/second for ${duration}ms`);
            
            this.isRunning = true;
            const startTime = Date.now();
            const interval = 1000 / frequency;
            let validationCount = 0;
            
            const testOrder = {
                orderType: 'MARKET',
                quantity: 1,
                symbol: 'ES',
                account: 'LOAD_TEST',
                side: 'BUY'
            };
            
            const loadTest = {
                startTime: startTime,
                duration: duration,
                frequency: frequency,
                results: []
            };
            
            const runValidation = async () => {
                if (!this.isRunning || Date.now() - startTime > duration) {
                    this.completeLoadTest(loadTest);
                    return;
                }
                
                const validationStart = performance.now();
                
                try {
                    if (window.autoOrderValidator) {
                        await window.autoOrderValidator.validatePreSubmission(testOrder);
                    }
                    
                    const validationEnd = performance.now();
                    const validationTime = validationEnd - validationStart;
                    
                    loadTest.results.push({
                        time: validationTime,
                        timestamp: Date.now()
                    });
                    
                    validationCount++;
                    
                } catch (error) {
                    console.error('Load test validation error:', error);
                }
                
                // Schedule next validation
                setTimeout(runValidation, interval);
            };
            
            // Start load test
            this.loadTests.push(loadTest);
            runValidation();
            
            return loadTest;
        }
        
        // Simulate burst load
        async simulateBurstLoad(burstSize = 100, burstCount = 5, delayBetween = 2000) {
            console.log(`💥 Starting burst load test: ${burstCount} bursts of ${burstSize} validations`);
            
            this.isRunning = true;
            const results = [];
            
            for (let burst = 0; burst < burstCount && this.isRunning; burst++) {
                console.log(`Burst ${burst + 1}/${burstCount} starting...`);
                
                const burstPromises = [];
                const burstStart = performance.now();
                
                // Create burst of validations
                for (let i = 0; i < burstSize; i++) {
                    const promise = this.runSingleValidation(burst, i);
                    burstPromises.push(promise);
                }
                
                // Wait for burst to complete
                const burstResults = await Promise.all(burstPromises);
                const burstEnd = performance.now();
                
                results.push({
                    burstNumber: burst + 1,
                    burstSize: burstSize,
                    totalTime: burstEnd - burstStart,
                    averageTime: burstResults.reduce((sum, r) => sum + r.time, 0) / burstResults.length,
                    maxTime: Math.max(...burstResults.map(r => r.time)),
                    results: burstResults
                });
                
                // Delay between bursts
                if (burst < burstCount - 1) {
                    await new Promise(resolve => setTimeout(resolve, delayBetween));
                }
            }
            
            this.isRunning = false;
            return results;
        }
        
        // Run single validation for testing
        async runSingleValidation(burstNumber, index) {
            const testOrder = {
                orderType: 'MARKET',
                quantity: 1,
                symbol: 'ES',
                account: `BURST_${burstNumber}_${index}`,
                side: index % 2 === 0 ? 'BUY' : 'SELL'
            };
            
            const start = performance.now();
            
            try {
                if (window.autoOrderValidator) {
                    await window.autoOrderValidator.validatePreSubmission(testOrder);
                }
            } catch (error) {
                console.error(`Validation error in burst ${burstNumber}, index ${index}:`, error);
            }
            
            const end = performance.now();
            
            return {
                burstNumber: burstNumber,
                index: index,
                time: end - start,
                timestamp: Date.now()
            };
        }
        
        // Complete load test and generate report
        completeLoadTest(loadTest) {
            this.isRunning = false;
            
            const endTime = Date.now();
            const actualDuration = endTime - loadTest.startTime;
            const validationTimes = loadTest.results.map(r => r.time);
            
            const report = {
                duration: actualDuration,
                totalValidations: validationTimes.length,
                actualFrequency: (validationTimes.length / actualDuration) * 1000,
                averageTime: validationTimes.reduce((sum, t) => sum + t, 0) / validationTimes.length,
                minTime: Math.min(...validationTimes),
                maxTime: Math.max(...validationTimes),
                p95Time: this.calculatePercentile(validationTimes, 0.95),
                p99Time: this.calculatePercentile(validationTimes, 0.99),
                violations: validationTimes.filter(t => t > 10).length,
                violationRate: (validationTimes.filter(t => t > 10).length / validationTimes.length) * 100
            };
            
            console.log('📊 Load Test Complete:', report);
            
            // Check performance health
            if (window.autoOrderValidator) {
                const perfReport = window.autoOrderValidator.getPerformanceReport();
                console.log('📈 Framework Performance After Load:', perfReport);
            }
            
            return report;
        }
        
        // Calculate percentile
        calculatePercentile(array, percentile) {
            const sorted = array.slice().sort((a, b) => a - b);
            const index = Math.floor(sorted.length * percentile);
            return sorted[index];
        }
        
        // Stop running tests
        stop() {
            console.log('🛑 Stopping load simulator');
            this.isRunning = false;
        }
    };
    
    // Stress Test Runner
    window.stressTest = async function(iterations = 1000) {
        console.log(`🏃 Running stress test with ${iterations} iterations...`);
        
        if (!window.autoOrderValidator) {
            console.error('Order Validation Framework not loaded');
            return;
        }
        
        const times = [];
        const testOrder = {
            orderType: 'MARKET',
            quantity: 1,
            symbol: 'ES',
            account: 'STRESS_TEST',
            side: 'BUY'
        };
        
        const startTime = performance.now();
        
        for (let i = 0; i < iterations; i++) {
            const iterStart = performance.now();
            
            try {
                await window.autoOrderValidator.validatePreSubmission(testOrder);
            } catch (error) {
                console.error(`Stress test error at iteration ${i}:`, error);
            }
            
            const iterEnd = performance.now();
            times.push(iterEnd - iterStart);
            
            // Progress update every 100 iterations
            if ((i + 1) % 100 === 0) {
                console.log(`Progress: ${i + 1}/${iterations} (${((i + 1) / iterations * 100).toFixed(1)}%)`);
            }
        }
        
        const endTime = performance.now();
        const totalDuration = endTime - startTime;
        
        // Calculate statistics
        const avg = times.reduce((a, b) => a + b) / times.length;
        const violations = times.filter(t => t > 10).length;
        const sorted = times.slice().sort((a, b) => a - b);
        
        const results = {
            iterations: iterations,
            totalDuration: totalDuration,
            averageTime: avg,
            minTime: Math.min(...times),
            maxTime: Math.max(...times),
            medianTime: sorted[Math.floor(sorted.length / 2)],
            p95Time: sorted[Math.floor(sorted.length * 0.95)],
            p99Time: sorted[Math.floor(sorted.length * 0.99)],
            violations: violations,
            violationRate: (violations / iterations * 100).toFixed(1) + '%',
            compliant: avg < 10
        };
        
        console.log('🎯 Stress Test Results:', results);
        
        // Show performance report
        const perfReport = window.autoOrderValidator.getPerformanceReport();
        console.log('📊 Final Performance State:', perfReport);
        
        return results;
    };
    
    // Initialize global instances
    window.errorSimulator = new window.ValidationErrorSimulator();
    window.loadSimulator = new window.PerformanceLoadSimulator();
    
    // Add test control panel
    function createTestControlPanel() {
        const panel = document.createElement('div');
        panel.id = 'validation-test-panel';
        panel.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(30, 30, 40, 0.95);
            border: 1px solid #666;
            border-radius: 5px;
            padding: 15px;
            color: #fff;
            font-family: monospace;
            font-size: 12px;
            z-index: 9999;
            max-width: 300px;
        `;
        
        panel.innerHTML = `
            <h4 style="margin: 0 0 10px 0;">🧪 Validation Test Controls</h4>
            
            <div style="margin-bottom: 10px;">
                <label>Error Simulation:</label>
                <select id="error-type" style="width: 100%; margin: 5px 0;">
                    <option value="">Select Error Type</option>
                    <option value="INSUFFICIENT_FUNDS">Insufficient Funds</option>
                    <option value="MARKET_CLOSED">Market Closed</option>
                    <option value="CONNECTION_TIMEOUT">Connection Timeout</option>
                    <option value="INVALID_CONTRACT">Invalid Contract</option>
                    <option value="ORDER_REJECTION">Order Rejection</option>
                    <option value="DOM_ELEMENT_MISSING">DOM Element Missing</option>
                    <option value="NETWORK_FAILURE">Network Failure</option>
                </select>
                <button id="simulate-error" style="width: 48%; margin-right: 4%;">Simulate</button>
                <button id="clear-errors" style="width: 48%;">Clear All</button>
            </div>
            
            <div style="margin-bottom: 10px;">
                <label>Load Testing:</label>
                <button id="high-freq-test" style="width: 100%; margin: 5px 0;">High Frequency (50/sec)</button>
                <button id="burst-test" style="width: 100%; margin: 5px 0;">Burst Load (5x100)</button>
                <button id="stress-test" style="width: 100%; margin: 5px 0;">Stress Test (1000x)</button>
            </div>
            
            <div id="test-status" style="
                margin-top: 10px;
                padding: 10px;
                background: rgba(50, 50, 60, 0.5);
                border-radius: 3px;
                font-size: 11px;
            ">
                Ready for testing
            </div>
            
            <button id="close-test-panel" style="
                position: absolute;
                top: 5px;
                right: 5px;
                background: transparent;
                border: none;
                color: #fff;
                cursor: pointer;
                font-size: 16px;
            ">×</button>
        `;
        
        document.body.appendChild(panel);
        
        // Event handlers
        document.getElementById('simulate-error').onclick = () => {
            const errorType = document.getElementById('error-type').value;
            if (errorType) {
                window.errorSimulator.simulateError(errorType, 10000);
                updateTestStatus(`Simulating ${errorType} for 10 seconds...`);
            }
        };
        
        document.getElementById('clear-errors').onclick = () => {
            window.errorSimulator.clearAllSimulations();
            updateTestStatus('All error simulations cleared');
        };
        
        document.getElementById('high-freq-test').onclick = () => {
            window.loadSimulator.simulateHighFrequencyLoad(10000, 50);
            updateTestStatus('Running high frequency load test...');
        };
        
        document.getElementById('burst-test').onclick = () => {
            window.loadSimulator.simulateBurstLoad(100, 5, 2000);
            updateTestStatus('Running burst load test...');
        };
        
        document.getElementById('stress-test').onclick = () => {
            window.stressTest(1000);
            updateTestStatus('Running stress test (1000 iterations)...');
        };
        
        document.getElementById('close-test-panel').onclick = () => {
            panel.style.display = 'none';
        };
        
        function updateTestStatus(message) {
            document.getElementById('test-status').textContent = message;
        }
    }
    
    // Initialize test panel after page load
    setTimeout(() => {
        createTestControlPanel();
        console.log('Validation Test Utilities ready. Use window.errorSimulator and window.loadSimulator for testing.');
    }, 3000);
    
})();
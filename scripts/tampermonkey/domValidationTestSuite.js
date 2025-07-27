// ==UserScript==
// @name         DOM Validation Test Suite
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Comprehensive test suite for DOM validation standardization
// @match        https://trader.tradovate.com/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';
    
    console.log('🧪 DOM Validation Test Suite - Starting comprehensive validation tests');
    
    // ============================================================================
    // TEST FRAMEWORK
    // ============================================================================
    
    class DOMValidationTestSuite {
        constructor() {
            this.testResults = {
                passed: 0,
                failed: 0,
                total: 0,
                details: []
            };
            this.startTime = Date.now();
        }
        
        async runTest(testName, testFunction, timeout = 10000) {
            console.log(`🔍 Running test: ${testName}`);
            this.testResults.total++;
            
            const testStart = Date.now();
            
            try {
                const timeoutPromise = new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Test timeout')), timeout)
                );
                
                const result = await Promise.race([testFunction(), timeoutPromise]);
                const duration = Date.now() - testStart;
                
                if (result.success) {
                    this.testResults.passed++;
                    console.log(`✅ PASS: ${testName} (${duration}ms)`);
                    this.testResults.details.push({
                        test: testName,
                        status: 'PASS',
                        duration,
                        message: result.message || 'Test passed'
                    });
                } else {
                    this.testResults.failed++;
                    console.error(`❌ FAIL: ${testName} (${duration}ms) - ${result.message}`);
                    this.testResults.details.push({
                        test: testName,
                        status: 'FAIL',
                        duration,
                        message: result.message,
                        error: result.error
                    });
                }
            } catch (error) {
                const duration = Date.now() - testStart;
                this.testResults.failed++;
                console.error(`❌ ERROR: ${testName} (${duration}ms) - ${error.message}`);
                this.testResults.details.push({
                    test: testName,
                    status: 'ERROR',
                    duration,
                    message: error.message,
                    error: error.stack
                });
            }
        }
        
        generateReport() {
            const totalDuration = Date.now() - this.startTime;
            const successRate = this.testResults.total > 0 
                ? (this.testResults.passed / this.testResults.total * 100).toFixed(2)
                : 0;
            
            console.log('\n' + '='.repeat(80));
            console.log('🧪 DOM VALIDATION TEST SUITE - FINAL REPORT');
            console.log('='.repeat(80));
            console.log(`📊 Results: ${this.testResults.passed}/${this.testResults.total} tests passed (${successRate}%)`);
            console.log(`⏱️ Total Duration: ${totalDuration}ms`);
            console.log(`✅ Passed: ${this.testResults.passed}`);
            console.log(`❌ Failed: ${this.testResults.failed}`);
            
            if (this.testResults.failed > 0) {
                console.log('\n❌ FAILED TESTS:');
                this.testResults.details
                    .filter(test => test.status !== 'PASS')
                    .forEach(test => {
                        console.log(`  • ${test.test}: ${test.message}`);
                    });
            }
            
            console.log('\n📋 DETAILED RESULTS:');
            this.testResults.details.forEach(test => {
                const icon = test.status === 'PASS' ? '✅' : '❌';
                console.log(`  ${icon} ${test.test} (${test.duration}ms): ${test.message}`);
            });
            
            return {
                success: this.testResults.failed === 0,
                successRate,
                totalDuration,
                ...this.testResults
            };
        }
    }
    
    // ============================================================================
    // DOM HELPERS VALIDATION TESTS
    // ============================================================================
    
    async function testDOMHelpersLoading() {
        return new Promise(async (resolve) => {
            try {
                // Test if domHelpers is available
                if (!window.domHelpers) {
                    // Try to load it
                    const script = document.createElement('script');
                    script.src = '/scripts/tampermonkey/domHelpers.js';
                    document.head.appendChild(script);
                    
                    await new Promise((scriptResolve, scriptReject) => {
                        script.onload = scriptResolve;
                        script.onerror = scriptReject;
                        setTimeout(() => scriptReject(new Error('Script load timeout')), 5000);
                    });
                }
                
                if (window.domHelpers) {
                    const expectedFunctions = [
                        'waitForElement', 'validateElementExists', 'validateElementVisible',
                        'validateElementClickable', 'validateFormFieldValue', 'findElementWithValidation',
                        'safeClick', 'safeSetValue', 'safeSelectDropdownOption', 'safeModalAction',
                        'safeExtractTableData', 'safeDragAndDrop'
                    ];
                    
                    const missingFunctions = expectedFunctions.filter(func => 
                        typeof window.domHelpers[func] !== 'function'
                    );
                    
                    if (missingFunctions.length === 0) {
                        resolve({ 
                            success: true, 
                            message: `All ${expectedFunctions.length} DOM helper functions loaded successfully` 
                        });
                    } else {
                        resolve({ 
                            success: false, 
                            message: `Missing functions: ${missingFunctions.join(', ')}` 
                        });
                    }
                } else {
                    resolve({ success: false, message: 'DOM helpers not available after load attempt' });
                }
            } catch (error) {
                resolve({ success: false, message: `Error loading DOM helpers: ${error.message}` });
            }
        });
    }
    
    async function testValidateElementExists() {
        return new Promise((resolve) => {
            try {
                // Test with existing element (body should always exist)
                const bodyExists = window.domHelpers.validateElementExists('body');
                
                // Test with non-existing element
                const fakeExists = window.domHelpers.validateElementExists('.fake-element-12345');
                
                if (bodyExists === true && fakeExists === false) {
                    resolve({ success: true, message: 'validateElementExists working correctly' });
                } else {
                    resolve({ 
                        success: false, 
                        message: `Validation failed: body=${bodyExists}, fake=${fakeExists}` 
                    });
                }
            } catch (error) {
                resolve({ success: false, message: `Error: ${error.message}` });
            }
        });
    }
    
    async function testValidateElementVisible() {
        return new Promise((resolve) => {
            try {
                // Test with visible element
                const body = document.querySelector('body');
                const bodyVisible = window.domHelpers.validateElementVisible(body);
                
                // Create hidden element for testing
                const hiddenDiv = document.createElement('div');
                hiddenDiv.style.display = 'none';
                document.body.appendChild(hiddenDiv);
                
                const hiddenVisible = window.domHelpers.validateElementVisible(hiddenDiv);
                
                // Cleanup
                hiddenDiv.remove();
                
                if (bodyVisible === true && hiddenVisible === false) {
                    resolve({ success: true, message: 'validateElementVisible working correctly' });
                } else {
                    resolve({ 
                        success: false, 
                        message: `Validation failed: body=${bodyVisible}, hidden=${hiddenVisible}` 
                    });
                }
            } catch (error) {
                resolve({ success: false, message: `Error: ${error.message}` });
            }
        });
    }
    
    async function testWaitForElement() {
        return new Promise(async (resolve) => {
            try {
                // Test immediate element
                const bodyResult = await window.domHelpers.waitForElement('body', 1000);
                
                if (!bodyResult) {
                    resolve({ success: false, message: 'Failed to find existing element (body)' });
                    return;
                }
                
                // Test timeout with non-existing element
                const startTime = Date.now();
                const fakeResult = await window.domHelpers.waitForElement('.fake-element-12345', 1000);
                const duration = Date.now() - startTime;
                
                if (fakeResult === null && duration >= 950 && duration <= 1100) {
                    resolve({ success: true, message: `waitForElement working correctly (timeout: ${duration}ms)` });
                } else {
                    resolve({ 
                        success: false, 
                        message: `Timeout test failed: result=${fakeResult}, duration=${duration}ms` 
                    });
                }
            } catch (error) {
                resolve({ success: false, message: `Error: ${error.message}` });
            }
        });
    }
    
    async function testSafeClick() {
        return new Promise(async (resolve) => {
            try {
                // Create a test button
                const testButton = document.createElement('button');
                testButton.id = 'dom-test-button';
                testButton.textContent = 'Test Button';
                testButton.style.position = 'fixed';
                testButton.style.top = '-100px'; // Hidden but technically visible
                testButton.style.left = '0px';
                document.body.appendChild(testButton);
                
                let clicked = false;
                testButton.addEventListener('click', () => { clicked = true; });
                
                // Test safe click
                const clickResult = await window.domHelpers.safeClick(testButton);
                
                // Cleanup
                testButton.remove();
                
                if (clickResult === true && clicked === true) {
                    resolve({ success: true, message: 'safeClick working correctly' });
                } else {
                    resolve({ 
                        success: false, 
                        message: `Click test failed: result=${clickResult}, clicked=${clicked}` 
                    });
                }
            } catch (error) {
                resolve({ success: false, message: `Error: ${error.message}` });
            }
        });
    }
    
    async function testSafeSetValue() {
        return new Promise(async (resolve) => {
            try {
                // Create a test input
                const testInput = document.createElement('input');
                testInput.id = 'dom-test-input';
                testInput.type = 'text';
                testInput.style.position = 'fixed';
                testInput.style.top = '-100px'; // Hidden but technically accessible
                testInput.style.left = '0px';
                document.body.appendChild(testInput);
                
                const testValue = 'test-value-12345';
                
                // Test safe set value
                const setResult = await window.domHelpers.safeSetValue(testInput, testValue);
                
                // Verify value was set
                const actualValue = testInput.value;
                
                // Cleanup
                testInput.remove();
                
                if (setResult === true && actualValue === testValue) {
                    resolve({ success: true, message: 'safeSetValue working correctly' });
                } else {
                    resolve({ 
                        success: false, 
                        message: `Set value test failed: result=${setResult}, value='${actualValue}' (expected '${testValue}')` 
                    });
                }
            } catch (error) {
                resolve({ success: false, message: `Error: ${error.message}` });
            }
        });
    }
    
    // ============================================================================
    // ERROR RECOVERY FRAMEWORK TESTS
    // ============================================================================
    
    async function testErrorRecoveryFrameworkLoading() {
        return new Promise(async (resolve) => {
            try {
                // Test if ErrorRecoveryFramework is available
                if (!window.ErrorRecoveryFramework) {
                    // Try to load it
                    const script = document.createElement('script');
                    script.src = '/scripts/tampermonkey/errorRecoveryFramework.js';
                    document.head.appendChild(script);
                    
                    await new Promise((scriptResolve, scriptReject) => {
                        script.onload = scriptResolve;
                        script.onerror = scriptReject;
                        setTimeout(() => scriptReject(new Error('Script load timeout')), 5000);
                    });
                }
                
                if (window.ErrorRecoveryFramework) {
                    // Test instantiation
                    const recovery = new window.ErrorRecoveryFramework({
                        scriptName: 'test',
                        maxRetries: 2
                    });
                    
                    if (recovery && typeof recovery.executeWithRecovery === 'function') {
                        resolve({ 
                            success: true, 
                            message: 'Error Recovery Framework loaded and instantiated successfully' 
                        });
                    } else {
                        resolve({ 
                            success: false, 
                            message: 'Error Recovery Framework instantiation failed' 
                        });
                    }
                } else {
                    resolve({ 
                        success: false, 
                        message: 'Error Recovery Framework not available after load attempt' 
                    });
                }
            } catch (error) {
                resolve({ 
                    success: false, 
                    message: `Error loading Error Recovery Framework: ${error.message}` 
                });
            }
        });
    }
    
    async function testErrorRecoveryExecution() {
        return new Promise(async (resolve) => {
            try {
                const recovery = new window.ErrorRecoveryFramework({
                    scriptName: 'test-recovery',
                    maxRetries: 2,
                    baseDelay: 100
                });
                
                // Test successful operation
                let attempt = 0;
                const successfulOperation = async () => {
                    attempt++;
                    return `success-${attempt}`;
                };
                
                const result = await recovery.executeWithRecovery(
                    successfulOperation, 
                    'Test Successful Operation'
                );
                
                if (result === 'success-1' && attempt === 1) {
                    resolve({ 
                        success: true, 
                        message: 'Error recovery execution working correctly for successful operations' 
                    });
                } else {
                    resolve({ 
                        success: false, 
                        message: `Successful operation test failed: result='${result}', attempts=${attempt}` 
                    });
                }
            } catch (error) {
                resolve({ 
                    success: false, 
                    message: `Error testing recovery execution: ${error.message}` 
                });
            }
        });
    }
    
    async function testErrorRecoveryRetry() {
        return new Promise(async (resolve) => {
            try {
                const recovery = new window.ErrorRecoveryFramework({
                    scriptName: 'test-retry',
                    maxRetries: 3,
                    baseDelay: 50
                });
                
                // Test operation that fails twice then succeeds
                let attempt = 0;
                const retryOperation = async () => {
                    attempt++;
                    if (attempt < 3) {
                        throw new Error(`Attempt ${attempt} failed`);
                    }
                    return `success-after-${attempt}-attempts`;
                };
                
                const startTime = Date.now();
                const result = await recovery.executeWithRecovery(
                    retryOperation, 
                    'Test Retry Operation'
                );
                const duration = Date.now() - startTime;
                
                if (result === 'success-after-3-attempts' && attempt === 3 && duration >= 100) {
                    resolve({ 
                        success: true, 
                        message: `Error recovery retry working correctly (3 attempts, ${duration}ms)` 
                    });
                } else {
                    resolve({ 
                        success: false, 
                        message: `Retry test failed: result='${result}', attempts=${attempt}, duration=${duration}ms` 
                    });
                }
            } catch (error) {
                resolve({ 
                    success: false, 
                    message: `Error testing recovery retry: ${error.message}` 
                });
            }
        });
    }
    
    // ============================================================================
    // INTEGRATION TESTS
    // ============================================================================
    
    async function testTradovateUIElementsAccess() {
        return new Promise((resolve) => {
            try {
                // Check for common Tradovate UI elements
                const commonSelectors = [
                    'body',
                    '.app', '.main-content', '.header', '.navbar',
                    '.pane', '.module', '.toolbar'
                ];
                
                const foundElements = commonSelectors.filter(selector => 
                    window.domHelpers.validateElementExists(selector)
                );
                
                if (foundElements.length >= 2) {
                    resolve({ 
                        success: true, 
                        message: `Found ${foundElements.length}/${commonSelectors.length} common UI elements: ${foundElements.join(', ')}` 
                    });
                } else {
                    resolve({ 
                        success: false, 
                        message: `Only found ${foundElements.length}/${commonSelectors.length} UI elements: ${foundElements.join(', ')}` 
                    });
                }
            } catch (error) {
                resolve({ 
                    success: false, 
                    message: `Error testing UI elements: ${error.message}` 
                });
            }
        });
    }
    
    async function testPerformanceCompliance() {
        return new Promise(async (resolve) => {
            try {
                const iterations = 10;
                const times = [];
                
                // Test performance of DOM validation operations
                for (let i = 0; i < iterations; i++) {
                    const start = performance.now();
                    
                    // Simulate typical validation operations
                    window.domHelpers.validateElementExists('body');
                    window.domHelpers.validateElementVisible(document.body);
                    await window.domHelpers.waitForElement('body', 100);
                    
                    const end = performance.now();
                    times.push(end - start);
                }
                
                const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
                const maxTime = Math.max(...times);
                
                // Check if average time is under 10ms (requirement)
                if (avgTime < 10 && maxTime < 20) {
                    resolve({ 
                        success: true, 
                        message: `Performance compliant: avg=${avgTime.toFixed(2)}ms, max=${maxTime.toFixed(2)}ms` 
                    });
                } else {
                    resolve({ 
                        success: false, 
                        message: `Performance non-compliant: avg=${avgTime.toFixed(2)}ms, max=${maxTime.toFixed(2)}ms` 
                    });
                }
            } catch (error) {
                resolve({ 
                    success: false, 
                    message: `Error testing performance: ${error.message}` 
                });
            }
        });
    }
    
    // ============================================================================
    // RUN ALL TESTS
    // ============================================================================
    
    async function runAllTests() {
        const testSuite = new DOMValidationTestSuite();
        
        console.log('🧪 Starting DOM Validation Test Suite...\n');
        
        // Core DOM Helpers Tests
        await testSuite.runTest('DOM Helpers Loading', testDOMHelpersLoading);
        await testSuite.runTest('validateElementExists', testValidateElementExists);
        await testSuite.runTest('validateElementVisible', testValidateElementVisible);
        await testSuite.runTest('waitForElement', testWaitForElement);
        await testSuite.runTest('safeClick', testSafeClick);
        await testSuite.runTest('safeSetValue', testSafeSetValue);
        
        // Error Recovery Framework Tests
        await testSuite.runTest('Error Recovery Framework Loading', testErrorRecoveryFrameworkLoading);
        await testSuite.runTest('Error Recovery Execution', testErrorRecoveryExecution);
        await testSuite.runTest('Error Recovery Retry Logic', testErrorRecoveryRetry);
        
        // Integration Tests
        await testSuite.runTest('Tradovate UI Elements Access', testTradovateUIElementsAccess);
        await testSuite.runTest('Performance Compliance', testPerformanceCompliance);
        
        // Generate final report
        const report = testSuite.generateReport();
        
        // Store results for external access
        window.domValidationTestResults = report;
        
        return report;
    }
    
    // Auto-run tests after a short delay to ensure page is loaded
    setTimeout(runAllTests, 2000);
    
    // Make test suite available globally for manual execution
    window.runDOMValidationTests = runAllTests;
    
})();
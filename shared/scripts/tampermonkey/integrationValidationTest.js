// ============================================================================
// INTEGRATION VALIDATION TEST
// ============================================================================
// 
// Tests the integration between DOM helpers and Error Recovery Framework
// Validates real-world scenarios and cross-component functionality
//
// ============================================================================

class IntegrationValidationTest {
    constructor() {
        this.testResults = [];
        this.totalTests = 0;
        this.passedTests = 0;
        this.startTime = Date.now();
    }
    
    async runIntegrationTest(testName, testFunction, timeout = 15000) {
        console.log(`🔗 Integration Test: ${testName}`);
        this.totalTests++;
        
        const testStart = Date.now();
        
        try {
            const timeoutPromise = new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Integration test timeout')), timeout)
            );
            
            const result = await Promise.race([testFunction(), timeoutPromise]);
            const duration = Date.now() - testStart;
            
            if (result.success) {
                this.passedTests++;
                console.log(`✅ INTEGRATION PASS: ${testName} (${duration}ms)`);
                this.testResults.push({
                    test: testName,
                    status: 'PASS',
                    duration,
                    message: result.message,
                    details: result.details || {}
                });
            } else {
                console.error(`❌ INTEGRATION FAIL: ${testName} (${duration}ms) - ${result.message}`);
                this.testResults.push({
                    test: testName,
                    status: 'FAIL',
                    duration,
                    message: result.message,
                    details: result.details || {},
                    error: result.error
                });
            }
        } catch (error) {
            const duration = Date.now() - testStart;
            console.error(`❌ INTEGRATION ERROR: ${testName} (${duration}ms) - ${error.message}`);
            this.testResults.push({
                test: testName,
                status: 'ERROR',
                duration,
                message: error.message,
                error: error.stack
            });
        }
    }
    
    // ========================================================================
    // INTEGRATION TEST SCENARIOS
    // ========================================================================
    
    async testDOMHelpersWithErrorRecovery() {
        return new Promise(async (resolve) => {
            try {
                if (!window.domHelpers || !window.ErrorRecoveryFramework) {
                    resolve({
                        success: false,
                        message: 'Required frameworks not loaded'
                    });
                    return;
                }
                
                const recovery = new window.ErrorRecoveryFramework({
                    scriptName: 'integration-test',
                    maxRetries: 3,
                    baseDelay: 100
                });
                
                // Test operation that uses DOM helpers within error recovery
                let attempts = 0;
                const testOperation = async () => {
                    attempts++;
                    
                    // This should always succeed since body exists
                    const bodyExists = window.domHelpers.validateElementExists('body');
                    if (!bodyExists) {
                        throw new Error('Body element validation failed');
                    }
                    
                    return `DOM validation successful on attempt ${attempts}`;
                };
                
                const result = await recovery.executeWithRecovery(
                    testOperation,
                    'DOM Helpers Integration Test'
                );
                
                if (result && attempts === 1) {
                    resolve({
                        success: true,
                        message: 'DOM helpers work correctly within error recovery framework',
                        details: { result, attempts }
                    });
                } else {
                    resolve({
                        success: false,
                        message: `Integration failed: result=${result}, attempts=${attempts}`
                    });
                }
            } catch (error) {
                resolve({
                    success: false,
                    message: `Integration error: ${error.message}`,
                    error: error.stack
                });
            }
        });
    }
    
    async testErrorRecoveryWithDOMFailures() {
        return new Promise(async (resolve) => {
            try {
                const recovery = new window.ErrorRecoveryFramework({
                    scriptName: 'dom-failure-test',
                    maxRetries: 3,
                    baseDelay: 50
                });
                
                // Test operation that fails on DOM operations first few times
                let attempts = 0;
                const failingDOMOperation = async () => {
                    attempts++;
                    
                    if (attempts < 3) {
                        // Simulate DOM element not found
                        const fakeExists = window.domHelpers.validateElementExists('.fake-element-12345');
                        if (!fakeExists) {
                            throw new Error('ElementNotFound: Required element not available');
                        }
                    }
                    
                    // On third attempt, use real element
                    const realExists = window.domHelpers.validateElementExists('body');
                    if (realExists) {
                        return `DOM operation succeeded after ${attempts} attempts`;
                    }
                    
                    throw new Error('Unexpected DOM validation failure');
                };
                
                const startTime = Date.now();
                const result = await recovery.executeWithRecovery(
                    failingDOMOperation,
                    'DOM Failure Recovery Test'
                );
                const duration = Date.now() - startTime;
                
                if (result && attempts === 3 && duration >= 100) {
                    resolve({
                        success: true,
                        message: `Error recovery handled DOM failures correctly (${attempts} attempts, ${duration}ms)`,
                        details: { result, attempts, duration }
                    });
                } else {
                    resolve({
                        success: false,
                        message: `Recovery test failed: result=${result}, attempts=${attempts}, duration=${duration}ms`
                    });
                }
            } catch (error) {
                resolve({
                    success: false,
                    message: `DOM failure recovery error: ${error.message}`,
                    error: error.stack
                });
            }
        });
    }
    
    async testFormOperationsWithRecovery() {
        return new Promise(async (resolve) => {
            try {
                const recovery = new window.ErrorRecoveryFramework({
                    scriptName: 'form-operations-test',
                    maxRetries: 2,
                    baseDelay: 100
                });
                
                // Create test form elements
                const testForm = document.createElement('form');
                testForm.id = 'integration-test-form';
                testForm.style.position = 'fixed';
                testForm.style.top = '-200px';
                testForm.style.left = '0px';
                
                const testInput = document.createElement('input');
                testInput.id = 'integration-test-input';
                testInput.type = 'text';
                testInput.required = true;
                
                const testButton = document.createElement('button');
                testButton.id = 'integration-test-button';
                testButton.type = 'submit';
                testButton.textContent = 'Test Submit';
                
                testForm.appendChild(testInput);
                testForm.appendChild(testButton);
                document.body.appendChild(testForm);
                
                // Test form operations with recovery
                let operationAttempts = 0;
                const formOperation = async () => {
                    operationAttempts++;
                    
                    // Validate form exists
                    if (!window.domHelpers.validateElementExists('#integration-test-form')) {
                        throw new Error('Form validation failed');
                    }
                    
                    // Set form value
                    const setValue = await window.domHelpers.safeSetValue(testInput, `test-value-${operationAttempts}`);
                    if (!setValue) {
                        throw new Error('Form value setting failed');
                    }
                    
                    // Verify value was set
                    if (testInput.value !== `test-value-${operationAttempts}`) {
                        throw new Error('Form value verification failed');
                    }
                    
                    return `Form operations successful on attempt ${operationAttempts}`;
                };
                
                const result = await recovery.executeWithRecovery(
                    formOperation,
                    'Form Operations Test'
                );
                
                // Cleanup
                testForm.remove();
                
                if (result && operationAttempts === 1) {
                    resolve({
                        success: true,
                        message: 'Form operations with recovery work correctly',
                        details: { result, operationAttempts }
                    });
                } else {
                    resolve({
                        success: false,
                        message: `Form operations failed: result=${result}, attempts=${operationAttempts}`
                    });
                }
            } catch (error) {
                // Cleanup on error
                const testForm = document.getElementById('integration-test-form');
                if (testForm) testForm.remove();
                
                resolve({
                    success: false,
                    message: `Form operations error: ${error.message}`,
                    error: error.stack
                });
            }
        });
    }
    
    async testCircuitBreakerIntegration() {
        return new Promise(async (resolve) => {
            try {
                const recovery = new window.ErrorRecoveryFramework({
                    scriptName: 'circuit-breaker-test',
                    maxRetries: 2,
                    circuitBreakerThreshold: 3,
                    baseDelay: 50
                });
                
                // Operation that always fails to test circuit breaker
                const alwaysFailingOperation = async () => {
                    const fakeExists = window.domHelpers.validateElementExists('.absolutely-fake-element');
                    if (!fakeExists) {
                        throw new Error('Simulated operation failure');
                    }
                    return 'This should never happen';
                };
                
                // Run failing operation multiple times to trigger circuit breaker
                const results = [];
                
                for (let i = 0; i < 4; i++) {
                    try {
                        await recovery.executeWithRecovery(
                            alwaysFailingOperation,
                            `Circuit Test Operation ${i + 1}`
                        );
                        results.push('SUCCESS');
                    } catch (error) {
                        results.push(error.message.includes('Circuit breaker OPEN') ? 'CIRCUIT_OPEN' : 'FAILED');
                    }
                }
                
                // Check if circuit breaker opened
                const circuitOpenCount = results.filter(r => r === 'CIRCUIT_OPEN').length;
                const failedCount = results.filter(r => r === 'FAILED').length;
                
                if (circuitOpenCount > 0 && failedCount >= 2) {
                    resolve({
                        success: true,
                        message: `Circuit breaker integration working: ${failedCount} failures, then ${circuitOpenCount} circuit opens`,
                        details: { results }
                    });
                } else {
                    resolve({
                        success: false,
                        message: `Circuit breaker not working correctly: ${results.join(', ')}`,
                        details: { results }
                    });
                }
            } catch (error) {
                resolve({
                    success: false,
                    message: `Circuit breaker test error: ${error.message}`,
                    error: error.stack
                });
            }
        });
    }
    
    async testPerformanceUnderLoad() {
        return new Promise(async (resolve) => {
            try {
                const recovery = new window.ErrorRecoveryFramework({
                    scriptName: 'performance-test',
                    maxRetries: 1,
                    baseDelay: 10
                });
                
                const iterations = 50;
                const times = [];
                const results = [];
                
                // Run multiple DOM operations with recovery to test performance
                for (let i = 0; i < iterations; i++) {
                    const start = performance.now();
                    
                    const operation = async () => {
                        // Rapid DOM validation operations
                        window.domHelpers.validateElementExists('body');
                        window.domHelpers.validateElementVisible(document.body);
                        await window.domHelpers.waitForElement('body', 100);
                        return `operation-${i}`;
                    };
                    
                    try {
                        const result = await recovery.executeWithRecovery(
                            operation,
                            `Performance Test ${i}`
                        );
                        const end = performance.now();
                        times.push(end - start);
                        results.push('SUCCESS');
                    } catch (error) {
                        const end = performance.now();
                        times.push(end - start);
                        results.push('FAILED');
                    }
                }
                
                const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
                const maxTime = Math.max(...times);
                const successCount = results.filter(r => r === 'SUCCESS').length;
                const successRate = (successCount / iterations * 100).toFixed(1);
                
                // Check performance requirements
                if (avgTime < 15 && maxTime < 50 && successRate >= 95) {
                    resolve({
                        success: true,
                        message: `Performance under load acceptable: avg=${avgTime.toFixed(2)}ms, max=${maxTime.toFixed(2)}ms, success=${successRate}%`,
                        details: { avgTime, maxTime, successRate, iterations }
                    });
                } else {
                    resolve({
                        success: false,
                        message: `Performance under load inadequate: avg=${avgTime.toFixed(2)}ms, max=${maxTime.toFixed(2)}ms, success=${successRate}%`,
                        details: { avgTime, maxTime, successRate, iterations }
                    });
                }
            } catch (error) {
                resolve({
                    success: false,
                    message: `Performance test error: ${error.message}`,
                    error: error.stack
                });
            }
        });
    }
    
    async testRealWorldScenario() {
        return new Promise(async (resolve) => {
            try {
                const recovery = new window.ErrorRecoveryFramework({
                    scriptName: 'real-world-test',
                    maxRetries: 3,
                    baseDelay: 200
                });
                
                // Simulate a real trading operation scenario
                const tradingOperation = async () => {
                    // Step 1: Validate UI is ready
                    if (!window.domHelpers.validateElementExists('body')) {
                        throw new Error('UI not ready');
                    }
                    
                    // Step 2: Create mock trading elements
                    const mockOrderForm = document.createElement('div');
                    mockOrderForm.id = 'mock-order-form';
                    mockOrderForm.style.position = 'fixed';
                    mockOrderForm.style.top = '-300px';
                    
                    const symbolInput = document.createElement('input');
                    symbolInput.id = 'mock-symbol-input';
                    symbolInput.type = 'text';
                    
                    const quantityInput = document.createElement('input');
                    quantityInput.id = 'mock-quantity-input';
                    quantityInput.type = 'number';
                    
                    const submitButton = document.createElement('button');
                    submitButton.id = 'mock-submit-button';
                    submitButton.textContent = 'Submit Order';
                    
                    mockOrderForm.appendChild(symbolInput);
                    mockOrderForm.appendChild(quantityInput);
                    mockOrderForm.appendChild(submitButton);
                    document.body.appendChild(mockOrderForm);
                    
                    // Step 3: Fill form with validation
                    const symbolSet = await window.domHelpers.safeSetValue(symbolInput, 'NQ');
                    if (!symbolSet) throw new Error('Symbol setting failed');
                    
                    const quantitySet = await window.domHelpers.safeSetValue(quantityInput, '5');
                    if (!quantitySet) throw new Error('Quantity setting failed');
                    
                    // Step 4: Validate form before submission
                    if (symbolInput.value !== 'NQ' || quantityInput.value !== '5') {
                        throw new Error('Form validation failed');
                    }
                    
                    // Step 5: Click submit button
                    const clicked = await window.domHelpers.safeClick(submitButton);
                    if (!clicked) throw new Error('Submit click failed');
                    
                    // Step 6: Cleanup
                    mockOrderForm.remove();
                    
                    return 'Trading operation completed successfully';
                };
                
                const result = await recovery.executeWithRecovery(
                    tradingOperation,
                    'Real World Trading Scenario'
                );
                
                if (result && result.includes('successfully')) {
                    resolve({
                        success: true,
                        message: 'Real-world scenario completed successfully',
                        details: { result }
                    });
                } else {
                    resolve({
                        success: false,
                        message: `Real-world scenario failed: ${result}`,
                        details: { result }
                    });
                }
            } catch (error) {
                // Cleanup on error
                const mockForm = document.getElementById('mock-order-form');
                if (mockForm) mockForm.remove();
                
                resolve({
                    success: false,
                    message: `Real-world scenario error: ${error.message}`,
                    error: error.stack
                });
            }
        });
    }
    
    // ========================================================================
    // REPORT GENERATION
    // ========================================================================
    
    generateIntegrationReport() {
        const totalDuration = Date.now() - this.startTime;
        const successRate = this.totalTests > 0 
            ? (this.passedTests / this.totalTests * 100).toFixed(2)
            : 0;
        
        console.log('\n' + '='.repeat(80));
        console.log('🔗 INTEGRATION VALIDATION TEST REPORT');
        console.log('='.repeat(80));
        console.log(`📊 Integration Results: ${this.passedTests}/${this.totalTests} tests passed (${successRate}%)`);
        console.log(`⏱️ Total Duration: ${totalDuration}ms`);
        console.log(`🔗 Integration Status: ${this.passedTests === this.totalTests ? 'FULLY INTEGRATED' : 'NEEDS ATTENTION'}`);
        
        if (this.passedTests < this.totalTests) {
            console.log('\n❌ FAILED INTEGRATION TESTS:');
            this.testResults
                .filter(test => test.status !== 'PASS')
                .forEach(test => {
                    console.log(`  • ${test.test}: ${test.message}`);
                });
        }
        
        console.log('\n📋 INTEGRATION TEST DETAILS:');
        this.testResults.forEach(test => {
            const icon = test.status === 'PASS' ? '✅' : '❌';
            console.log(`  ${icon} ${test.test} (${test.duration}ms): ${test.message}`);
        });
        
        // Integration quality assessment
        console.log('\n🏆 INTEGRATION QUALITY METRICS:');
        const qualityMetrics = this.calculateQualityMetrics();
        for (const [metric, score] of Object.entries(qualityMetrics)) {
            const status = score >= 80 ? '✅' : score >= 60 ? '⚠️' : '❌';
            console.log(`  ${status} ${metric}: ${score}%`);
        }
        
        return {
            success: this.passedTests === this.totalTests,
            successRate,
            totalDuration,
            totalTests: this.totalTests,
            passedTests: this.passedTests,
            testResults: this.testResults,
            qualityMetrics
        };
    }
    
    calculateQualityMetrics() {
        const passedTests = this.testResults.filter(t => t.status === 'PASS');
        const avgDuration = passedTests.length > 0 
            ? passedTests.reduce((sum, t) => sum + t.duration, 0) / passedTests.length
            : 0;
        
        return {
            'Test Success Rate': parseFloat(((this.passedTests / this.totalTests) * 100).toFixed(1)),
            'Performance Score': avgDuration < 100 ? 100 : Math.max(0, 100 - (avgDuration - 100) / 10),
            'Integration Reliability': this.passedTests === this.totalTests ? 100 : 
                                      this.passedTests / this.totalTests * 80,
            'Error Handling Quality': passedTests.some(t => t.test.includes('Error') || t.test.includes('Failure')) ? 100 : 70
        };
    }
}

// ============================================================================
// EXECUTION
// ============================================================================

async function runIntegrationValidation() {
    console.log('🔗 Starting Integration Validation Tests...\n');
    
    const integrationTest = new IntegrationValidationTest();
    
    // Run all integration tests
    await integrationTest.runIntegrationTest(
        'DOM Helpers with Error Recovery',
        () => integrationTest.testDOMHelpersWithErrorRecovery()
    );
    
    await integrationTest.runIntegrationTest(
        'Error Recovery with DOM Failures',
        () => integrationTest.testErrorRecoveryWithDOMFailures()
    );
    
    await integrationTest.runIntegrationTest(
        'Form Operations with Recovery',
        () => integrationTest.testFormOperationsWithRecovery()
    );
    
    await integrationTest.runIntegrationTest(
        'Circuit Breaker Integration',
        () => integrationTest.testCircuitBreakerIntegration()
    );
    
    await integrationTest.runIntegrationTest(
        'Performance Under Load',
        () => integrationTest.testPerformanceUnderLoad()
    );
    
    await integrationTest.runIntegrationTest(
        'Real World Trading Scenario',
        () => integrationTest.testRealWorldScenario()
    );
    
    // Generate and return report
    const report = integrationTest.generateIntegrationReport();
    
    // Store results globally
    window.integrationValidationResults = report;
    
    return report;
}

// Make available globally
if (typeof window !== 'undefined') {
    window.runIntegrationValidation = runIntegrationValidation;
    window.IntegrationValidationTest = IntegrationValidationTest;
}

// Auto-run integration tests
setTimeout(runIntegrationValidation, 3000);
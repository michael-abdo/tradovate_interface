// ==Test Suite==
// @name         Order Validation Framework Test Suite
// @description  Comprehensive tests for order validation system
// @author       Trading System
// @version      1.0

(function() {
    'use strict';
    
    console.log('=== Order Validation Framework Test Suite ===');
    
    const TEST_RESULTS = {
        passed: 0,
        failed: 0,
        tests: []
    };
    
    // Test helper functions
    function assert(condition, testName, message) {
        if (condition) {
            TEST_RESULTS.passed++;
            TEST_RESULTS.tests.push({
                name: testName,
                status: 'PASSED',
                message: message || 'Test passed'
            });
            console.log(`✅ ${testName}: PASSED`);
        } else {
            TEST_RESULTS.failed++;
            TEST_RESULTS.tests.push({
                name: testName,
                status: 'FAILED',
                message: message || 'Test failed'
            });
            console.error(`❌ ${testName}: FAILED - ${message}`);
        }
    }
    
    function asyncAssert(promise, testName, validator) {
        return promise
            .then(result => {
                const isValid = validator(result);
                assert(isValid, testName, `Result: ${JSON.stringify(result)}`);
                return result;
            })
            .catch(error => {
                assert(false, testName, `Error: ${error.message}`);
                throw error;
            });
    }
    
    // Mock objects for testing
    const mockOrderData = {
        orderType: 'MARKET',
        quantity: 1,
        symbol: 'ES',
        account: 'SIM12345',
        price: 4500.25,
        side: 'BUY'
    };
    
    const mockBracketOrderData = {
        ...mockOrderData,
        orderType: 'BRACKET',
        stopLoss: 4490.25,
        takeProfit: 4510.25
    };
    
    // ============================================================================
    // TEST SUITE 1: Framework Initialization
    // ============================================================================
    
    async function testFrameworkInitialization() {
        console.log('\n--- Testing Framework Initialization ---');
        
        // Test 1.1: Framework exists
        assert(
            typeof window.OrderValidationFramework !== 'undefined',
            'Framework Class Exists',
            'OrderValidationFramework class should be defined'
        );
        
        // Test 1.2: Can create instance
        let validator = null;
        try {
            validator = new window.OrderValidationFramework({
                scriptName: 'TestSuite',
                debugMode: true,
                performanceMode: true
            });
            assert(validator !== null, 'Framework Instance Creation', 'Should create validator instance');
        } catch (error) {
            assert(false, 'Framework Instance Creation', `Error: ${error.message}`);
        }
        
        // Test 1.3: Required methods exist
        const requiredMethods = [
            'validatePreSubmission',
            'monitorOrderSubmission', 
            'validatePostSubmission',
            'recordOrderEvent',
            'getOrderStatus',
            'getPerformanceReport'
        ];
        
        requiredMethods.forEach(method => {
            assert(
                validator && typeof validator[method] === 'function',
                `Method Exists: ${method}`,
                `${method} should be a function`
            );
        });
        
        return validator;
    }
    
    // ============================================================================
    // TEST SUITE 2: Pre-Submission Validation
    // ============================================================================
    
    async function testPreSubmissionValidation(validator) {
        console.log('\n--- Testing Pre-Submission Validation ---');
        
        // Test 2.1: Valid order data
        await asyncAssert(
            validator.validatePreSubmission(mockOrderData),
            'Valid Order Pre-Submission',
            result => result.valid === true && result.errors.length === 0
        );
        
        // Test 2.2: Missing required fields
        const invalidOrder = { ...mockOrderData };
        delete invalidOrder.quantity;
        
        await asyncAssert(
            validator.validatePreSubmission(invalidOrder),
            'Missing Required Field Detection',
            result => result.valid === false && result.errors.some(e => e.includes('quantity'))
        );
        
        // Test 2.3: Invalid order type
        await asyncAssert(
            validator.validatePreSubmission({ ...mockOrderData, orderType: 'INVALID' }),
            'Invalid Order Type Detection',
            result => result.valid === false && result.errors.some(e => e.includes('orderType'))
        );
        
        // Test 2.4: Bracket order validation
        await asyncAssert(
            validator.validatePreSubmission(mockBracketOrderData),
            'Bracket Order Validation',
            result => result.valid === true && result.validationType === 'BRACKET'
        );
    }
    
    // ============================================================================
    // TEST SUITE 3: Order Event Recording
    // ============================================================================
    
    async function testOrderEventRecording(validator) {
        console.log('\n--- Testing Order Event Recording ---');
        
        const testOrderId = `TEST_${Date.now()}`;
        
        // Test 3.1: Record submission event
        validator.recordOrderEvent(testOrderId, 'SUBMISSION_ATTEMPT', {
            orderData: mockOrderData,
            timestamp: Date.now()
        });
        
        const orderStatus = validator.getOrderStatus(testOrderId);
        assert(
            orderStatus && orderStatus.events.length > 0,
            'Order Event Recording',
            'Should record order events'
        );
        
        // Test 3.2: Event type validation
        assert(
            orderStatus.events[0].type === 'SUBMISSION_ATTEMPT',
            'Event Type Recording',
            'Should record correct event type'
        );
        
        // Test 3.3: Multiple events
        validator.recordOrderEvent(testOrderId, 'SUBMISSION_CONFIRMED', {
            confirmationId: 'CONF123'
        });
        
        assert(
            orderStatus.events.length === 2,
            'Multiple Event Recording',
            'Should record multiple events for same order'
        );
        
        return testOrderId;
    }
    
    // ============================================================================
    // TEST SUITE 4: Performance Monitoring
    // ============================================================================
    
    async function testPerformanceMonitoring(validator) {
        console.log('\n--- Testing Performance Monitoring ---');
        
        // Test 4.1: Performance metrics exist
        const perfReport = validator.getPerformanceReport();
        assert(
            perfReport !== null && typeof perfReport === 'object',
            'Performance Report Generation',
            'Should generate performance report'
        );
        
        // Test 4.2: Metrics tracking
        assert(
            perfReport.validationCalls > 0,
            'Validation Call Tracking',
            `Should track validation calls: ${perfReport.validationCalls}`
        );
        
        // Test 4.3: Average time calculation
        assert(
            perfReport.averageValidationTime >= 0,
            'Average Time Calculation',
            `Average time: ${perfReport.averageValidationTime}ms`
        );
        
        // Test 4.4: Compliance rate
        assert(
            perfReport.complianceRate !== undefined,
            'Compliance Rate Calculation',
            `Compliance rate: ${perfReport.complianceRate}`
        );
        
        // Test 4.5: Performance within threshold
        assert(
            perfReport.averageValidationTime < 10,
            'Performance Threshold Compliance',
            `Average ${perfReport.averageValidationTime}ms should be < 10ms`
        );
        
        // Test 4.6: Adaptive performance levels
        assert(
            perfReport.performanceMode && perfReport.adaptiveLevel,
            'Adaptive Performance Tracking',
            `Mode: ${perfReport.performanceMode}, Level: ${perfReport.adaptiveLevel}`
        );
    }
    
    // ============================================================================
    // TEST SUITE 5: Error Classification
    // ============================================================================
    
    async function testErrorClassification(validator) {
        console.log('\n--- Testing Error Classification ---');
        
        // Test 5.1: Error patterns loaded
        assert(
            window.ORDER_ERROR_PATTERNS !== undefined,
            'Error Patterns Loaded',
            'ORDER_ERROR_PATTERNS should be available'
        );
        
        // Test 5.2: Classification function
        if (validator.classifyError) {
            const testError = 'Insufficient funds to place order';
            const classification = validator.classifyError(testError);
            
            assert(
                classification && classification.category,
                'Error Classification',
                `Classified as: ${classification.category}`
            );
            
            assert(
                classification.severity === 'HIGH',
                'Error Severity Detection',
                'Insufficient funds should be HIGH severity'
            );
        }
    }
    
    // ============================================================================
    // TEST SUITE 6: Order Reconciliation
    // ============================================================================
    
    async function testOrderReconciliation() {
        console.log('\n--- Testing Order Reconciliation ---');
        
        // Test 6.1: Reconciliation class exists
        assert(
            typeof window.OrderReconciliationReporting !== 'undefined',
            'Reconciliation Class Exists',
            'OrderReconciliationReporting should be defined'
        );
        
        if (window.OrderReconciliationReporting) {
            const reconciler = new window.OrderReconciliationReporting();
            
            // Test 6.2: Report generation
            const report = reconciler.generateComprehensiveReport();
            assert(
                report && report.summary,
                'Reconciliation Report Generation',
                'Should generate comprehensive report'
            );
            
            // Test 6.3: Report sections
            const requiredSections = ['summary', 'performance', 'reconciliation', 'errorAnalysis'];
            requiredSections.forEach(section => {
                assert(
                    report[section] !== undefined,
                    `Report Section: ${section}`,
                    `Report should include ${section} section`
                );
            });
        }
    }
    
    // ============================================================================
    // TEST SUITE 7: Integration Tests
    // ============================================================================
    
    async function testIntegration(validator) {
        console.log('\n--- Testing Integration Flow ---');
        
        const integrationOrderId = `INT_${Date.now()}`;
        const integrationOrder = { ...mockOrderData, orderId: integrationOrderId };
        
        try {
            // Test 7.1: Full validation flow
            const preValidation = await validator.validatePreSubmission(integrationOrder);
            assert(
                preValidation.valid,
                'Integration: Pre-Validation',
                'Pre-submission validation should pass'
            );
            
            // Test 7.2: Monitoring activation
            const monitoringPromise = validator.monitorOrderSubmission(integrationOrderId);
            assert(
                monitoringPromise instanceof Promise,
                'Integration: Monitoring Setup',
                'Should return monitoring promise'
            );
            
            // Test 7.3: Event recording during flow
            validator.recordOrderEvent(integrationOrderId, 'SUBMISSION_ATTEMPT', {
                validationId: preValidation.validationId
            });
            
            const status = validator.getOrderStatus(integrationOrderId);
            assert(
                status && status.events.length > 0,
                'Integration: Event Flow',
                'Should track events through flow'
            );
            
        } catch (error) {
            assert(false, 'Integration Test Flow', `Error: ${error.message}`);
        }
    }
    
    // ============================================================================
    // TEST SUITE 8: DOM Helpers Integration
    // ============================================================================
    
    async function testDOMHelpers() {
        console.log('\n--- Testing DOM Helpers Integration ---');
        
        // Test 8.1: DOM Helpers available
        assert(
            window.domHelpers !== undefined,
            'DOM Helpers Loaded',
            'domHelpers should be available'
        );
        
        if (window.domHelpers) {
            // Test 8.2: Required helper functions
            const requiredHelpers = [
                'waitForElement',
                'validateElementExists',
                'validateElementVisible',
                'validateFormFieldValue'
            ];
            
            requiredHelpers.forEach(helper => {
                assert(
                    typeof window.domHelpers[helper] === 'function',
                    `DOM Helper: ${helper}`,
                    `${helper} should be a function`
                );
            });
        }
    }
    
    // ============================================================================
    // RUN ALL TESTS
    // ============================================================================
    
    async function runAllTests() {
        console.log('🧪 Starting Order Validation Framework Test Suite...\n');
        const startTime = performance.now();
        
        try {
            // Initialize framework
            const validator = await testFrameworkInitialization();
            
            if (validator) {
                // Run test suites
                await testPreSubmissionValidation(validator);
                await testOrderEventRecording(validator);
                await testPerformanceMonitoring(validator);
                await testErrorClassification(validator);
                await testOrderReconciliation();
                await testIntegration(validator);
                await testDOMHelpers();
            }
            
        } catch (error) {
            console.error('Test suite error:', error);
        }
        
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        // Generate test report
        console.log('\n=== TEST RESULTS ===');
        console.log(`Total Tests: ${TEST_RESULTS.passed + TEST_RESULTS.failed}`);
        console.log(`✅ Passed: ${TEST_RESULTS.passed}`);
        console.log(`❌ Failed: ${TEST_RESULTS.failed}`);
        console.log(`⏱️  Duration: ${duration.toFixed(2)}ms`);
        console.log(`📊 Success Rate: ${((TEST_RESULTS.passed / (TEST_RESULTS.passed + TEST_RESULTS.failed)) * 100).toFixed(1)}%`);
        
        // Store results for external access
        window.ORDER_VALIDATION_TEST_RESULTS = TEST_RESULTS;
        
        // Return summary
        return {
            success: TEST_RESULTS.failed === 0,
            passed: TEST_RESULTS.passed,
            failed: TEST_RESULTS.failed,
            duration: duration,
            details: TEST_RESULTS.tests
        };
    }
    
    // Make test runner available globally
    window.runOrderValidationTests = runAllTests;
    
    // Auto-run if in test mode
    if (window.location.search.includes('runTests=true')) {
        setTimeout(runAllTests, 2000); // Wait for page load
    }
    
})();
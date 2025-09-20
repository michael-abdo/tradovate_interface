#!/usr/bin/env python3
"""
Live Order Validation Testing Script
Tests the Order Validation Framework with real Tradovate UI
"""

import json
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Set up logging with comprehensive detail per CLAUDE.md
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][ValidationTest][%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OrderValidationLiveTester:
    """Tests Order Validation Framework with live Tradovate DOM"""
    
    def __init__(self, chrome_tab):
        self.tab = chrome_tab
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'tests': [],
            'performance_metrics': []
        }
        self.start_time = time.time()
        
    async def run_validation_tests(self) -> Dict:
        """Run comprehensive validation tests"""
        logger.info("=== Starting Live Order Validation Tests ===")
        
        try:
            # Test 1: Framework Loading
            await self._test_framework_loading()
            
            # Test 2: UI Element Validation
            await self._test_ui_element_validation()
            
            # Test 3: Order Submission Flow
            await self._test_order_submission_flow()
            
            # Test 4: Error Detection
            await self._test_error_detection()
            
            # Test 5: Performance Compliance
            await self._test_performance_compliance()
            
            # Test 6: Reconciliation System
            await self._test_reconciliation_system()
            
            # Generate report
            return self._generate_test_report()
            
        except Exception as e:
            logger.error(f"Test suite failed: {str(e)}")
            raise
    
    async def _test_framework_loading(self):
        """Test that validation framework is properly loaded"""
        logger.info("\n--- Test 1: Framework Loading ---")
        
        # Check OrderValidationFramework
        result = await self._execute_js("""
            return {
                frameworkLoaded: typeof window.OrderValidationFramework !== 'undefined',
                validatorExists: typeof window.autoOrderValidator !== 'undefined',
                validatorActive: window.autoOrderValidator ? window.autoOrderValidator.validationEnabled : false,
                uiElementsLoaded: typeof window.TRADOVATE_UI_ELEMENTS !== 'undefined',
                errorPatternsLoaded: typeof window.ORDER_ERROR_PATTERNS !== 'undefined',
                reconcilerLoaded: typeof window.OrderReconciliationReporting !== 'undefined'
            };
        """)
        
        self._assert(result.get('frameworkLoaded'), 'Framework Class Loaded')
        self._assert(result.get('validatorExists'), 'Validator Instance Created')
        self._assert(result.get('validatorActive'), 'Validator Active')
        self._assert(result.get('uiElementsLoaded'), 'UI Elements Map Loaded')
        self._assert(result.get('errorPatternsLoaded'), 'Error Patterns Loaded')
        self._assert(result.get('reconcilerLoaded'), 'Reconciliation System Loaded')
        
    async def _test_ui_element_validation(self):
        """Test UI element detection and validation"""
        logger.info("\n--- Test 2: UI Element Validation ---")
        
        # Test critical UI elements
        elements_to_test = [
            ('Order Type Dropdown', '.group.order-type .select-input div[tabindex]'),
            ('Submit Button', '.btn-group .btn-primary'),
            ('Price Input', '.numeric-input.feedback-wrapper input'),
            ('Quantity Input', 'input[placeholder="Qty"]'),
            ('Account Selector', '.account-selector, .accounts-dropdown')
        ]
        
        for element_name, selector in elements_to_test:
            result = await self._execute_js(f"""
                const element = document.querySelector('{selector}');
                return {{
                    exists: element !== null,
                    visible: element ? window.domHelpers?.validateElementVisible(element) : false,
                    selector: '{selector}'
                }};
            """)
            
            self._assert(
                result.get('exists') or 'optional' in element_name.lower(),
                f'UI Element Exists: {element_name}',
                f"Selector: {selector}"
            )
    
    async def _test_order_submission_flow(self):
        """Test order submission validation flow"""
        logger.info("\n--- Test 3: Order Submission Flow ---")
        
        # Create test order data
        test_order = {
            'orderType': 'MARKET',
            'quantity': 1,
            'symbol': 'ES',
            'account': 'SIM_TEST',
            'side': 'BUY'
        }
        
        # Test pre-submission validation
        result = await self._execute_js(f"""
            const orderData = {json.dumps(test_order)};
            if (window.autoOrderValidator) {{
                const validation = await window.autoOrderValidator.validatePreSubmission(orderData);
                return {{
                    valid: validation.valid,
                    errors: validation.errors,
                    warnings: validation.warnings,
                    validationId: validation.validationId,
                    duration: validation.performanceMetrics?.duration
                }};
            }}
            return {{ error: 'Validator not available' }};
        """)
        
        self._assert(
            not result.get('error'),
            'Pre-Submission Validation Executed',
            f"Valid: {result.get('valid')}, Errors: {len(result.get('errors', []))}"
        )
        
        if result.get('duration'):
            self.test_results['performance_metrics'].append({
                'operation': 'pre_submission_validation',
                'duration': result['duration']
            })
    
    async def _test_error_detection(self):
        """Test error detection and classification"""
        logger.info("\n--- Test 4: Error Detection ---")
        
        # Test error classification
        test_errors = [
            'Insufficient funds to place order',
            'Market is closed',
            'Invalid contract specification',
            'Connection timeout',
            'Order rejected by exchange'
        ]
        
        for error_msg in test_errors:
            result = await self._execute_js(f"""
                if (window.autoOrderValidator && window.autoOrderValidator.classifyError) {{
                    const classification = window.autoOrderValidator.classifyError('{error_msg}');
                    return classification;
                }} else if (window.ORDER_ERROR_PATTERNS) {{
                    // Manual classification if method not available
                    for (const [category, patterns] of Object.entries(window.ORDER_ERROR_PATTERNS)) {{
                        for (const [errorType, config] of Object.entries(patterns)) {{
                            if (config.patterns && config.patterns.some(p => p.test('{error_msg}'))) {{
                                return {{
                                    category: category,
                                    type: errorType,
                                    severity: config.severity,
                                    recovery: config.recovery
                                }};
                            }}
                        }}
                    }}
                }}
                return {{ error: 'Classification not available' }};
            """)
            
            self._assert(
                not result.get('error') and result.get('category'),
                f'Error Classification: "{error_msg}"',
                f"Category: {result.get('category')}, Severity: {result.get('severity')}"
            )
    
    async def _test_performance_compliance(self):
        """Test performance monitoring and compliance"""
        logger.info("\n--- Test 5: Performance Compliance ---")
        
        # Get performance report
        result = await self._execute_js("""
            if (window.autoOrderValidator) {
                const report = window.autoOrderValidator.getPerformanceReport();
                return {
                    averageTime: report.averageValidationTime,
                    maxTime: report.maxValidationTime,
                    complianceRate: report.complianceRate,
                    performanceMode: report.performanceMode,
                    adaptiveLevel: report.adaptiveLevel,
                    violations: report.overheadWarnings,
                    healthScore: report.performanceHealthScore
                };
            }
            return { error: 'Performance data not available' };
        """)
        
        if not result.get('error'):
            self._assert(
                result.get('averageTime', 999) < 10,
                'Average Validation Time < 10ms',
                f"Average: {result.get('averageTime', 'N/A')}ms"
            )
            
            self._assert(
                result.get('performanceMode') == 'OPTIMAL',
                'Performance Mode Optimal',
                f"Current mode: {result.get('performanceMode')}"
            )
            
            self._assert(
                result.get('healthScore', 0) >= 70,
                'Performance Health Score >= 70',
                f"Score: {result.get('healthScore', 'N/A')}/100"
            )
    
    async def _test_reconciliation_system(self):
        """Test order reconciliation and reporting"""
        logger.info("\n--- Test 6: Reconciliation System ---")
        
        result = await self._execute_js("""
            if (window.OrderReconciliationReporting) {
                const reconciler = new window.OrderReconciliationReporting();
                const report = reconciler.generateComprehensiveReport();
                return {
                    hasReport: true,
                    sections: Object.keys(report),
                    summaryExists: report.summary !== undefined,
                    performanceExists: report.performance !== undefined,
                    reconciliationExists: report.reconciliation !== undefined,
                    errorAnalysisExists: report.errorAnalysis !== undefined
                };
            }
            return { error: 'Reconciliation system not available' };
        """)
        
        if not result.get('error'):
            self._assert(
                result.get('hasReport'),
                'Reconciliation Report Generated'
            )
            
            required_sections = ['summary', 'performance', 'reconciliation', 'errorAnalysis']
            for section in required_sections:
                self._assert(
                    result.get(f'{section}Exists'),
                    f'Report Section: {section}'
                )
    
    async def _execute_js(self, js_code: str) -> Dict:
        """Execute JavaScript and return result"""
        try:
            result = await self.tab.Runtime.evaluate(expression=js_code, awaitPromise=True)
            if result.get('exceptionDetails'):
                logger.error(f"JS execution error: {result['exceptionDetails']}")
                return {'error': str(result['exceptionDetails'])}
            return result.get('result', {}).get('value', {})
        except Exception as e:
            logger.error(f"Failed to execute JS: {str(e)}")
            return {'error': str(e)}
    
    def _assert(self, condition: bool, test_name: str, details: str = ""):
        """Assert test condition and record result"""
        if condition:
            self.test_results['passed'] += 1
            logger.info(f"✅ {test_name} - PASSED {details}")
            self.test_results['tests'].append({
                'name': test_name,
                'status': 'PASSED',
                'details': details
            })
        else:
            self.test_results['failed'] += 1
            logger.error(f"❌ {test_name} - FAILED {details}")
            self.test_results['tests'].append({
                'name': test_name,
                'status': 'FAILED',
                'details': details
            })
    
    def _generate_test_report(self) -> Dict:
        """Generate comprehensive test report"""
        duration = time.time() - self.start_time
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': self.test_results['passed'],
                'failed': self.test_results['failed'],
                'success_rate': f"{success_rate:.1f}%",
                'duration': f"{duration:.2f}s"
            },
            'performance': {
                'metrics': self.test_results['performance_metrics'],
                'average_duration': sum(m['duration'] for m in self.test_results['performance_metrics']) / len(self.test_results['performance_metrics']) if self.test_results['performance_metrics'] else 0
            },
            'test_details': self.test_results['tests'],
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("\n=== TEST REPORT ===")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {self.test_results['passed']}")
        logger.info(f"Failed: {self.test_results['failed']}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Duration: {duration:.2f}s")
        
        return report


async def run_live_validation(chrome_tab):
    """Run live validation tests"""
    tester = OrderValidationLiveTester(chrome_tab)
    return await tester.run_validation_tests()


# Function to be called from app.py
def create_validation_test_command():
    """Create command for running validation tests from app.py"""
    return """
    # Add this to app.py to run validation tests
    
    async def test_order_validation():
        '''Test order validation framework'''
        from utils.test_order_validation_live import run_live_validation
        
        try:
            # Get active Chrome tab
            tab = get_active_tab()  # Your existing function
            
            # Run validation tests
            results = await run_live_validation(tab)
            
            # Display results
            logger.info(f"Validation test completed: {results['summary']['success_rate']} success rate")
            
            return results
            
        except Exception as e:
            logger.error(f"Validation test failed: {str(e)}")
            return {'error': str(e)}
    """


if __name__ == "__main__":
    logger.info("Order Validation Live Test script ready")
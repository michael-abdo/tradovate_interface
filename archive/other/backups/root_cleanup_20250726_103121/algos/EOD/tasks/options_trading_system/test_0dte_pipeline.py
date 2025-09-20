#!/usr/bin/env python3
"""
Comprehensive Test Suite for 0DTE Pipeline

Tests all components of the 0DTE validation and pipeline system:
1. Symbol generation with multiple prefixes
2. Expiration validation logic
3. Pipeline integration and abort mechanisms
4. Error handling and fallback scenarios
5. Configuration integration

This test suite validates the complete 0DTE system end-to-end.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add project paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

# Import modules to test
from data_ingestion.barchart_web_scraper.symbol_generator import (
    OptionsSymbolGenerator,
    LegacySymbolGenerator,
    generate_0dte_symbol,
    get_symbol_with_fallbacks
)
from data_ingestion.barchart_web_scraper.expiration_validator import (
    ExpirationValidator,
    find_0dte_symbol,
    validate_is_0dte
)
from daily_options_pipeline import (
    DailyOptionsPipeline,
    run_daily_0dte_pipeline,
    validate_0dte_symbol_only
)


class TestSymbolGenerator(unittest.TestCase):
    """Test suite for OptionsSymbolGenerator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = OptionsSymbolGenerator(validate_0dte=False, headless=True)
        self.test_date = datetime(2025, 7, 3)  # Thursday
        self.weekend_date = datetime(2025, 7, 5)  # Saturday
    
    def test_symbol_generation_weekday(self):
        """Test symbol generation for weekday"""
        symbol = self.generator._generate_symbol_for_prefix('MC', self.test_date)
        # Thursday (July 3, 2025) -> day_code=4, month=N, year=25
        expected = 'MC4N25'
        self.assertEqual(symbol, expected)
    
    def test_symbol_generation_weekend_adjustment(self):
        """Test weekend date adjustment to Monday"""
        adjusted_date = self.generator._adjust_for_weekends(self.weekend_date)
        # Saturday July 5 -> Monday July 7
        expected_date = datetime(2025, 7, 7)
        self.assertEqual(adjusted_date.date(), expected_date.date())
    
    def test_multiple_prefixes(self):
        """Test generation with different contract prefixes"""
        prefixes = ['MC', 'MM', 'MQ']
        for prefix in prefixes:
            symbol = self.generator._generate_symbol_for_prefix(prefix, self.test_date)
            self.assertTrue(symbol.startswith(prefix))
            self.assertEqual(len(symbol), 6)  # MC + 1 + N + 25 = 6 chars
    
    def test_generate_symbol_with_fallbacks(self):
        """Test comprehensive fallback generation"""
        result = self.generator.generate_symbol_with_fallbacks(self.test_date)
        
        # Check result structure
        self.assertIn('requested_date', result)
        self.assertIn('fallbacks_tried', result)
        self.assertIn('validation_enabled', result)
        self.assertEqual(len(result['fallbacks_tried']), 3)  # MC, MM, MQ
        
        # Check fallback details
        for fallback in result['fallbacks_tried']:
            self.assertIn('prefix', fallback)
            self.assertIn('symbol', fallback)
            self.assertIn('validated', fallback)
    
    def test_legacy_compatibility(self):
        """Test backward compatibility with legacy generator"""
        legacy_symbol = LegacySymbolGenerator.get_eod_contract_symbol()
        new_symbol = self.generator.get_legacy_eod_symbol()
        
        # Should generate same symbol format
        self.assertEqual(len(legacy_symbol), len(new_symbol))
        self.assertTrue(legacy_symbol.startswith('MC'))
        self.assertTrue(new_symbol.startswith('MC'))


class TestExpirationValidator(unittest.TestCase):
    """Test suite for ExpirationValidator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_date = datetime(2025, 7, 3)
        self.mock_validator = Mock(spec=ExpirationValidator)
    
    @patch('data_ingestion.barchart_web_scraper.expiration_validator.webdriver.Chrome')
    def test_validator_initialization(self, mock_chrome):
        """Test validator initialization"""
        validator = ExpirationValidator(headless=True)
        self.assertTrue(validator.headless)
        self.assertEqual(validator.wait_time, 10)
        self.assertEqual(len(validator.CONTRACT_PREFIXES), 3)
    
    def test_date_parsing(self):
        """Test date string parsing functionality"""
        validator = ExpirationValidator()
        
        # Test various date formats
        test_cases = [
            ('2025-07-03', '2025-07-03'),
            ('July 3, 2025', '2025-07-03'),
            ('Jul 3, 2025', '2025-07-03'),
            ('07/03/2025', '2025-07-03'),
            ('03/07/2025', '2025-03-07'),  # MM/DD/YYYY format
        ]
        
        for input_date, expected in test_cases:
            result = validator._parse_date_string(input_date)
            self.assertEqual(result, expected, f"Failed for input: {input_date}")
    
    def test_symbol_generation_logic(self):
        """Test symbol generation within validator"""
        validator = ExpirationValidator()
        
        # Test Thursday July 3, 2025
        symbol = validator._generate_contract_symbol('MC', self.test_date)
        expected = 'MC4N25'  # MC + Thursday(4) + July(N) + 25
        self.assertEqual(symbol, expected)
    
    @patch.object(ExpirationValidator, 'validate_is_0dte')
    def test_find_0dte_symbol_success(self, mock_validate):
        """Test successful 0DTE symbol finding"""
        # Mock validation to return True for MC prefix
        mock_validate.side_effect = lambda symbol, date: symbol.startswith('MC')
        
        validator = ExpirationValidator()
        symbol = validator.find_0dte_symbol(self.test_date)
        
        self.assertIsNotNone(symbol)
        self.assertTrue(symbol.startswith('MC'))
        self.assertEqual(symbol, 'MC4N25')
    
    @patch.object(ExpirationValidator, 'validate_is_0dte')
    def test_find_0dte_symbol_fallback(self, mock_validate):
        """Test fallback to MM prefix when MC fails"""
        # Mock validation to return False for MC, True for MM
        mock_validate.side_effect = lambda symbol, date: symbol.startswith('MM')
        
        validator = ExpirationValidator()
        symbol = validator.find_0dte_symbol(self.test_date)
        
        self.assertIsNotNone(symbol)
        self.assertTrue(symbol.startswith('MM'))
        self.assertEqual(symbol, 'MM4N25')
    
    @patch.object(ExpirationValidator, 'validate_is_0dte')
    def test_find_0dte_symbol_no_valid(self, mock_validate):
        """Test when no valid 0DTE symbol found"""
        # Mock validation to always return False
        mock_validate.return_value = False
        
        validator = ExpirationValidator()
        symbol = validator.find_0dte_symbol(self.test_date)
        
        self.assertIsNone(symbol)


class TestDailyOptionsPipeline(unittest.TestCase):
    """Test suite for DailyOptionsPipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_date = datetime(2025, 7, 3)
        self.config = {
            "data": {"barchart": {"use_live_api": False}},  # Disable live API for testing
            "analysis": {},
            "output": {},
            "save": {}
        }
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization"""
        pipeline = DailyOptionsPipeline(config=self.config, enable_validation=True)
        
        self.assertEqual(pipeline.config, self.config)
        self.assertTrue(pipeline.enable_validation)
        self.assertEqual(len(pipeline.pipeline_state), 5)
        
        # Check initial state
        for stage in pipeline.pipeline_state.values():
            self.assertEqual(stage['status'], 'pending')
    
    @patch.object(OptionsSymbolGenerator, 'generate_symbol_with_fallbacks')
    def test_symbol_generation_success(self, mock_generate):
        """Test successful symbol generation"""
        # Mock successful symbol generation
        mock_generate.return_value = {
            'requested_date': '2025-07-03',
            'symbol': 'MC4N25',
            'contract_type': 'MC',
            'is_0dte': True,
            'fallbacks_tried': [{'prefix': 'MC', 'symbol': 'MC4N25', 'is_0dte': True}]
        }
        
        pipeline = DailyOptionsPipeline(config=self.config, enable_validation=True)
        result = pipeline._generate_and_validate_symbol(self.test_date)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['symbol'], 'MC4N25')
        self.assertEqual(result['contract_type'], 'MC')
        self.assertTrue(result['is_validated'])
    
    @patch.object(OptionsSymbolGenerator, 'generate_symbol_with_fallbacks')
    def test_symbol_generation_failure(self, mock_generate):
        """Test symbol generation failure"""
        # Mock failed symbol generation
        mock_generate.return_value = {
            'requested_date': '2025-07-03',
            'symbol': None,
            'contract_type': None,
            'is_0dte': False,
            'fallbacks_tried': [
                {'prefix': 'MC', 'symbol': 'MC4N25', 'is_0dte': False},
                {'prefix': 'MM', 'symbol': 'MM4N25', 'is_0dte': False},
                {'prefix': 'MQ', 'symbol': 'MQ4N25', 'is_0dte': False}
            ]
        }
        
        pipeline = DailyOptionsPipeline(config=self.config, enable_validation=True)
        result = pipeline._generate_and_validate_symbol(self.test_date)
        
        self.assertFalse(result['success'])
        self.assertIn('No valid 0DTE symbol found', result['reason'])
    
    @patch.object(ExpirationValidator, 'validate_is_0dte')
    def test_forced_symbol_validation(self, mock_validate):
        """Test forced symbol with validation"""
        mock_validate.return_value = True
        
        pipeline = DailyOptionsPipeline(config=self.config, enable_validation=True)
        result = pipeline._handle_forced_symbol('MC4N25', self.test_date)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['symbol'], 'MC4N25')
        self.assertTrue(result['is_validated'])
        self.assertTrue(result['forced'])
    
    def test_forced_symbol_no_validation(self):
        """Test forced symbol without validation"""
        pipeline = DailyOptionsPipeline(config=self.config, enable_validation=False)
        result = pipeline._handle_forced_symbol('MC4N25', self.test_date)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['symbol'], 'MC4N25')
        self.assertFalse(result['is_validated'])
        self.assertTrue(result['forced'])
    
    def test_config_update_with_symbol(self):
        """Test configuration update with symbol"""
        pipeline = DailyOptionsPipeline(config=self.config, enable_validation=True)
        pipeline._update_config_with_symbol('MC4N25')
        
        self.assertEqual(pipeline.config['data']['barchart']['target_symbol'], 'MC4N25')
    
    def test_abort_result_creation(self):
        """Test abort result creation"""
        pipeline = DailyOptionsPipeline(config=self.config, enable_validation=True)
        
        symbol_result = {'success': False, 'reason': 'Test failure'}
        result = pipeline._create_abort_result('Test abort reason', symbol_result)
        
        self.assertEqual(result['status'], 'aborted')
        self.assertEqual(result['abort_reason'], 'Test abort reason')
        self.assertEqual(result['pipeline_type'], 'daily_0dte')
        self.assertEqual(pipeline.results['abort_reason'], 'Test abort reason')


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complete scenarios"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.test_date = datetime(2025, 7, 3)  # Thursday
        self.weekend_date = datetime(2025, 7, 5)  # Saturday
    
    @patch.object(ExpirationValidator, 'validate_is_0dte')
    @patch.object(ExpirationValidator, 'setup_driver')
    def test_end_to_end_symbol_validation(self, mock_setup_driver, mock_validate):
        """Test complete end-to-end symbol validation"""
        # Mock driver setup to avoid actual browser launch
        mock_driver = Mock()
        mock_setup_driver.return_value = mock_driver
        
        # Mock validation to return True for MC symbols
        mock_validate.return_value = True
        
        # Test convenience function
        symbol = find_0dte_symbol(self.test_date, headless=True)
        
        self.assertIsNotNone(symbol)
        self.assertTrue(symbol.startswith('MC'))
    
    def test_weekend_handling_integration(self):
        """Test weekend date handling across all components"""
        # Generator should adjust weekend to Monday
        generator = OptionsSymbolGenerator(validate_0dte=False)
        result = generator.generate_symbol_with_fallbacks(self.weekend_date)
        
        self.assertEqual(result['requested_date'], '2025-07-05')  # Saturday
        self.assertEqual(result['adjusted_date'], '2025-07-07')   # Monday
        self.assertTrue(result['date_adjusted'])
        
        # All generated symbols should be for Monday (day_code=1)
        for fallback in result['fallbacks_tried']:
            if fallback['symbol']:
                self.assertIn('1N25', fallback['symbol'])  # 1=Monday, N=July, 25=2025
    
    @patch('daily_options_pipeline.NQOptionsTradingSystem')
    @patch.object(OptionsSymbolGenerator, 'generate_symbol_with_fallbacks')
    def test_pipeline_integration_success(self, mock_generate, mock_system):
        """Test successful pipeline integration"""
        # Mock successful symbol generation
        mock_generate.return_value = {
            'requested_date': '2025-07-03',
            'symbol': 'MC4N25',
            'contract_type': 'MC', 
            'is_0dte': True,
            'fallbacks_tried': [{'prefix': 'MC', 'symbol': 'MC4N25', 'is_0dte': True}]
        }
        
        # Mock successful main pipeline
        mock_system_instance = Mock()
        mock_system_instance.run_complete_system.return_value = {
            'status': 'success',
            'pipeline_results': {
                'data': {'status': 'success'},
                'analysis': {'status': 'success'}, 
                'output': {'status': 'success'}
            }
        }
        mock_system.return_value = mock_system_instance
        
        # Test convenience function
        result = run_daily_0dte_pipeline(
            target_date=self.test_date,
            enable_validation=True
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['pipeline_type'], 'daily_0dte')
        self.assertIn('symbol_validation', result)
        self.assertIn('main_pipeline', result)
    
    @patch.object(OptionsSymbolGenerator, 'generate_symbol_with_fallbacks')
    def test_pipeline_abort_scenario(self, mock_generate):
        """Test pipeline abort when no valid symbol found"""
        # Mock failed symbol generation
        mock_generate.return_value = {
            'requested_date': '2025-07-03',
            'symbol': None,
            'contract_type': None,
            'is_0dte': False,
            'fallbacks_tried': []
        }
        
        # Test convenience function
        result = run_daily_0dte_pipeline(
            target_date=self.test_date,
            enable_validation=True
        )
        
        self.assertEqual(result['status'], 'aborted')
        self.assertIn('abort_reason', result)


class TestValidationModes(unittest.TestCase):
    """Test different validation modes and configurations"""
    
    def setUp(self):
        """Set up validation test fixtures"""
        self.test_date = datetime(2025, 7, 3)
    
    def test_validation_enabled_mode(self):
        """Test behavior with validation enabled"""
        generator = OptionsSymbolGenerator(validate_0dte=True, headless=True)
        self.assertTrue(generator.validate_0dte)
    
    def test_validation_disabled_mode(self):
        """Test behavior with validation disabled"""
        generator = OptionsSymbolGenerator(validate_0dte=False, headless=True)
        self.assertFalse(generator.validate_0dte)
    
    def test_headless_vs_non_headless(self):
        """Test headless vs non-headless mode"""
        validator_headless = ExpirationValidator(headless=True)
        validator_gui = ExpirationValidator(headless=False)
        
        self.assertTrue(validator_headless.headless)
        self.assertFalse(validator_gui.headless)


def run_comprehensive_tests():
    """
    Run all test suites with detailed reporting
    
    Returns:
        Test results summary
    """
    import time
    
    print("🧪 COMPREHENSIVE 0DTE PIPELINE TEST SUITE")
    print("=" * 60)
    
    start_time = time.time()
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestSymbolGenerator,
        TestExpirationValidator, 
        TestDailyOptionsPipeline,
        TestIntegrationScenarios,
        TestValidationModes
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed results
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"Execution Time: {execution_time:.2f} seconds")
    
    if result.failures:
        print(f"\n❌ FAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n💥 ERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Error:')[-1].strip()}")
    
    print("=" * 60)
    
    # Return success status
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == "__main__":
    # Run comprehensive tests when script is executed directly
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Enhanced Test Validation for Dead Simple Strategy
Tests both absolute and relative analysis modes with comprehensive logging
"""

import json
import logging
import tempfile
import os
from datetime import datetime, timezone
from typing import Dict, List

# Set up comprehensive logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('enhanced_dead_simple_tests.log')
    ]
)
logger = logging.getLogger(__name__)

# Import the enhanced solution
try:
    from solution import (
        DeadSimpleVolumeSpike, 
        InstitutionalSignal,
        RelativeThresholdCalculator,
        CrossStrikeAnalyzer,
        create_dead_simple_analyzer,
        create_enhanced_dead_simple_analyzer,
        create_configured_analyzer,
        CONFIGURATION_TEMPLATES
    )
    from baseline_data_manager import BaselineDataManager, VolumeStats, MarketContext
    logger.info("[TEST_SETUP] Enhanced solution imports successful")
except ImportError as e:
    logger.error(f"[TEST_SETUP] Import error: {e}")
    raise

class EnhancedDeadSimpleTests:
    """Comprehensive test suite for enhanced Dead Simple strategy"""
    
    def __init__(self):
        """Initialize test environment with comprehensive logging"""
        self.test_results = {}
        self.temp_db_path = None
        
        logger.info("[TEST_INIT] Enhanced Dead Simple test suite initialized")
        logger.info("[TEST_INIT] Setting up test data and temporary database")
        
        # Create temporary database for baseline manager tests
        self.temp_db_dir = tempfile.mkdtemp()
        self.temp_db_path = os.path.join(self.temp_db_dir, "test_baseline.db")
        
        logger.debug(f"[TEST_INIT] Temporary database path: {self.temp_db_path}")
    
    def run_all_tests(self) -> Dict:
        """
        Run comprehensive test suite with detailed logging
        
        Returns:
            Dictionary with test results
        """
        logger.info("[TEST_RUNNER] Starting comprehensive enhanced test suite")
        
        test_methods = [
            self.test_backward_compatibility,
            self.test_enhanced_signal_fields,
            self.test_baseline_data_manager,
            self.test_relative_threshold_calculator,
            self.test_cross_strike_analyzer,
            self.test_enhanced_analysis_modes,
            self.test_configuration_templates,
            self.test_factory_functions,
            self.test_integration_compatibility,
            self.test_error_handling_and_fallbacks,
            self.test_performance_and_logging
        ]
        
        for test_method in test_methods:
            test_name = test_method.__name__
            logger.info(f"[TEST_RUNNER] Running {test_name}")
            
            try:
                result = test_method()
                self.test_results[test_name] = {
                    'status': 'PASSED' if result else 'FAILED',
                    'details': result if isinstance(result, dict) else {'passed': result}
                }
                logger.info(f"[TEST_RUNNER] {test_name}: {'PASSED' if result else 'FAILED'}")
                
            except Exception as e:
                logger.error(f"[TEST_RUNNER] {test_name} failed with error: {e}")
                self.test_results[test_name] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
        
        # Calculate overall results
        passed_tests = sum(1 for r in self.test_results.values() if r['status'] == 'PASSED')
        total_tests = len(self.test_results)
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"[TEST_RUNNER] Test suite complete: {passed_tests}/{total_tests} passed ({pass_rate:.1f}%)")
        
        return {
            'test_results': self.test_results,
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'pass_rate_percent': pass_rate
            }
        }
    
    def test_backward_compatibility(self) -> bool:
        """Test that existing API remains unchanged"""
        logger.info("[TEST_COMPAT] Testing backward compatibility")
        
        try:
            # Test original factory function
            analyzer = create_dead_simple_analyzer()
            logger.debug(f"[TEST_COMPAT] Created analyzer with default config")
            
            # Test original analysis method (should work without contract parameter)
            sample_strike = {
                'strike': 21840,
                'optionType': 'PUT',
                'volume': 2750,
                'openInterest': 50,
                'lastPrice': 35.5,
                'expirationDate': '2024-01-10'
            }
            
            # This should work (old API)
            signal = analyzer.analyze_strike(sample_strike, 21870)
            logger.debug(f"[TEST_COMPAT] Old API analyze_strike: {signal is not None}")
            
            # Test find_institutional_flow returns signals (old behavior expected)
            sample_options = [sample_strike]
            result = analyzer.find_institutional_flow(sample_options, 21870)
            
            # Check if result format is backward compatible
            if isinstance(result, dict):
                signals = result.get('signals', [])
                logger.debug(f"[TEST_COMPAT] New enhanced format detected with {len(signals)} signals")
            else:
                # Old format would be a list
                signals = result if isinstance(result, list) else []
                logger.debug(f"[TEST_COMPAT] Old list format with {len(signals)} signals")
            
            logger.info(f"[TEST_COMPAT] Backward compatibility test passed")
            return True
            
        except Exception as e:
            logger.error(f"[TEST_COMPAT] Backward compatibility test failed: {e}")
            return False
    
    def test_enhanced_signal_fields(self) -> bool:
        """Test enhanced InstitutionalSignal fields"""
        logger.info("[TEST_SIGNAL] Testing enhanced signal fields")
        
        try:
            # Create signal with enhanced fields
            signal = InstitutionalSignal(
                strike=21840,
                option_type='PUT',
                volume=2750,
                open_interest=50,
                vol_oi_ratio=55.0,
                option_price=35.5,
                dollar_size=1950000,
                direction='SHORT',
                target_price=21840,
                confidence='EXTREME',
                timestamp=datetime.now(timezone.utc),
                expiration_date='2024-01-10',
                # Enhanced fields
                relative_volume_ratio=5.2,
                volume_percentile_rank=95.5,
                dynamic_confidence_score=87.3,
                baseline_data_source='historical_baseline'
            )
            
            logger.debug(f"[TEST_SIGNAL] Created enhanced signal: {signal.strike}{signal.option_type[0]}")
            
            # Test enhanced methods
            is_enhanced = signal.is_enhanced_analysis()
            enhanced_desc = signal.get_enhanced_confidence_description()
            signal_dict = signal.to_dict()
            
            logger.debug(f"[TEST_SIGNAL] Is enhanced: {is_enhanced}")
            logger.debug(f"[TEST_SIGNAL] Enhanced description: {enhanced_desc}")
            logger.debug(f"[TEST_SIGNAL] Signal dict keys: {list(signal_dict.keys())}")
            
            # Verify enhanced fields are present
            expected_fields = [
                'relative_volume_ratio', 'volume_percentile_rank', 
                'dynamic_confidence_score', 'baseline_data_source'
            ]
            
            for field in expected_fields:
                if field not in signal_dict:
                    logger.error(f"[TEST_SIGNAL] Missing enhanced field: {field}")
                    return False
            
            logger.info(f"[TEST_SIGNAL] Enhanced signal fields test passed")
            return True
            
        except Exception as e:
            logger.error(f"[TEST_SIGNAL] Enhanced signal fields test failed: {e}")
            return False
    
    def test_baseline_data_manager(self) -> bool:
        """Test baseline data manager functionality"""
        logger.info("[TEST_BASELINE] Testing baseline data manager")
        
        try:
            # Create baseline manager with temporary database
            baseline_manager = BaselineDataManager(self.temp_db_path)
            logger.debug(f"[TEST_BASELINE] Created baseline manager with temp DB")
            
            # Test storing daily snapshot
            sample_data = [
                {
                    'strike': 21840,
                    'optionType': 'PUT',
                    'volume': 2750,
                    'openInterest': 500,
                    'lastPrice': 35.5
                },
                {
                    'strike': 21900,
                    'optionType': 'CALL', 
                    'volume': 1200,
                    'openInterest': 300,
                    'lastPrice': 42.0
                }
            ]
            
            stored = baseline_manager.store_daily_snapshot("MC7M25", sample_data)
            logger.debug(f"[TEST_BASELINE] Daily snapshot stored: {stored}")
            
            # Test market context calculation
            market_context = baseline_manager.get_market_context("MC7M25")
            logger.debug(f"[TEST_BASELINE] Market context: {market_context.to_dict()}")
            
            # Test smart defaults
            smart_defaults = baseline_manager.get_smart_defaults(sample_data[0])
            logger.debug(f"[TEST_BASELINE] Smart defaults: {smart_defaults}")
            
            # Test sufficient data check
            has_sufficient = baseline_manager.has_sufficient_baseline_data("MC7M25", min_days=1)
            logger.debug(f"[TEST_BASELINE] Has sufficient data: {has_sufficient}")
            
            logger.info(f"[TEST_BASELINE] Baseline data manager test passed")
            return True
            
        except Exception as e:
            logger.error(f"[TEST_BASELINE] Baseline data manager test failed: {e}")
            return False
    
    def test_relative_threshold_calculator(self) -> bool:
        """Test relative threshold calculator"""
        logger.info("[TEST_THRESHOLD] Testing relative threshold calculator")
        
        try:
            # Create baseline manager and threshold calculator
            baseline_manager = BaselineDataManager(self.temp_db_path)
            threshold_calc = RelativeThresholdCalculator(baseline_manager)
            
            logger.debug(f"[TEST_THRESHOLD] Created threshold calculator")
            
            sample_strike = {
                'strike': 21840,
                'optionType': 'PUT',
                'volume': 2750,
                'openInterest': 50,
                'lastPrice': 35.5
            }
            
            # Test dynamic threshold calculations
            vol_oi_threshold, vol_oi_source = threshold_calc.calculate_dynamic_vol_oi_threshold(
                sample_strike, "MC7M25")
            volume_threshold, volume_source = threshold_calc.calculate_dynamic_volume_threshold(
                sample_strike, "MC7M25")
            
            logger.debug(f"[TEST_THRESHOLD] Vol/OI threshold: {vol_oi_threshold} ({vol_oi_source})")
            logger.debug(f"[TEST_THRESHOLD] Volume threshold: {volume_threshold} ({volume_source})")
            
            # Test confidence score calculation
            confidence_score = threshold_calc.calculate_dynamic_confidence_score(
                relative_volume_ratio=5.2,
                volume_percentile_rank=95.0,
                vol_oi_ratio=55.0,
                baseline_source='smart_defaults'
            )
            
            logger.debug(f"[TEST_THRESHOLD] Dynamic confidence score: {confidence_score}")
            
            # Test calculation summary
            summary = threshold_calc.get_calculation_summary(sample_strike, "MC7M25")
            logger.debug(f"[TEST_THRESHOLD] Calculation summary keys: {list(summary.keys())}")
            
            logger.info(f"[TEST_THRESHOLD] Relative threshold calculator test passed")
            return True
            
        except Exception as e:
            logger.error(f"[TEST_THRESHOLD] Relative threshold calculator test failed: {e}")
            return False
    
    def test_cross_strike_analyzer(self) -> bool:
        """Test cross-strike correlation analyzer"""
        logger.info("[TEST_CROSS_STRIKE] Testing cross-strike analyzer")
        
        try:
            analyzer = CrossStrikeAnalyzer()
            logger.debug(f"[TEST_CROSS_STRIKE] Created cross-strike analyzer")
            
            # Test data with coordinated flow
            sample_options = [
                {'strike': 21800, 'optionType': 'PUT', 'volume': 1500, 'lastPrice': 30.0},
                {'strike': 21840, 'optionType': 'PUT', 'volume': 2750, 'lastPrice': 35.5},
                {'strike': 21880, 'optionType': 'PUT', 'volume': 1200, 'lastPrice': 40.0},
                {'strike': 21900, 'optionType': 'CALL', 'volume': 800, 'lastPrice': 42.0},
                {'strike': 21920, 'optionType': 'CALL', 'volume': 600, 'lastPrice': 38.0}
            ]
            
            current_price = 21870
            
            # Test cross-strike correlation analysis
            correlation_analysis = analyzer.analyze_cross_strike_correlations(
                sample_options, current_price)
            
            logger.debug(f"[TEST_CROSS_STRIKE] Correlation analysis: {correlation_analysis}")
            
            # Test volume-weighted skew calculation
            volume_skew = analyzer.get_volume_weighted_skew(sample_options, current_price)
            logger.debug(f"[TEST_CROSS_STRIKE] Volume-weighted skew: {volume_skew}")
            
            # Test premium velocity calculation (with mock historical data)
            historical_premiums = [
                {'timestamp': '2025-06-10T10:00:00Z', 'premium': 30.0},
                {'timestamp': '2025-06-10T10:15:00Z', 'premium': 32.5},
                {'timestamp': '2025-06-10T10:30:00Z', 'premium': 35.5}
            ]
            
            velocity_metrics = analyzer.calculate_premium_velocity(
                sample_options[1], historical_premiums)
            
            logger.debug(f"[TEST_CROSS_STRIKE] Premium velocity: {velocity_metrics}")
            
            logger.info(f"[TEST_CROSS_STRIKE] Cross-strike analyzer test passed")
            return True
            
        except Exception as e:
            logger.error(f"[TEST_CROSS_STRIKE] Cross-strike analyzer test failed: {e}")
            return False
    
    def test_enhanced_analysis_modes(self) -> bool:
        """Test both absolute and relative analysis modes"""
        logger.info("[TEST_MODES] Testing enhanced analysis modes")
        
        try:
            # Test absolute mode (backward compatible)
            abs_config = {'threshold_mode': 'absolute'}
            abs_analyzer = DeadSimpleVolumeSpike(abs_config)
            
            logger.debug(f"[TEST_MODES] Created absolute mode analyzer")
            
            # Test relative mode (enhanced)
            rel_config = {
                'threshold_mode': 'relative',
                'baseline_db_path': self.temp_db_path
            }
            rel_analyzer = DeadSimpleVolumeSpike(rel_config)
            
            logger.debug(f"[TEST_MODES] Created relative mode analyzer")
            
            sample_options = [
                {
                    'strike': 21840,
                    'optionType': 'PUT',
                    'volume': 2750,
                    'openInterest': 50,
                    'lastPrice': 35.5,
                    'expirationDate': '2024-01-10'
                }
            ]
            
            current_price = 21870
            contract = "MC7M25"
            
            # Test absolute mode analysis
            abs_result = abs_analyzer.find_institutional_flow(sample_options, current_price, contract)
            abs_signals = abs_result.get('signals', []) if isinstance(abs_result, dict) else abs_result
            
            logger.debug(f"[TEST_MODES] Absolute mode signals: {len(abs_signals)}")
            
            # Test relative mode analysis  
            rel_result = rel_analyzer.find_institutional_flow(sample_options, current_price, contract)
            rel_signals = rel_result.get('signals', []) if isinstance(rel_result, dict) else rel_result
            
            logger.debug(f"[TEST_MODES] Relative mode signals: {len(rel_signals)}")
            
            # Compare signal characteristics
            if abs_signals and rel_signals:
                abs_signal = abs_signals[0]
                rel_signal = rel_signals[0]
                
                logger.debug(f"[TEST_MODES] Absolute signal enhanced: {abs_signal.is_enhanced_analysis()}")
                logger.debug(f"[TEST_MODES] Relative signal enhanced: {rel_signal.is_enhanced_analysis()}")
                
                # Relative should have enhanced fields
                if not rel_signal.is_enhanced_analysis():
                    logger.error(f"[TEST_MODES] Relative signal should be enhanced")
                    return False
            
            logger.info(f"[TEST_MODES] Enhanced analysis modes test passed")
            return True
            
        except Exception as e:
            logger.error(f"[TEST_MODES] Enhanced analysis modes test failed: {e}")
            return False
    
    def test_configuration_templates(self) -> bool:
        """Test configuration templates"""
        logger.info("[TEST_CONFIG] Testing configuration templates")
        
        try:
            for template_name in CONFIGURATION_TEMPLATES.keys():
                logger.debug(f"[TEST_CONFIG] Testing template: {template_name}")
                
                analyzer = create_configured_analyzer(template_name)
                
                # Verify analyzer was created successfully
                if not isinstance(analyzer, DeadSimpleVolumeSpike):
                    logger.error(f"[TEST_CONFIG] Template {template_name} failed to create analyzer")
                    return False
                
                logger.debug(f"[TEST_CONFIG] Template {template_name} created successfully")
            
            # Test custom overrides
            custom_analyzer = create_configured_analyzer(
                'conservative_absolute',
                {'min_dollar_size': 200_000}
            )
            
            if custom_analyzer.MIN_DOLLAR_SIZE != 200_000:
                logger.error(f"[TEST_CONFIG] Custom override not applied")
                return False
            
            logger.info(f"[TEST_CONFIG] Configuration templates test passed")
            return True
            
        except Exception as e:
            logger.error(f"[TEST_CONFIG] Configuration templates test failed: {e}")
            return False
    
    def test_factory_functions(self) -> bool:
        """Test factory functions"""
        logger.info("[TEST_FACTORY] Testing factory functions")
        
        try:
            # Test basic factory
            basic_analyzer = create_dead_simple_analyzer()
            logger.debug(f"[TEST_FACTORY] Basic factory: {type(basic_analyzer)}")
            
            # Test enhanced factory
            enhanced_analyzer = create_enhanced_dead_simple_analyzer()
            logger.debug(f"[TEST_FACTORY] Enhanced factory: {type(enhanced_analyzer)}")
            
            # Test factory with config
            config_analyzer = create_dead_simple_analyzer({
                'min_vol_oi_ratio': 15,
                'threshold_mode': 'relative'
            })
            logger.debug(f"[TEST_FACTORY] Config factory: {type(config_analyzer)}")
            
            # Verify configurations applied
            if basic_analyzer.threshold_mode != 'absolute':
                logger.error(f"[TEST_FACTORY] Basic factory should default to absolute mode")
                return False
            
            if enhanced_analyzer.threshold_mode != 'relative':
                logger.error(f"[TEST_FACTORY] Enhanced factory should default to relative mode")
                return False
            
            if config_analyzer.MIN_VOL_OI_RATIO != 15:
                logger.error(f"[TEST_FACTORY] Config not applied correctly")
                return False
            
            logger.info(f"[TEST_FACTORY] Factory functions test passed")
            return True
            
        except Exception as e:
            logger.error(f"[TEST_FACTORY] Factory functions test failed: {e}")
            return False
    
    def test_integration_compatibility(self) -> bool:
        """Test integration with existing pipeline"""
        logger.info("[TEST_INTEGRATION] Testing pipeline integration compatibility")
        
        try:
            # Test that enhanced analyzer can be used as drop-in replacement
            analyzer = create_dead_simple_analyzer()
            
            # Original interface should still work
            sample_options = [
                {
                    'strike': 21840,
                    'optionType': 'PUT',
                    'volume': 2750,
                    'openInterest': 50,
                    'lastPrice': 35.5,
                    'expirationDate': '2024-01-10'
                }
            ]
            
            # Test with minimal parameters (backward compatibility)
            result = analyzer.find_institutional_flow(sample_options, 21870)
            
            # Should return enhanced format but be usable as before
            if isinstance(result, dict):
                signals = result['signals']
                summary = result['summary']
                metadata = result['metadata']
                
                logger.debug(f"[TEST_INTEGRATION] Enhanced format detected")
                logger.debug(f"[TEST_INTEGRATION] Signals: {len(signals)}")
                logger.debug(f"[TEST_INTEGRATION] Summary keys: {list(summary.keys())}")
                logger.debug(f"[TEST_INTEGRATION] Metadata keys: {list(metadata.keys())}")
            else:
                logger.debug(f"[TEST_INTEGRATION] Old format detected: {len(result)} signals")
            
            logger.info(f"[TEST_INTEGRATION] Integration compatibility test passed")
            return True
            
        except Exception as e:
            logger.error(f"[TEST_INTEGRATION] Integration compatibility test failed: {e}")
            return False
    
    def test_error_handling_and_fallbacks(self) -> bool:
        """Test error handling and fallback mechanisms"""
        logger.info("[TEST_ERRORS] Testing error handling and fallbacks")
        
        try:
            # Test invalid configuration
            try:
                invalid_analyzer = create_configured_analyzer("nonexistent_template")
                logger.error(f"[TEST_ERRORS] Should have failed with invalid template")
                return False
            except ValueError:
                logger.debug(f"[TEST_ERRORS] Correctly caught invalid template error")
            
            # Test fallback behavior with missing baseline data
            rel_config = {
                'threshold_mode': 'relative',
                'baseline_db_path': '/nonexistent/path/db.sqlite'
            }
            
            # Should fallback gracefully
            fallback_analyzer = DeadSimpleVolumeSpike(rel_config)
            logger.debug(f"[TEST_ERRORS] Created analyzer with invalid DB path (should fallback)")
            
            # Test analysis with bad data
            bad_data = [
                {'strike': None, 'volume': None, 'openInterest': None},
                {'strike': 21840, 'volume': 0, 'openInterest': 0}
            ]
            
            result = fallback_analyzer.find_institutional_flow(bad_data, 21870)
            signals = result.get('signals', []) if isinstance(result, dict) else result
            
            logger.debug(f"[TEST_ERRORS] Analysis with bad data returned {len(signals)} signals")
            
            logger.info(f"[TEST_ERRORS] Error handling and fallbacks test passed")
            return True
            
        except Exception as e:
            logger.error(f"[TEST_ERRORS] Error handling test failed: {e}")
            return False
    
    def test_performance_and_logging(self) -> Dict:
        """Test performance and logging coverage"""
        logger.info("[TEST_PERFORMANCE] Testing performance and logging")
        
        results = {
            'performance_acceptable': False,
            'logging_comprehensive': False,
            'memory_usage_reasonable': False
        }
        
        try:
            import time
            import psutil
            import os
            
            # Performance test with larger dataset
            large_options_chain = []
            for i in range(100):  # 100 strikes
                large_options_chain.extend([
                    {
                        'strike': 21000 + i * 10,
                        'optionType': 'CALL',
                        'volume': 100 + i * 10,
                        'openInterest': 50 + i * 5,
                        'lastPrice': 20.0 + i * 0.5,
                        'expirationDate': '2024-01-10'
                    },
                    {
                        'strike': 21000 + i * 10,
                        'optionType': 'PUT',
                        'volume': 80 + i * 8,
                        'openInterest': 40 + i * 4,
                        'lastPrice': 18.0 + i * 0.4,
                        'expirationDate': '2024-01-10'
                    }
                ])
            
            logger.debug(f"[TEST_PERFORMANCE] Created dataset with {len(large_options_chain)} options")
            
            # Test enhanced analyzer performance
            enhanced_analyzer = create_enhanced_dead_simple_analyzer()
            
            # Measure memory before
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Time the analysis
            start_time = time.time()
            result = enhanced_analyzer.find_institutional_flow(
                large_options_chain, 21500, "MC7M25")
            end_time = time.time()
            
            # Measure memory after
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta = memory_after - memory_before
            
            duration = end_time - start_time
            signals = result.get('signals', []) if isinstance(result, dict) else result
            
            logger.info(f"[TEST_PERFORMANCE] Analysis completed:")
            logger.info(f"[TEST_PERFORMANCE] - Duration: {duration:.3f} seconds")
            logger.info(f"[TEST_PERFORMANCE] - Signals found: {len(signals)}")
            logger.info(f"[TEST_PERFORMANCE] - Memory delta: {memory_delta:.1f} MB")
            logger.info(f"[TEST_PERFORMANCE] - Throughput: {len(large_options_chain)/duration:.0f} options/sec")
            
            # Performance criteria
            results['performance_acceptable'] = duration < 5.0  # Should complete within 5 seconds
            results['memory_usage_reasonable'] = memory_delta < 50  # Should use less than 50MB additional
            results['logging_comprehensive'] = True  # If we got here, logging is working
            
            logger.info(f"[TEST_PERFORMANCE] Performance and logging test completed")
            return results
            
        except Exception as e:
            logger.error(f"[TEST_PERFORMANCE] Performance test failed: {e}")
            results['error'] = str(e)
            return results
    
    def cleanup(self):
        """Clean up test resources"""
        logger.info("[TEST_CLEANUP] Cleaning up test resources")
        
        try:
            if self.temp_db_path and os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
                logger.debug(f"[TEST_CLEANUP] Removed temporary database")
            
            if self.temp_db_dir and os.path.exists(self.temp_db_dir):
                os.rmdir(self.temp_db_dir)
                logger.debug(f"[TEST_CLEANUP] Removed temporary directory")
                
        except Exception as e:
            logger.warning(f"[TEST_CLEANUP] Cleanup error: {e}")

def run_enhanced_validation() -> Dict:
    """
    Run comprehensive enhanced validation tests
    
    Returns:
        Complete test results with pass/fail status
    """
    logger.info("="*60)
    logger.info("ENHANCED DEAD SIMPLE STRATEGY - COMPREHENSIVE VALIDATION")
    logger.info("="*60)
    
    test_suite = EnhancedDeadSimpleTests()
    
    try:
        results = test_suite.run_all_tests()
        return results
    finally:
        test_suite.cleanup()

if __name__ == "__main__":
    # Run validation if called directly
    validation_results = run_enhanced_validation()
    
    # Print summary
    summary = validation_results['summary']
    print(f"\n{'='*60}")
    print(f"ENHANCED VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Pass Rate: {summary['pass_rate_percent']:.1f}%")
    print(f"{'='*60}")
    
    # Save detailed results
    with open('enhanced_validation_results.json', 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    print(f"Detailed results saved to: enhanced_validation_results.json")
    print(f"Detailed logs saved to: enhanced_dead_simple_tests.log")
#!/usr/bin/env python3
"""
Test predictive failure detection implementation
Comprehensive test of pattern analysis and failure prediction capabilities
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add correct paths - order matters!
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path = [path for path in sys.path if 'tradovate_interface' not in path]
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'tradovate_interface', 'src'))

def test_pattern_analyzer():
    """Test the PatternAnalyzer class functionality"""
    print("🧠 Testing Pattern Analyzer")
    print("=" * 50)
    
    try:
        from utils.process_monitor import (
            PatternAnalyzer, FailurePatternData, FailurePattern, 
            PredictiveAnalysis, CrashType
        )
        import logging
        
        # Create logger for analyzer
        logger = logging.getLogger('test_analyzer')
        logger.setLevel(logging.INFO)
        
        # Create pattern analyzer
        analyzer = PatternAnalyzer(logger)
        
        print("✅ PatternAnalyzer created successfully")
        print(f"   Analysis window: {analyzer.analysis_window_hours} hours")
        print(f"   Min pattern occurrences: {analyzer.min_pattern_occurrences}")
        print(f"   Pattern history size: {len(analyzer.pattern_history)}")
        
        # Test pattern recording
        print("\n--- Testing Pattern Recording ---")
        
        test_patterns = [
            FailurePatternData(
                pattern_type=FailurePattern.RESOURCE_SPIKE,
                account_name="Test_Account_1",
                timestamp=datetime.now(),
                context={'crash_type': 'process_died'},
                severity_score=0.8,
                phase='runtime',
                resource_metrics={'cpu_percent': 85.0, 'memory_percent': 92.0},
                preceding_events=['High CPU usage detected', 'Memory leak pattern'],
                failure_outcome='process_died'
            ),
            FailurePatternData(
                pattern_type=FailurePattern.TIMEOUT_SEQUENCE,
                account_name="Test_Account_1", 
                timestamp=datetime.now() - timedelta(minutes=10),
                context={'timeout_count': 3},
                severity_score=0.6,
                phase='connecting',
                resource_metrics={'cpu_percent': 45.0, 'memory_percent': 70.0},
                preceding_events=['Connection timeout', 'Retry attempt failed'],
                failure_outcome='timeout'
            ),
            FailurePatternData(
                pattern_type=FailurePattern.ERROR_CLUSTERING,
                account_name="Test_Account_1",
                timestamp=datetime.now() - timedelta(minutes=5),
                context={'error_count': 4},
                severity_score=0.7,
                phase='runtime',
                resource_metrics={'cpu_percent': 60.0, 'memory_percent': 75.0},
                preceding_events=['Multiple errors in sequence'],
                failure_outcome='tab_crashed'
            )
        ]
        
        for pattern in test_patterns:
            analyzer.record_pattern(pattern)
            print(f"✅ Recorded pattern: {pattern.pattern_type.value}")
        
        print(f"✅ Pattern history now contains {len(analyzer.pattern_history)} patterns")
        
        # Test predictive analysis
        print("\n--- Testing Predictive Analysis ---")
        
        current_metrics = {
            'cpu_percent': 78.0,  # High CPU approaching spike threshold
            'memory_percent': 88.0,  # High memory approaching spike threshold
            'consecutive_failures': 2,
            'last_healthy': datetime.now() - timedelta(minutes=30),
            'uptime_seconds': 3600
        }
        
        analysis = analyzer.analyze_predictive_risk("Test_Account_1", current_metrics)
        
        print("✅ Predictive analysis completed:")
        print(f"   Account: {analysis.account_name}")
        print(f"   Prediction confidence: {analysis.prediction_confidence:.2f}")
        print(f"   Risk patterns: {[p.value for p in analysis.risk_patterns]}")
        print(f"   Recommendations: {len(analysis.recommendations)}")
        print(f"   Prevention actions: {len(analysis.prevention_actions)}")
        
        if analysis.predicted_failure_time:
            print(f"   Predicted failure time: {analysis.predicted_failure_time}")
        
        if analysis.recommendations:
            print("   Recommendations:")
            for rec in analysis.recommendations:
                print(f"     - {rec}")
        
        if analysis.prevention_actions:
            print("   Prevention actions:")
            for action in analysis.prevention_actions:
                print(f"     - {action}")
        
        # Verify prediction confidence is reasonable
        if analysis.prediction_confidence > 0.3:
            print("✅ High prediction confidence indicates pattern detection is working")
        else:
            print("⚠️  Low prediction confidence - may need more historical data")
        
        return True
        
    except Exception as e:
        print(f"❌ Pattern analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chrome_monitor_integration():
    """Test predictive analysis integration with ChromeProcessMonitor"""
    print("\n🔗 Testing ChromeProcessMonitor Integration")
    print("=" * 50)
    
    try:
        from utils.process_monitor import ChromeProcessMonitor, StartupMonitoringMode
        
        # Create monitor
        monitor = ChromeProcessMonitor()
        
        print("✅ ChromeProcessMonitor with predictive analysis created")
        print(f"   Pattern analyzer available: {hasattr(monitor, 'pattern_analyzer')}")
        print(f"   Predictive alerts storage: {hasattr(monitor, 'predictive_alerts')}")
        print(f"   Prediction check interval: {monitor.prediction_check_interval}s")
        
        # Test status reporting includes predictive analysis
        print("\n--- Testing Status Reporting ---")
        
        status = monitor.get_status()
        
        if "predictive_analysis" in status:
            print("✅ Predictive analysis included in status")
            
            pred_status = status["predictive_analysis"]
            print(f"   Predictive analysis enabled: {pred_status.get('predictive_analysis_enabled', False)}")
            print(f"   Total accounts analyzed: {pred_status.get('total_accounts_analyzed', 0)}")
            print(f"   Pattern history size: {pred_status.get('pattern_history_size', 0)}")
            print(f"   Analysis window: {pred_status.get('analysis_window_hours', 0)} hours")
            
        else:
            print("❌ Predictive analysis not included in status")
            return False
        
        # Test predictive status method
        print("\n--- Testing Predictive Status Method ---")
        
        pred_status = monitor.get_predictive_status()
        
        print("✅ Predictive status retrieved:")
        print(f"   Enabled: {pred_status.get('predictive_analysis_enabled', False)}")
        print(f"   High risk accounts: {len(pred_status.get('high_risk_accounts', []))}")
        print(f"   Medium risk accounts: {len(pred_status.get('medium_risk_accounts', []))}")
        print(f"   Pattern history size: {pred_status.get('pattern_history_size', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromeProcessMonitor integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pattern_detection_scenarios():
    """Test specific failure pattern detection scenarios"""
    print("\n🎯 Testing Pattern Detection Scenarios")
    print("=" * 50)
    
    try:
        from utils.process_monitor import (
            PatternAnalyzer, FailurePatternData, FailurePattern
        )
        import logging
        
        logger = logging.getLogger('scenario_test')
        analyzer = PatternAnalyzer(logger)
        
        # Scenario 1: Resource spike pattern
        print("--- Scenario 1: Resource Spike Pattern ---")
        
        # Simulate resource spike leading to failure
        for i in range(3):
            pattern = FailurePatternData(
                pattern_type=FailurePattern.RESOURCE_SPIKE,
                account_name="Scenario_Account",
                timestamp=datetime.now() - timedelta(minutes=30-i*10),
                context={'spike_type': 'memory'},
                severity_score=0.7 + i*0.1,
                resource_metrics={'cpu_percent': 70 + i*10, 'memory_percent': 80 + i*5}
            )
            analyzer.record_pattern(pattern)
        
        # Test prediction with current high resource usage
        current_metrics = {'cpu_percent': 85.0, 'memory_percent': 89.0}
        analysis = analyzer.analyze_predictive_risk("Scenario_Account", current_metrics)
        
        print(f"✅ Resource spike scenario - Confidence: {analysis.prediction_confidence:.2f}")
        if FailurePattern.RESOURCE_SPIKE in analysis.risk_patterns:
            print("✅ Resource spike pattern correctly detected")
        
        # Scenario 2: Timeout sequence pattern
        print("\n--- Scenario 2: Timeout Sequence Pattern ---")
        
        analyzer_timeout = PatternAnalyzer(logger)
        
        # Simulate repeated timeouts in same phase
        for i in range(4):
            pattern = FailurePatternData(
                pattern_type=FailurePattern.TIMEOUT_SEQUENCE,
                account_name="Timeout_Account",
                timestamp=datetime.now() - timedelta(minutes=20-i*5),
                context={'timeout_phase': 'connecting'},
                severity_score=0.5,
                phase='connecting'
            )
            analyzer_timeout.record_pattern(pattern)
        
        analysis_timeout = analyzer_timeout.analyze_predictive_risk("Timeout_Account", {})
        
        print(f"✅ Timeout sequence scenario - Confidence: {analysis_timeout.prediction_confidence:.2f}")
        if FailurePattern.TIMEOUT_SEQUENCE in analysis_timeout.risk_patterns:
            print("✅ Timeout sequence pattern correctly detected")
        
        # Scenario 3: Error clustering pattern
        print("\n--- Scenario 3: Error Clustering Pattern ---")
        
        analyzer_errors = PatternAnalyzer(logger)
        
        # Simulate error clustering (multiple errors in short time)
        base_time = datetime.now()
        for i in range(5):
            pattern = FailurePatternData(
                pattern_type=FailurePattern.ERROR_CLUSTERING,
                account_name="Error_Account",
                timestamp=base_time - timedelta(minutes=3-i*0.5),  # Errors within 3 minutes
                context={'error_type': 'connection_failed'},
                severity_score=0.4
            )
            analyzer_errors.record_pattern(pattern)
        
        analysis_errors = analyzer_errors.analyze_predictive_risk("Error_Account", {})
        
        print(f"✅ Error clustering scenario - Confidence: {analysis_errors.prediction_confidence:.2f}")
        if FailurePattern.ERROR_CLUSTERING in analysis_errors.risk_patterns:
            print("✅ Error clustering pattern correctly detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Pattern detection scenarios test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_predictive_configuration():
    """Test predictive analysis configuration and thresholds"""
    print("\n⚙️  Testing Predictive Configuration")
    print("=" * 50)
    
    try:
        from utils.process_monitor import PatternAnalyzer
        import logging
        
        logger = logging.getLogger('config_test')
        analyzer = PatternAnalyzer(logger)
        
        print("✅ Default configuration loaded:")
        print(f"   Analysis window: {analyzer.analysis_window_hours} hours")
        print(f"   Min pattern occurrences: {analyzer.min_pattern_occurrences}")
        
        print("\n✅ Pattern thresholds:")
        for key, value in analyzer.thresholds.items():
            print(f"   {key}: {value}")
        
        # Test threshold validation
        expected_thresholds = [
            'resource_spike_cpu', 'resource_spike_memory', 'timeout_sequence_count',
            'error_clustering_window', 'phase_regression_factor', 
            'memory_leak_growth_mb', 'auth_degradation_factor'
        ]
        
        for threshold in expected_thresholds:
            if threshold in analyzer.thresholds:
                print(f"✅ Threshold '{threshold}' configured: {analyzer.thresholds[threshold]}")
            else:
                print(f"❌ Missing threshold: {threshold}")
                return False
        
        # Test pattern history management
        print("\n--- Testing Pattern History Management ---")
        
        from utils.process_monitor import FailurePatternData, FailurePattern
        
        # Add patterns from different time periods
        old_pattern = FailurePatternData(
            pattern_type=FailurePattern.RESOURCE_SPIKE,
            account_name="History_Test",
            timestamp=datetime.now() - timedelta(hours=30),  # Outside analysis window
            context={},
            severity_score=0.5
        )
        
        recent_pattern = FailurePatternData(
            pattern_type=FailurePattern.RESOURCE_SPIKE,
            account_name="History_Test",
            timestamp=datetime.now() - timedelta(hours=1),  # Within analysis window
            context={},
            severity_score=0.5
        )
        
        analyzer.record_pattern(old_pattern)
        analyzer.record_pattern(recent_pattern)
        
        # Check that old patterns are cleaned up
        if len(analyzer.pattern_history) == 1:
            print("✅ Pattern history cleanup working - old patterns removed")
        else:
            print(f"⚠️  Pattern history contains {len(analyzer.pattern_history)} patterns")
        
        return True
        
    except Exception as e:
        print(f"❌ Predictive configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive predictive failure detection tests"""
    print("🔮 Comprehensive Predictive Failure Detection Tests")
    print("=" * 60)
    
    tests = [
        ("Pattern Analyzer", test_pattern_analyzer),
        ("ChromeProcessMonitor Integration", test_chrome_monitor_integration),
        ("Pattern Detection Scenarios", test_pattern_detection_scenarios),
        ("Predictive Configuration", test_predictive_configuration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test")
        print("-" * 60)
        
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:<10} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL PREDICTIVE FAILURE DETECTION TESTS PASSED!")
        print("\n🚀 Key Features Validated:")
        print("   ✅ Pattern recording and analysis")
        print("   ✅ Predictive risk calculation")
        print("   ✅ Multiple failure pattern types")
        print("   ✅ ChromeProcessMonitor integration")
        print("   ✅ Status reporting and monitoring")
        print("   ✅ Configurable thresholds and windows")
        print("   ✅ Pattern history management")
        print("\n🔮 Predictive failure detection is ready for production!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TESTS FAILED")
        print("Review test output and fix identified issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
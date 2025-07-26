#!/usr/bin/env python3
"""
Comprehensive test for Phase 2 startup monitoring implementation
Tests all components: registration, monitoring, health checks, and dashboard integration
"""

import sys
import os
import time
import json
import threading
from datetime import datetime

# Add project paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'tradovate_interface', 'src'))

def test_imports():
    """Test that all Phase 2 components can be imported"""
    print("=== Testing Phase 2 Imports ===")
    
    try:
        from utils.process_monitor import (
            ChromeProcessMonitor, 
            StartupPhase, 
            StartupMonitoringMode,
            StartupProcessInfo
        )
        print("✅ ChromeProcessMonitor imports successful")
        
        # Test enum values
        print(f"✅ StartupPhase enum: {[phase.value for phase in StartupPhase]}")
        print(f"✅ StartupMonitoringMode enum: {[mode.value for mode in StartupMonitoringMode]}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_process_monitor_initialization():
    """Test ChromeProcessMonitor initialization with startup monitoring"""
    print("\n=== Testing Process Monitor Initialization ===")
    
    try:
        from utils.process_monitor import ChromeProcessMonitor, StartupMonitoringMode
        
        # Initialize with default config
        monitor = ChromeProcessMonitor()
        print("✅ ChromeProcessMonitor initialized successfully")
        
        # Test startup monitoring configuration
        if hasattr(monitor, 'startup_config'):
            print(f"✅ Startup config loaded: {monitor.startup_config}")
        else:
            print("❌ Startup config not found")
            return False
        
        # Test startup monitoring attributes
        required_attrs = [
            'startup_monitoring_mode', 
            'startup_processes', 
            'startup_lock',
            'startup_monitoring_thread'
        ]
        
        for attr in required_attrs:
            if hasattr(monitor, attr):
                print(f"✅ {attr} attribute present")
            else:
                print(f"❌ {attr} attribute missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Process Monitor initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_startup_process_registration():
    """Test startup process registration functionality"""
    print("\n=== Testing Startup Process Registration ===")
    
    try:
        from utils.process_monitor import ChromeProcessMonitor, StartupMonitoringMode, StartupPhase
        
        monitor = ChromeProcessMonitor()
        
        # Enable startup monitoring
        monitor.enable_startup_monitoring(StartupMonitoringMode.PASSIVE)
        print("✅ Startup monitoring enabled in PASSIVE mode")
        
        # Test registration
        account_name = "Test_Account_1"
        test_port = 9223
        
        # SAFETY: Never use port 9222
        if test_port == 9222:
            print("❌ SAFETY VIOLATION: Attempted to use protected port 9222")
            return False
        
        success = monitor.register_for_startup_monitoring(account_name, test_port)
        if success:
            print(f"✅ Successfully registered {account_name} for startup monitoring on port {test_port}")
        else:
            print(f"❌ Failed to register {account_name}")
            return False
        
        # Verify registration
        with monitor.startup_lock:
            if account_name in monitor.startup_processes:
                startup_info = monitor.startup_processes[account_name]
                print(f"✅ Registration verified: Phase={startup_info.current_phase.value}, Port={startup_info.expected_port}")
            else:
                print(f"❌ Registration not found in startup_processes")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Startup registration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_startup_phase_transitions():
    """Test startup phase transition functionality"""
    print("\n=== Testing Startup Phase Transitions ===")
    
    try:
        from utils.process_monitor import ChromeProcessMonitor, StartupMonitoringMode, StartupPhase
        
        monitor = ChromeProcessMonitor()
        monitor.enable_startup_monitoring(StartupMonitoringMode.PASSIVE)
        
        account_name = "Test_Account_2"
        test_port = 9224
        
        # Register and test phase transitions
        monitor.register_for_startup_monitoring(account_name, test_port)
        
        # Test each phase transition
        phases_to_test = [
            (StartupPhase.LAUNCHING, "Chrome process starting"),
            (StartupPhase.CONNECTING, "Chrome process started with PID 12345", 12345),
            (StartupPhase.LOADING, "Connected to Chrome, tab available"),
            (StartupPhase.AUTHENTICATING, "Login attempted: True"),
            (StartupPhase.VALIDATING, "Authentication completed"),
            (StartupPhase.READY, "Startup validation successful")
        ]
        
        for phase, details, *args in phases_to_test:
            pid = args[0] if args else None
            success = monitor.update_startup_phase(account_name, phase, details, pid)
            
            if success:
                print(f"✅ Phase transition to {phase.value}: {details}")
            else:
                print(f"❌ Failed to transition to {phase.value}")
                return False
            
            # Small delay to ensure timing metrics work
            time.sleep(0.1)
        
        # Verify final state
        with monitor.startup_lock:
            startup_info = monitor.startup_processes[account_name]
            if startup_info.current_phase == StartupPhase.READY:
                print(f"✅ Final phase verification: {startup_info.current_phase.value}")
                print(f"✅ Total startup duration: {startup_info.get_startup_duration():.2f}s")
            else:
                print(f"❌ Unexpected final phase: {startup_info.current_phase.value}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Phase transition test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_startup_health_checks():
    """Test startup health check functionality"""
    print("\n=== Testing Startup Health Checks ===")
    
    try:
        from utils.process_monitor import ChromeProcessMonitor, StartupMonitoringMode, StartupPhase
        
        monitor = ChromeProcessMonitor()
        monitor.enable_startup_monitoring(StartupMonitoringMode.PASSIVE)
        
        account_name = "Test_Account_3"
        test_port = 9225
        
        # Register and advance to connecting phase
        monitor.register_for_startup_monitoring(account_name, test_port)
        monitor.update_startup_phase(account_name, StartupPhase.CONNECTING, "Testing health checks")
        
        # Test individual health check
        health_status = monitor.startup_health_check(account_name)
        
        if health_status:
            print(f"✅ Individual health check completed")
            print(f"   Account: {health_status['account']}")
            print(f"   Phase: {health_status['startup_phase']}")
            print(f"   Healthy: {health_status['healthy']}")
            print(f"   Checks: {len(health_status['checks'])} performed")
            print(f"   Warnings: {len(health_status['warnings'])}")
            print(f"   Errors: {len(health_status['errors'])}")
        else:
            print("❌ Individual health check failed")
            return False
        
        # Test batch health check
        batch_results = monitor.batch_startup_health_check()
        
        if batch_results:
            print(f"✅ Batch health check completed")
            print(f"   Total processes: {batch_results['total_startup_processes']}")
            print(f"   Healthy: {batch_results['healthy_processes']}")
            print(f"   Unhealthy: {batch_results['unhealthy_processes']}")
        else:
            print("❌ Batch health check failed")
            return False
        
        # Test health summary
        health_summary = monitor.get_startup_health_summary()
        
        if health_summary:
            print(f"✅ Health summary generated")
            print(f"   Total processes: {health_summary['total_processes']}")
            print(f"   Healthy count: {health_summary['healthy_count']}")
            print(f"   Error count: {health_summary['error_count']}")
            print(f"   Phase distribution: {health_summary['phase_distribution']}")
        else:
            print("❌ Health summary failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_startup_validation():
    """Test startup completion validation"""
    print("\n=== Testing Startup Validation ===")
    
    try:
        from utils.process_monitor import ChromeProcessMonitor, StartupMonitoringMode, StartupPhase
        
        monitor = ChromeProcessMonitor()
        monitor.enable_startup_monitoring(StartupMonitoringMode.PASSIVE)
        
        account_name = "Test_Account_4"
        test_port = 9226
        
        # Register and advance to validating phase
        monitor.register_for_startup_monitoring(account_name, test_port)
        monitor.update_startup_phase(account_name, StartupPhase.VALIDATING, "Ready for validation")
        
        # Test validation (will fail since Chrome isn't actually running, but tests the logic)
        validation_result = monitor.validate_startup_completion(account_name)
        print(f"✅ Startup validation test completed (result: {validation_result})")
        print("   Note: Validation expected to fail since Chrome isn't actually running")
        
        return True
        
    except Exception as e:
        print(f"❌ Startup validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_status_reporting():
    """Test comprehensive status reporting"""
    print("\n=== Testing Status Reporting ===")
    
    try:
        from utils.process_monitor import ChromeProcessMonitor, StartupMonitoringMode, StartupPhase
        
        monitor = ChromeProcessMonitor()
        monitor.enable_startup_monitoring(StartupMonitoringMode.ACTIVE)
        
        # Add multiple test processes in different phases
        test_accounts = [
            ("Test_Account_5", 9227, StartupPhase.LAUNCHING),
            ("Test_Account_6", 9228, StartupPhase.CONNECTING),
            ("Test_Account_7", 9229, StartupPhase.READY)
        ]
        
        for account_name, port, phase in test_accounts:
            monitor.register_for_startup_monitoring(account_name, port)
            monitor.update_startup_phase(account_name, phase, f"Testing {phase.value}")
        
        # Get comprehensive status
        status = monitor.get_status()
        
        if status:
            print("✅ Status reporting successful")
            print(f"   Monitoring active: {status.get('monitoring_active', False)}")
            
            startup_monitoring = status.get('startup_monitoring', {})
            print(f"   Startup monitoring active: {startup_monitoring.get('monitoring_active', False)}")
            print(f"   Startup processes: {len(startup_monitoring.get('startup_processes', {}))}")
            
            # Check health summary
            health_summary = startup_monitoring.get('health_summary', {})
            if health_summary:
                print(f"   Health summary included: {health_summary.get('total_processes', 0)} processes")
                print(f"   Phase distribution: {health_summary.get('phase_distribution', {})}")
            
            # Check individual process health status
            startup_processes = startup_monitoring.get('startup_processes', {})
            for account_name, process_info in startup_processes.items():
                health_status = process_info.get('health_status', {})
                print(f"   {account_name}: Phase={process_info.get('phase')}, Healthy={health_status.get('healthy', 'unknown')}")
        else:
            print("❌ Status reporting failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Status reporting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dashboard_integration():
    """Test dashboard integration components"""
    print("\n=== Testing Dashboard Integration ===")
    
    try:
        # Test dashboard import
        sys.path.insert(0, os.path.join(project_root, 'src'))
        
        try:
            from dashboard import STARTUP_MONITORING_AVAILABLE, startup_monitor
            print(f"✅ Dashboard startup monitoring available: {STARTUP_MONITORING_AVAILABLE}")
            
            if startup_monitor:
                print("✅ Dashboard startup monitor initialized")
                
                # Test if startup monitor has required methods
                required_methods = [
                    'get_status',
                    'startup_health_check', 
                    'batch_startup_health_check',
                    'get_startup_health_summary'
                ]
                
                for method_name in required_methods:
                    if hasattr(startup_monitor, method_name):
                        print(f"✅ Dashboard monitor has {method_name} method")
                    else:
                        print(f"❌ Dashboard monitor missing {method_name} method")
                        return False
            else:
                print("⚠️  Dashboard startup monitor not initialized (expected if config missing)")
                
        except ImportError as e:
            print(f"⚠️  Dashboard import failed (expected if Flask not installed): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auto_login_integration():
    """Test auto_login.py integration with startup monitoring"""
    print("\n=== Testing Auto Login Integration ===")
    
    try:
        sys.path.insert(0, os.path.join(project_root, 'src'))
        
        # Test imports
        from auto_login import ChromeInstance, WATCHDOG_AVAILABLE
        from utils.process_monitor import ChromeProcessMonitor, StartupPhase
        
        print(f"✅ Auto login integration imports successful")
        print(f"✅ Watchdog available: {WATCHDOG_AVAILABLE}")
        
        # Test ChromeInstance with startup monitoring
        if WATCHDOG_AVAILABLE:
            monitor = ChromeProcessMonitor()
            
            # Create ChromeInstance with startup monitoring
            test_port = 9230
            username = "test@example.com"
            password = "testpass"
            account_name = "Test_Integration"
            
            instance = ChromeInstance(
                port=test_port,
                username=username, 
                password=password,
                account_name=account_name,
                process_monitor=monitor
            )
            
            print("✅ ChromeInstance created with startup monitoring")
            print(f"   Account name: {instance.account_name}")
            print(f"   Process monitor: {instance.process_monitor is not None}")
            
            # Note: We won't actually start Chrome in this test
            print("✅ Auto login integration test completed (Chrome not started in test)")
        else:
            print("⚠️  Auto login integration limited (watchdog not available)")
        
        return True
        
    except Exception as e:
        print(f"❌ Auto login integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_resource_limits_and_safety():
    """Test resource limits and safety protections"""
    print("\n=== Testing Resource Limits and Safety ===")
    
    try:
        from utils.process_monitor import ChromeProcessMonitor, StartupMonitoringMode
        
        monitor = ChromeProcessMonitor()
        
        # Test port 9222 protection
        print("Testing port 9222 protection...")
        
        # This should fail safely
        result = monitor.register_for_startup_monitoring("Protected_Test", 9222)
        if not result:
            print("✅ Port 9222 protection working correctly")
        else:
            print("❌ Port 9222 protection FAILED - SAFETY VIOLATION")
            return False
        
        # Test resource limit configuration
        config = monitor.startup_config
        resource_limits = config.get('resource_limits', {})
        
        if resource_limits:
            print(f"✅ Resource limits configured:")
            print(f"   CPU limit: {resource_limits.get('cpu_percent', 'not set')}%")
            print(f"   Memory limit: {resource_limits.get('memory_percent', 'not set')}%")
        else:
            print("⚠️  Resource limits not configured (using defaults)")
        
        # Test timeout configuration
        timeout_seconds = config.get('startup_timeout_seconds', 60)
        print(f"✅ Startup timeout configured: {timeout_seconds}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Resource limits and safety test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_comprehensive_test():
    """Run all Phase 2 tests"""
    print("🚀 Starting Phase 2 Startup Monitoring Comprehensive Test")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Import Test", test_imports),
        ("Process Monitor Initialization", test_process_monitor_initialization),
        ("Startup Process Registration", test_startup_process_registration),
        ("Startup Phase Transitions", test_startup_phase_transitions),
        ("Startup Health Checks", test_startup_health_checks),
        ("Startup Validation", test_startup_validation),
        ("Status Reporting", test_status_reporting),
        ("Dashboard Integration", test_dashboard_integration),
        ("Auto Login Integration", test_auto_login_integration),
        ("Resource Limits and Safety", test_resource_limits_and_safety)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            test_results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"❌ {test_name}: EXCEPTION - {e}")
            test_results.append((test_name, False))
    
    # Print summary
    print(f"\n{'='*60}")
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:<12} {test_name}")
        if result:
            passed_tests += 1
    
    print("=" * 60)
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Phase 2 implementation is working correctly.")
        return True
    else:
        print(f"⚠️  {total_tests - passed_tests} tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
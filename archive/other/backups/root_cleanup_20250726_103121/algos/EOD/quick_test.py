#!/usr/bin/env python3
"""
Quick Test Runner - Execute key validation tests with timeouts
"""

import os
import sys
import subprocess
from pathlib import Path

def run_test(test_path, description, timeout=30):
    """Run a single test with timeout"""
    print(f"\n{'='*60}")
    print(f"TESTING: {description}")
    print(f"Path: {test_path}")
    print(f"{'='*60}")
    
    try:
        # Change to the test directory and run the test
        test_dir = os.path.dirname(test_path)
        test_file = os.path.basename(test_path)
        
        if test_dir:
            original_dir = os.getcwd()
            os.chdir(test_dir)
        
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=timeout)
        
        if test_dir:
            os.chdir(original_dir)
            
        if result.returncode == 0:
            print("✅ PASSED")
            return True
        else:
            print("❌ FAILED")
            print("STDERR:", result.stderr[-200:])  # Last 200 chars
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT ({timeout}s)")
        return False
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False

def main():
    """Run quick validation tests"""
    project_root = Path(__file__).parent
    
    # Define validation tests to run (avoid long-running integration tests)
    tests = [
        # Core utilities (critical)
        ("tasks/test_common_utils.py", "Common Utilities", 10),
        
        # Fast validation tests
        ("tasks/options_trading_system/data_ingestion/tradovate_api_data/test_validation.py", "Tradovate API Data", 20),
        ("tasks/options_trading_system/analysis_engine/risk_analysis/test_validation.py", "Risk Analysis", 20),
        
        # Test the report generator (should work now)
        ("tasks/options_trading_system/output_generation/report_generator/test_validation.py", "Report Generator", 30),
    ]
    
    print("🚀 STARTING QUICK VALIDATION TEST SUITE")
    print(f"Project root: {project_root}")
    
    results = []
    passed = 0
    failed = 0
    
    for test_path, description, timeout in tests:
        full_path = project_root / test_path
        if full_path.exists():
            success = run_test(str(full_path), description, timeout)
            results.append((description, success))
            if success:
                passed += 1
            else:
                failed += 1
        else:
            print(f"⚠️  SKIPPED: {description} (file not found: {test_path})")
            results.append((description, None))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    for description, result in results:
        if result is True:
            print(f"✅ {description}")
        elif result is False:
            print(f"❌ {description}")
        else:
            print(f"⚠️  {description} (skipped)")
    
    print(f"\n🎯 FINAL RESULTS:")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Skipped: {len([r for r in results if r[1] is None])}")
    
    success_rate = passed / (passed + failed) if (passed + failed) > 0 else 0
    print(f"   Success Rate: {success_rate:.1%}")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
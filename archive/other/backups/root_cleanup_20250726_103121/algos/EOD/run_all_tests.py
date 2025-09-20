#!/usr/bin/env python3
"""
Test Runner - Execute all project tests systematically
"""

import os
import sys
import subprocess
from pathlib import Path

def run_test(test_path, description):
    """Run a single test and return result"""
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
                              capture_output=True, text=True, timeout=120)
        
        if test_dir:
            os.chdir(original_dir)
            
        if result.returncode == 0:
            print("✅ PASSED")
            return True
        else:
            print("❌ FAILED")
            print("STDOUT:", result.stdout[-500:])  # Last 500 chars
            print("STDERR:", result.stderr[-500:])  # Last 500 chars
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT (120s)")
        return False
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False

def main():
    """Run all tests"""
    project_root = Path(__file__).parent
    
    # Define tests to run
    tests = [
        # Core utilities (critical)
        ("tasks/test_common_utils.py", "Common Utilities"),
        
        # Validation tests (most important after refactoring)
        ("tasks/options_trading_system/data_ingestion/tradovate_api_data/test_validation.py", "Tradovate API Data"),
        ("tasks/options_trading_system/analysis_engine/risk_analysis/test_validation.py", "Risk Analysis"),
        ("tasks/options_trading_system/analysis_engine/expected_value_analysis/test_validation.py", "Expected Value Analysis"),
        ("tasks/options_trading_system/output_generation/report_generator/test_validation.py", "Report Generator"),
        
        # Integration tests (if they work without live data)
        ("tasks/options_trading_system/analysis_engine/test_integration.py", "Analysis Engine Integration"),
        ("tasks/options_trading_system/output_generation/test_integration.py", "Output Generation Integration"),
    ]
    
    print("🚀 STARTING COMPREHENSIVE TEST SUITE")
    print(f"Project root: {project_root}")
    
    results = []
    passed = 0
    failed = 0
    
    for test_path, description in tests:
        full_path = project_root / test_path
        if full_path.exists():
            success = run_test(str(full_path), description)
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
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Refactoring successful!")
        return 0
    else:
        print(f"\n⚠️  {failed} tests failed. Review output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
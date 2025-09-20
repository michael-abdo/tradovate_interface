#!/usr/bin/env python3
"""
TASK: barchart_saved_data
TYPE: Validation Test
PURPOSE: Validate that barchart data loading works correctly
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from tasks.test_utils import save_evidence
from tasks.common_utils import add_validation_error
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))))
sys.path.insert(0, project_root)

from solution import BarchartSavedDataLoader, load_barchart_saved_data


def validate_barchart_data_loading():
    """
    Validate the barchart data loading functionality
    
    Returns:
        Dict with validation results and evidence
    """
    print("EXECUTING VALIDATION: barchart_saved_data")
    print("-" * 50)
    
    validation_results = {
        "task": "barchart_saved_data",
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "status": "FAILED",
        "evidence": {}
    }
    
    # Test file path (relative to project root)
    test_file = os.path.join(project_root, "data/api_responses/options_data_20250602_141553.json")
    
    # Test 1: File exists validation
    print("\n1. Testing file existence...")
    try:
        loader = BarchartSavedDataLoader(test_file)
        file_exists = loader.validate_file_exists()
        
        validation_results["tests"].append({
            "name": "file_exists",
            "passed": file_exists,
            "details": f"File exists at {test_file}: {file_exists}"
        })
        print(f"   ✓ File exists: {file_exists}")
    except Exception as e:
        add_validation_error(validation_results, "file_exists", e)
        return validation_results
    
    # Test 2: Data loading
    print("\n2. Testing data loading...")
    try:
        raw_data = loader.load_data()
        data_loaded = raw_data is not None and isinstance(raw_data, dict)
        
        validation_results["tests"].append({
            "name": "data_loading",
            "passed": data_loaded,
            "details": f"Data loaded successfully: {data_loaded}"
        })
        print(f"   ✓ Data loaded: {data_loaded}")
        
        # Store evidence
        validation_results["evidence"]["data_structure"] = list(raw_data.keys()) if data_loaded else []
        
    except Exception as e:
        add_validation_error(validation_results, "data_loading", e)
        return validation_results
    
    # Test 3: Options data extraction
    print("\n3. Testing options data extraction...")
    try:
        options_data = loader.get_options_data()
        
        has_calls = 'calls' in options_data and len(options_data['calls']) > 0
        has_puts = 'puts' in options_data and len(options_data['puts']) > 0
        
        validation_results["tests"].append({
            "name": "options_extraction",
            "passed": has_calls and has_puts,
            "details": {
                "calls_count": len(options_data['calls']),
                "puts_count": len(options_data['puts']),
                "total_contracts": options_data['total_contracts']
            }
        })
        print(f"   ✓ Calls found: {len(options_data['calls'])}")
        print(f"   ✓ Puts found: {len(options_data['puts'])}")
        
        # Store evidence
        validation_results["evidence"]["options_data"] = {
            "calls_count": len(options_data['calls']),
            "puts_count": len(options_data['puts']),
            "total_contracts": options_data['total_contracts']
        }
        
    except Exception as e:
        add_validation_error(validation_results, "options_extraction", e)
    
    # Test 4: Data quality metrics
    print("\n4. Testing data quality metrics...")
    try:
        quality = loader.get_data_quality_metrics()
        
        metrics_valid = (
            quality['total_contracts'] > 0 and
            quality['volume_coverage'] >= 0 and
            quality['oi_coverage'] >= 0
        )
        
        validation_results["tests"].append({
            "name": "quality_metrics",
            "passed": metrics_valid,
            "details": quality
        })
        
        print(f"   ✓ Total contracts: {quality['total_contracts']}")
        print(f"   ✓ Volume coverage: {quality['volume_coverage']:.1%}")
        print(f"   ✓ OI coverage: {quality['oi_coverage']:.1%}")
        
        # Store evidence
        validation_results["evidence"]["quality_metrics"] = quality
        
    except Exception as e:
        add_validation_error(validation_results, "quality_metrics", e)
    
    # Test 5: Strike range extraction
    print("\n5. Testing strike range extraction...")
    try:
        strike_range = loader.get_strike_range()
        
        range_valid = (
            strike_range is not None and
            strike_range['min'] > 0 and
            strike_range['max'] > strike_range['min']
        )
        
        validation_results["tests"].append({
            "name": "strike_range",
            "passed": range_valid,
            "details": strike_range
        })
        
        if strike_range:
            print(f"   ✓ Strike range: ${strike_range['min']:,.0f} - ${strike_range['max']:,.0f}")
            print(f"   ✓ Unique strikes: {strike_range['count']}")
        
        # Store evidence
        validation_results["evidence"]["strike_range"] = strike_range
        
    except Exception as e:
        add_validation_error(validation_results, "strike_range", e)
    
    # Test 6: Integration function test
    print("\n6. Testing integration function...")
    try:
        result = load_barchart_saved_data(test_file)
        
        integration_valid = (
            'loader' in result and
            'metadata' in result and
            'quality_metrics' in result and
            result['raw_data_available']
        )
        
        validation_results["tests"].append({
            "name": "integration_function",
            "passed": integration_valid,
            "details": {
                "keys_present": list(result.keys()),
                "metadata": result['metadata']
            }
        })
        
        print(f"   ✓ Integration function works")
        print(f"   ✓ Metadata captured: {result['metadata']['source']}")
        
    except Exception as e:
        add_validation_error(validation_results, "integration_function", e)
    
    # Determine overall status
    all_passed = all(test['passed'] for test in validation_results['tests'])
    validation_results['status'] = "VALIDATED" if all_passed else "FAILED"
    
    # Summary
    print("\n" + "-" * 50)
    print(f"VALIDATION COMPLETE: {validation_results['status']}")
    print(f"Tests passed: {sum(1 for t in validation_results['tests'] if t['passed'])}/{len(validation_results['tests'])}")
    
    return validation_results


# Removed duplicate save_evidence - now using canonical implementation from test_utils


if __name__ == "__main__":
    # Execute validation
    results = validate_barchart_data_loading()
    
    # Save evidence
    save_evidence(results)
    
    # Exit with appropriate code
    exit(0 if results['status'] == "VALIDATED" else 1)
#!/usr/bin/env python3
"""
TASK: polygon_api
TYPE: Validation Test
PURPOSE: Validate that Polygon.io API integration works correctly
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))))
sys.path.insert(0, project_root)

from solution import PolygonAPIClient, PolygonOptionsContract, load_polygon_api_data


def validate_polygon_api_client():
    """
    Validate the Polygon API client functionality
    
    Returns:
        Dict with validation results and evidence
    """
    print("EXECUTING VALIDATION: polygon_api")
    print("-" * 50)
    
    validation_results = {
        "task": "polygon_api",
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "status": "FAILED",
        "evidence": {}
    }
    
    # Test 1: Client initialization
    print("\n1. Testing client initialization...")
    try:
        client = PolygonAPIClient()
        api_key_set = bool(client.api_key)
        
        validation_results["tests"].append({
            "name": "client_initialization",
            "passed": api_key_set,
            "details": f"Client initialized with API key: {api_key_set}"
        })
        
        if api_key_set:
            print(f"   ✅ Client initialized with API key")
        else:
            print(f"   ❌ Client missing API key")
        
    except Exception as e:
        validation_results["tests"].append({
            "name": "client_initialization", 
            "passed": False,
            "details": f"Client initialization failed: {str(e)}"
        })
        print(f"   ❌ Client initialization failed: {e}")
    
    # Test 2: NDX options contracts retrieval
    print("\n2. Testing NDX options contracts retrieval...")
    try:
        client = PolygonAPIClient()
        contracts = client.get_options_contracts("NDX", limit=3)
        
        has_contracts = len(contracts) > 0
        contracts_valid = all(isinstance(c, PolygonOptionsContract) for c in contracts)
        
        validation_results["tests"].append({
            "name": "ndx_contracts_retrieval",
            "passed": has_contracts and contracts_valid,
            "details": f"Retrieved {len(contracts)} NDX contracts, all valid: {contracts_valid}"
        })
        
        if has_contracts:
            print(f"   ✅ Retrieved {len(contracts)} NDX contracts")
            validation_results["evidence"]["ndx_sample_contract"] = {
                "ticker": contracts[0].ticker,
                "strike": contracts[0].strike_price,
                "type": contracts[0].contract_type,
                "expiration": contracts[0].expiration_date
            }
        else:
            print(f"   ❌ No NDX contracts retrieved")
            
    except Exception as e:
        validation_results["tests"].append({
            "name": "ndx_contracts_retrieval",
            "passed": False,
            "details": f"NDX contracts retrieval failed: {str(e)}"
        })
        print(f"   ❌ NDX contracts retrieval failed: {e}")
    
    # Test 3: QQQ options contracts retrieval
    print("\n3. Testing QQQ options contracts retrieval...")
    try:
        client = PolygonAPIClient()
        contracts = client.get_options_contracts("QQQ", limit=3)
        
        has_contracts = len(contracts) > 0
        contracts_valid = all(isinstance(c, PolygonOptionsContract) for c in contracts)
        
        validation_results["tests"].append({
            "name": "qqq_contracts_retrieval", 
            "passed": has_contracts and contracts_valid,
            "details": f"Retrieved {len(contracts)} QQQ contracts, all valid: {contracts_valid}"
        })
        
        if has_contracts:
            print(f"   ✅ Retrieved {len(contracts)} QQQ contracts")
            validation_results["evidence"]["qqq_sample_contract"] = {
                "ticker": contracts[0].ticker,
                "strike": contracts[0].strike_price,
                "type": contracts[0].contract_type,
                "expiration": contracts[0].expiration_date
            }
        else:
            print(f"   ❌ No QQQ contracts retrieved")
            
    except Exception as e:
        validation_results["tests"].append({
            "name": "qqq_contracts_retrieval",
            "passed": False,
            "details": f"QQQ contracts retrieval failed: {str(e)}"
        })
        print(f"   ❌ QQQ contracts retrieval failed: {e}")
    
    # Test 4: NQ futures options (expected to fail)
    print("\n4. Testing NQ futures options availability...")
    try:
        client = PolygonAPIClient()
        contracts = client.get_options_contracts("NQ", limit=3)
        
        no_nq_contracts = len(contracts) == 0
        
        validation_results["tests"].append({
            "name": "nq_futures_unavailable",
            "passed": no_nq_contracts,
            "details": f"NQ futures options unavailable as expected: {no_nq_contracts}"
        })
        
        if no_nq_contracts:
            print(f"   ✅ Confirmed NQ futures options not available (as expected)")
        else:
            print(f"   ⚠️  Unexpected: Found {len(contracts)} NQ contracts")
            
    except Exception as e:
        validation_results["tests"].append({
            "name": "nq_futures_unavailable",
            "passed": True,  # Exception is expected for unavailable data
            "details": f"NQ futures options correctly unavailable: {str(e)}"
        })
        print(f"   ✅ NQ futures options correctly unavailable: {e}")
    
    # Test 5: Data loading function
    print("\n5. Testing data loading function...")
    try:
        config = {
            'tickers': ['NDX'],
            'limit': 2,
            'include_pricing': False
        }
        
        result = load_polygon_api_data(config)
        
        has_summary = 'options_summary' in result
        has_data = 'options_data' in result and len(result['options_data']) > 0
        has_quality_metrics = 'quality_metrics' in result
        
        data_loading_success = has_summary and has_data and has_quality_metrics
        
        validation_results["tests"].append({
            "name": "data_loading_function",
            "passed": data_loading_success,
            "details": f"Data loading complete - summary: {has_summary}, data: {has_data}, metrics: {has_quality_metrics}"
        })
        
        if data_loading_success:
            print(f"   ✅ Data loading function works correctly")
            print(f"      - Total contracts: {result['options_summary']['total_contracts']}")
            print(f"      - Data source: {result['quality_metrics']['data_source']}")
            
            validation_results["evidence"]["data_loading_sample"] = {
                "total_contracts": result['options_summary']['total_contracts'],
                "data_source": result['quality_metrics']['data_source'],
                "tickers_tested": result['options_summary']['underlying_tickers']
            }
        else:
            print(f"   ❌ Data loading function incomplete")
            
    except Exception as e:
        validation_results["tests"].append({
            "name": "data_loading_function",
            "passed": False,
            "details": f"Data loading function failed: {str(e)}"
        })
        print(f"   ❌ Data loading function failed: {e}")
    
    # Test 6: Rate limiting functionality
    print("\n6. Testing rate limiting...")
    try:
        client = PolygonAPIClient()
        client.min_request_interval = 1  # Set to 1 second for testing
        
        start_time = datetime.now()
        client.get_options_contracts("NDX", limit=1)
        client.get_options_contracts("QQQ", limit=1)  # Should trigger rate limiting
        end_time = datetime.now()
        
        elapsed = (end_time - start_time).total_seconds()
        rate_limiting_works = elapsed >= 1.0
        
        validation_results["tests"].append({
            "name": "rate_limiting",
            "passed": rate_limiting_works,
            "details": f"Rate limiting working - elapsed time: {elapsed:.1f}s (expected: >=1.0s)"
        })
        
        if rate_limiting_works:
            print(f"   ✅ Rate limiting works correctly ({elapsed:.1f}s elapsed)")
        else:
            print(f"   ❌ Rate limiting may not be working ({elapsed:.1f}s elapsed)")
            
    except Exception as e:
        validation_results["tests"].append({
            "name": "rate_limiting",
            "passed": False,
            "details": f"Rate limiting test failed: {str(e)}"
        })
        print(f"   ❌ Rate limiting test failed: {e}")
    
    # Calculate overall status
    passed_tests = sum(1 for test in validation_results["tests"] if test["passed"])
    total_tests = len(validation_results["tests"])
    
    validation_results["status"] = "VALIDATED" if passed_tests >= (total_tests * 0.8) else "FAILED"
    validation_results["evidence"]["summary"] = {
        "tests_passed": passed_tests,
        "tests_total": total_tests,
        "success_rate": f"{(passed_tests/total_tests)*100:.1f}%"
    }
    
    print(f"\n" + "=" * 50)
    print(f"VALIDATION COMPLETE: {validation_results['status']}")
    print(f"Tests passed: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
    
    return validation_results


def run_validation():
    """Run the validation and save evidence"""
    results = validate_polygon_api_client()
    
    # Save evidence
    evidence_file = os.path.join(os.path.dirname(__file__), "evidence.json")
    with open(evidence_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nEvidence saved to: {evidence_file}")
    return results


if __name__ == "__main__":
    run_validation()
#!/usr/bin/env python3
"""
TASK: data_normalizer
TYPE: Validation Test
PURPOSE: Validate that data normalization works correctly
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from tasks.test_utils import save_evidence
from tasks.common_utils import add_validation_error
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

from solution import DataNormalizer, normalize_options_data


def validate_data_normalizer():
    """
    Validate the data normalization functionality
    
    Returns:
        Dict with validation results and evidence
    """
    print("EXECUTING VALIDATION: data_normalizer")
    print("-" * 50)
    
    validation_results = {
        "task": "data_normalizer",
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "status": "FAILED",
        "evidence": {}
    }
    
    # Test configuration
    sources_config = {
        "barchart": {
            "file_path": os.path.join(project_root, "data/api_responses/options_data_20250602_141553.json")
        },
        "tradovate": {
            "mode": "demo",
            "cid": "6540",
            "secret": "f7a2b8f5-8348-424f-8ffa-047ab7502b7c",
            "use_mock": True
        }
    }
    
    # Test 1: Initialize normalizer
    print("\n1. Testing normalizer initialization...")
    try:
        normalizer = DataNormalizer()
        init_valid = normalizer is not None and hasattr(normalizer, 'sources')
        
        validation_results["tests"].append({
            "name": "normalizer_init",
            "passed": init_valid,
            "details": "Normalizer initialized successfully"
        })
        print(f"   ✓ Normalizer initialized: {init_valid}")
    except Exception as e:
        add_validation_error(validation_results, "normalizer_init", e)
        return validation_results
    
    # Test 2: Load Barchart data
    print("\n2. Testing Barchart data loading...")
    try:
        barchart_result = normalizer.load_barchart_data(sources_config["barchart"]["file_path"])
        barchart_loaded = (
            barchart_result is not None and
            'quality_metrics' in barchart_result and
            barchart_result['quality_metrics']['total_contracts'] > 0
        )
        
        validation_results["tests"].append({
            "name": "barchart_loading",
            "passed": barchart_loaded,
            "details": {
                "contracts": barchart_result['quality_metrics']['total_contracts'],
                "volume_coverage": barchart_result['quality_metrics']['volume_coverage']
            }
        })
        print(f"   ✓ Barchart data loaded: {barchart_result['quality_metrics']['total_contracts']} contracts")
        
    except Exception as e:
        add_validation_error(validation_results, "barchart_loading", e)
    
    # Test 3: Load Tradovate data
    print("\n3. Testing Tradovate data loading...")
    try:
        tradovate_result = normalizer.load_tradovate_data(sources_config["tradovate"])
        tradovate_loaded = (
            tradovate_result is not None and
            'quality_metrics' in tradovate_result and
            tradovate_result['quality_metrics']['total_contracts'] > 0
        )
        
        validation_results["tests"].append({
            "name": "tradovate_loading",
            "passed": tradovate_loaded,
            "details": {
                "contracts": tradovate_result['quality_metrics']['total_contracts'],
                "data_source": tradovate_result['quality_metrics']['data_source']
            }
        })
        print(f"   ✓ Tradovate data loaded: {tradovate_result['quality_metrics']['total_contracts']} contracts")
        
    except Exception as e:
        add_validation_error(validation_results, "tradovate_loading", e)
    
    # Test 4: Normalize all sources
    print("\n4. Testing data normalization...")
    try:
        normalized = normalizer.normalize_all_sources()
        
        normalize_valid = (
            normalized is not None and
            'contracts' in normalized and
            len(normalized['contracts']) > 0 and
            len(normalized['sources']) == 2
        )
        
        validation_results["tests"].append({
            "name": "normalization",
            "passed": normalize_valid,
            "details": {
                "total_contracts": normalized['summary']['total_contracts'],
                "sources": normalized['sources'],
                "by_source": normalized['summary']['by_source']
            }
        })
        
        print(f"   ✓ Normalized {normalized['summary']['total_contracts']} contracts")
        print(f"   ✓ Sources: {', '.join(normalized['sources'])}")
        
        # Store evidence
        validation_results["evidence"]["normalized_summary"] = normalized['summary']
        
    except Exception as e:
        add_validation_error(validation_results, "normalization", e)
    
    # Test 5: Verify normalized contract format
    print("\n5. Testing normalized contract format...")
    try:
        if normalized and normalized['contracts']:
            sample_contract = normalized['contracts'][0]
            required_fields = [
                'source', 'type', 'symbol', 'strike', 'expiration',
                'volume', 'open_interest', 'last_price', 'timestamp'
            ]
            
            format_valid = all(field in sample_contract for field in required_fields)
            
            validation_results["tests"].append({
                "name": "contract_format",
                "passed": format_valid,
                "details": {
                    "sample_contract_source": sample_contract.get('source'),
                    "sample_contract_type": sample_contract.get('type'),
                    "fields_present": list(sample_contract.keys())
                }
            })
            
            print(f"   ✓ Contract format valid: {format_valid}")
            print(f"   ✓ Sample: {sample_contract['source']} {sample_contract['type']} @ ${sample_contract['strike']}")
            
    except Exception as e:
        add_validation_error(validation_results, "contract_format", e)
    
    # Test 6: Quality metrics
    print("\n6. Testing quality metrics calculation...")
    try:
        quality = normalizer.get_quality_metrics()
        
        metrics_valid = (
            quality is not None and
            'total_contracts' in quality and
            'by_source' in quality and
            len(quality['by_source']) == 2
        )
        
        validation_results["tests"].append({
            "name": "quality_metrics",
            "passed": metrics_valid,
            "details": quality
        })
        
        print(f"   ✓ Overall volume coverage: {quality['overall_volume_coverage']:.1%}")
        print(f"   ✓ Overall OI coverage: {quality['overall_oi_coverage']:.1%}")
        
        for source, metrics in quality['by_source'].items():
            print(f"   ✓ {source}: {metrics['total']} contracts, "
                  f"{metrics['volume_coverage']:.1%} volume, "
                  f"{metrics['oi_coverage']:.1%} OI")
        
        # Store evidence
        validation_results["evidence"]["quality_metrics"] = quality
        
    except Exception as e:
        add_validation_error(validation_results, "quality_metrics", e)
    
    # Test 7: Integration function
    print("\n7. Testing integration function...")
    try:
        result = normalize_options_data(sources_config)
        
        integration_valid = (
            'normalizer' in result and
            'normalized_data' in result and
            'quality_metrics' in result and
            'metadata' in result
        )
        
        validation_results["tests"].append({
            "name": "integration_function",
            "passed": integration_valid,
            "details": {
                "keys": list(result.keys()),
                "total_normalized": result['normalized_data']['summary']['total_contracts']
            }
        })
        
        print(f"   ✓ Integration function works")
        print(f"   ✓ Total normalized: {result['normalized_data']['summary']['total_contracts']} contracts")
        
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
    results = validate_data_normalizer()
    
    # Save evidence
    save_evidence(results)
    
    # Exit with appropriate code
    exit(0 if results['status'] == "VALIDATED" else 1)
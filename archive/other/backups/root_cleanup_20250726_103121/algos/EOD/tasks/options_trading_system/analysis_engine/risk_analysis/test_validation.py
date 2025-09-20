#!/usr/bin/env python3
"""
TASK: risk_analysis
TYPE: Leaf Task Validation Test
PURPOSE: Validate risk analysis functionality
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from tasks.test_utils import save_evidence
from tasks.common_utils import add_validation_error
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.insert(0, project_root)

from solution import RiskAnalyzer, run_risk_analysis


def validate_risk_analysis():
    """
    Validate the risk analysis functionality
    
    Returns:
        Dict with validation results and evidence
    """
    print("EXECUTING VALIDATION: risk_analysis")
    print("-" * 50)
    
    validation_results = {
        "task": "risk_analysis",
        "type": "leaf",
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "status": "FAILED",
        "evidence": {}
    }
    
    # Test configuration
    test_data_config = {
        "normalized_data": {
            "underlying_price": 21761.75,
            "contracts": [
                {
                    "strike": 21750,
                    "call_open_interest": 545,
                    "call_mark_price": 12.75,
                    "put_open_interest": 18,
                    "put_mark_price": 6.00,
                    "volume": 916
                },
                {
                    "strike": 21760,
                    "call_open_interest": 15,
                    "call_mark_price": 8.00,
                    "put_open_interest": 1,
                    "put_mark_price": 10.75,
                    "volume": 394
                },
                {
                    "strike": 21770,
                    "call_open_interest": 60,
                    "call_mark_price": 4.05,
                    "put_open_interest": 0,
                    "put_mark_price": 17.00,
                    "volume": 392
                },
                {
                    "strike": 21740,
                    "call_open_interest": 25,
                    "call_mark_price": 22.50,
                    "put_open_interest": 100,
                    "put_mark_price": 2.75,
                    "volume": 150
                }
            ]
        }
    }
    
    test_analysis_config = {
        "multiplier": 20,
        "immediate_threat_distance": 10,
        "near_term_distance": 25,
        "medium_term_distance": 50
    }
    
    # Test 1: Analyzer initialization
    print("\n1. Testing RiskAnalyzer initialization...")
    try:
        analyzer = RiskAnalyzer(test_analysis_config)
        init_valid = (
            analyzer.multiplier == 20 and
            analyzer.immediate_distance == 10 and
            analyzer.near_term_distance == 25 and
            analyzer.medium_term_distance == 50
        )
        
        validation_results["tests"].append({
            "name": "analyzer_init",
            "passed": init_valid,
            "details": f"Analyzer initialized with correct config: {init_valid}"
        })
        
        print(f"   ✓ Analyzer initialization: {init_valid}")
        
    except Exception as e:
        add_validation_error(validation_results, "analyzer_init", e)
        return validation_results
    
    # Test 2: Risk calculation functionality
    print("\n2. Testing risk calculation...")
    try:
        result = analyzer.analyze_risk(test_data_config)
        
        calc_valid = (
            result["status"] == "success" and
            "summary" in result and
            "threats" in result and
            "battle_zones" in result and
            "signals" in result and
            result["summary"]["total_call_risk"] > 0 and
            result["summary"]["total_put_risk"] > 0
        )
        
        validation_results["tests"].append({
            "name": "risk_calculation",
            "passed": calc_valid,
            "details": {
                "status": result.get("status"),
                "total_call_risk": result.get("summary", {}).get("total_call_risk"),
                "total_put_risk": result.get("summary", {}).get("total_put_risk"),
                "battle_zones_found": len(result.get("battle_zones", []))
            }
        })
        
        print(f"   ✓ Risk calculation: {calc_valid}")
        print(f"   ✓ Call risk: ${result['summary']['total_call_risk']:,.0f}")
        print(f"   ✓ Put risk: ${result['summary']['total_put_risk']:,.0f}")
        
    except Exception as e:
        add_validation_error(validation_results, "risk_calculation", e)
    
    # Test 3: Dominance analysis
    print("\n3. Testing dominance analysis...")
    try:
        result = analyzer.analyze_risk(test_data_config)
        
        dominance_valid = (
            "risk_ratio" in result["summary"] and
            "verdict" in result["summary"] and
            "bias" in result["summary"] and
            result["summary"]["risk_ratio"] > 0
        )
        
        validation_results["tests"].append({
            "name": "dominance_analysis",
            "passed": dominance_valid,
            "details": {
                "risk_ratio": result["summary"]["risk_ratio"],
                "verdict": result["summary"]["verdict"],
                "bias": result["summary"]["bias"]
            }
        })
        
        print(f"   ✓ Dominance analysis: {dominance_valid}")
        print(f"   ✓ Risk ratio: {result['summary']['risk_ratio']:.2f}")
        print(f"   ✓ Verdict: {result['summary']['verdict']}")
        
    except Exception as e:
        add_validation_error(validation_results, "dominance_analysis", e)
    
    # Test 4: Battle zone mapping
    print("\n4. Testing battle zone mapping...")
    try:
        result = analyzer.analyze_risk(test_data_config)
        
        battle_zones = result.get("battle_zones", [])
        
        battle_valid = (
            len(battle_zones) > 0 and
            all("danger_score" in zone for zone in battle_zones) and
            all("urgency" in zone for zone in battle_zones) and
            all("type" in zone for zone in battle_zones) and
            battle_zones == sorted(battle_zones, key=lambda x: x["danger_score"], reverse=True)
        )
        
        validation_results["tests"].append({
            "name": "battle_zone_mapping",
            "passed": battle_valid,
            "details": {
                "zones_found": len(battle_zones),
                "urgency_levels": list(set(zone["urgency"] for zone in battle_zones)),
                "defense_types": list(set(zone["type"] for zone in battle_zones))
            }
        })
        
        print(f"   ✓ Battle zone mapping: {battle_valid}")
        print(f"   ✓ Zones found: {len(battle_zones)}")
        if battle_zones:
            print(f"   ✓ Top zone: {battle_zones[0]['strike']} ({battle_zones[0]['urgency']})")
        
    except Exception as e:
        add_validation_error(validation_results, "battle_zone_mapping", e)
    
    # Test 5: Module-level function
    print("\n5. Testing module-level function...")
    try:
        result = run_risk_analysis(test_data_config, test_analysis_config)
        
        module_valid = (
            result is not None and
            result["status"] == "success" and
            "signals" in result and
            len(result["signals"]) > 0
        )
        
        validation_results["tests"].append({
            "name": "module_function",
            "passed": module_valid,
            "details": {
                "status": result.get("status"),
                "signals_generated": len(result.get("signals", [])),
                "metrics_available": "metrics" in result
            }
        })
        
        print(f"   ✓ Module function: {module_valid}")
        print(f"   ✓ Signals generated: {len(result['signals'])}")
        
        # Store evidence
        validation_results["evidence"]["sample_result"] = {
            "status": result["status"],
            "summary": result["summary"],
            "signals": result["signals"],
            "metrics": result["metrics"],
            "battle_zones_count": len(result["battle_zones"])
        }
        
    except Exception as e:
        add_validation_error(validation_results, "module_function", e)
    
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
    results = validate_risk_analysis()
    
    # Save evidence
    save_evidence(results)
    
    # Exit with appropriate code
    exit(0 if results['status'] == "VALIDATED" else 1)
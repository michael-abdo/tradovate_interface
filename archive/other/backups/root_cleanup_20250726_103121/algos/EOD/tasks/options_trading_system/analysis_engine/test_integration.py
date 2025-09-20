#!/usr/bin/env python3
"""
TASK: analysis_engine
TYPE: Parent Task Integration Test
PURPOSE: Validate that analysis engine coordinates all child strategies correctly
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tasks.test_utils import save_evidence
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from integration import AnalysisEngine, run_analysis_engine


def validate_analysis_engine():
    """
    Validate the analysis engine integration functionality
    
    Returns:
        Dict with validation results and evidence
    """
    print("EXECUTING VALIDATION: analysis_engine")
    print("-" * 50)
    
    validation_results = {
        "task": "analysis_engine",
        "type": "parent",
        "timestamp": datetime.now().isoformat(),
        "integration_tests": [],
        "status": "FAILED",
        "evidence": {}
    }
    
    # Test configuration
    data_config = {
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
    
    analysis_config = {
        "expected_value": {
            "weights": {
                "oi_factor": 0.35,
                "vol_factor": 0.25,
                "pcr_factor": 0.25,
                "distance_factor": 0.15
            },
            "min_ev": 10,  # Lower threshold for testing
            "min_probability": 0.50,
            "max_risk": 200,
            "min_risk_reward": 0.5
        },
        "momentum": {
            "volume_threshold": 50,
            "price_change_threshold": 0.03,
            "momentum_window": 3,
            "min_momentum_score": 0.4
        },
        "volatility": {
            "iv_percentile_threshold": 70,
            "iv_skew_threshold": 0.03,
            "term_structure_slope_threshold": 0.01,
            "min_volume_for_iv": 5
        }
    }
    
    # Test 1: Verify child task validations
    print("\n1. Checking child task validations...")
    try:
        child_validations = []
        
        # Check expected_value_analysis evidence
        ev_evidence_path = os.path.join(project_root, "tasks/options_trading_system/analysis_engine/expected_value_analysis/evidence.json")
        if os.path.exists(ev_evidence_path):
            with open(ev_evidence_path, 'r') as f:
                ev_evidence = json.load(f)
                child_validations.append({
                    "task": "expected_value_analysis",
                    "status": ev_evidence.get("status"),
                    "tests_passed": sum(1 for t in ev_evidence.get("tests", []) if t.get("passed")),
                    "tests_total": len(ev_evidence.get("tests", []))
                })
        
        # Check momentum_analysis evidence
        momentum_evidence_path = os.path.join(project_root, "tasks/options_trading_system/analysis_engine/momentum_analysis/evidence.json")
        if os.path.exists(momentum_evidence_path):
            with open(momentum_evidence_path, 'r') as f:
                momentum_evidence = json.load(f)
                child_validations.append({
                    "task": "momentum_analysis",
                    "status": momentum_evidence.get("status"),
                    "tests_passed": sum(1 for t in momentum_evidence.get("tests", []) if t.get("passed")),
                    "tests_total": len(momentum_evidence.get("tests", []))
                })
        
        # Check volatility_analysis evidence
        vol_evidence_path = os.path.join(project_root, "tasks/options_trading_system/analysis_engine/volatility_analysis/evidence.json")
        if os.path.exists(vol_evidence_path):
            with open(vol_evidence_path, 'r') as f:
                vol_evidence = json.load(f)
                child_validations.append({
                    "task": "volatility_analysis",
                    "status": vol_evidence.get("status"),
                    "tests_passed": sum(1 for t in vol_evidence.get("tests", []) if t.get("passed")),
                    "tests_total": len(vol_evidence.get("tests", []))
                })
        
        all_children_validated = all(child["status"] == "VALIDATED" for child in child_validations)
        
        validation_results["integration_tests"].append({
            "name": "child_validations",
            "passed": all_children_validated,
            "details": f"All {len(child_validations)} children validated: {all_children_validated}"
        })
        
        print(f"   ✓ Child validations checked: {len(child_validations)} tasks")
        print(f"   ✓ All children validated: {all_children_validated}")
        
        # Store child validation info
        validation_results["child_validations"] = child_validations
        
    except Exception as e:
        validation_results["integration_tests"].append({
            "name": "child_validations",
            "passed": False,
            "error": str(e)
        })
        print(f"   ✗ Error checking child validations: {e}")
    
    # Test 2: Engine initialization
    print("\n2. Testing analysis engine initialization...")
    try:
        engine = AnalysisEngine(analysis_config)
        init_valid = (
            engine is not None and
            hasattr(engine, 'config') and
            hasattr(engine, 'analysis_results') and
            engine.config == analysis_config
        )
        
        validation_results["integration_tests"].append({
            "name": "engine_initialization",
            "passed": init_valid,
            "details": f"Engine initialized successfully: {init_valid}"
        })
        
        print(f"   ✓ Engine initialized: {init_valid}")
        
    except Exception as e:
        validation_results["integration_tests"].append({
            "name": "engine_initialization",
            "passed": False,
            "error": str(e)
        })
        print(f"   ✗ Error: {e}")
        return validation_results
    
    # Test 3: Individual analysis execution
    print("\n3. Testing individual analysis execution...")
    try:
        # Test NQ EV Analysis (updated method name)
        ev_result = engine.run_nq_ev_analysis(data_config)
        ev_valid = (
            ev_result["status"] == "success" and
            "result" in ev_result and
            ev_result["result"]["quality_setups"] >= 0
        )
        
        # Test Momentum Analysis
        momentum_result = engine.run_momentum_analysis(data_config)
        momentum_valid = (
            momentum_result["status"] == "success" and
            "result" in momentum_result and
            momentum_result["result"]["momentum_contracts"] >= 0
        )
        
        # Test Volatility Analysis
        vol_result = engine.run_volatility_analysis(data_config)
        vol_valid = (
            vol_result["status"] == "success" and
            "result" in vol_result and
            vol_result["result"]["total_opportunities"] >= 0
        )
        
        individual_valid = ev_valid and momentum_valid and vol_valid
        
        validation_results["integration_tests"].append({
            "name": "individual_analyses",
            "passed": individual_valid,
            "details": {
                "nq_ev_analysis": ev_valid,
                "momentum_analysis": momentum_valid,
                "volatility_analysis": vol_valid
            }
        })
        
        print(f"   ✓ NQ EV Analysis: {ev_valid}")
        print(f"   ✓ Momentum Analysis: {momentum_valid}")
        print(f"   ✓ Volatility Analysis: {vol_valid}")
        
    except Exception as e:
        validation_results["integration_tests"].append({
            "name": "individual_analyses",
            "passed": False,
            "error": str(e)
        })
        print(f"   ✗ Error: {e}")
    
    # Test 4: Results synthesis
    print("\n4. Testing results synthesis...")
    try:
        # Ensure we have analysis results
        if not hasattr(engine, 'analysis_results') or not engine.analysis_results:
            # Run individual analyses to populate results (updated method names)
            engine.analysis_results = {
                "expected_value": engine.run_nq_ev_analysis(data_config),
                "momentum": engine.run_momentum_analysis(data_config),
                "volatility": engine.run_volatility_analysis(data_config)
            }
        
        synthesis = engine.synthesize_analysis_results()
        
        synthesis_valid = (
            isinstance(synthesis, dict) and
            "trading_recommendations" in synthesis and
            "market_context" in synthesis and
            "execution_priorities" in synthesis and
            len(synthesis["trading_recommendations"]) >= 0
        )
        
        validation_results["integration_tests"].append({
            "name": "results_synthesis",
            "passed": synthesis_valid,
            "details": {
                "trading_recommendations": len(synthesis["trading_recommendations"]),
                "primary_algorithm": synthesis.get("primary_algorithm"),
                "execution_priorities": len(synthesis["execution_priorities"])
            }
        })
        
        print(f"   ✓ Results synthesized: {synthesis_valid}")
        print(f"   ✓ Trading recommendations: {len(synthesis['trading_recommendations'])}")
        print(f"   ✓ Primary algorithm: {synthesis.get('primary_algorithm')}")
        
    except Exception as e:
        validation_results["integration_tests"].append({
            "name": "results_synthesis",
            "passed": False,
            "error": str(e)
        })
        print(f"   ✗ Error: {e}")
    
    # Test 5: Full analysis engine
    print("\n5. Testing full analysis engine...")
    try:
        # Use module-level function
        result = run_analysis_engine(data_config, analysis_config)
        
        full_analysis_valid = (
            result is not None and
            result["status"] == "success" and
            "individual_results" in result and
            "synthesis" in result and
            len(result["individual_results"]) == 3 and
            result["summary"]["successful_analyses"] >= 1
        )
        
        validation_results["integration_tests"].append({
            "name": "full_analysis_engine",
            "passed": full_analysis_valid,
            "details": {
                "status": result.get("status"),
                "successful_analyses": result.get("summary", {}).get("successful_analyses"),
                "primary_recommendations": result.get("summary", {}).get("primary_recommendations"),
                "execution_time": result.get("execution_time_seconds")
            }
        })
        
        print(f"   ✓ Full analysis complete: {full_analysis_valid}")
        print(f"   ✓ Successful analyses: {result['summary']['successful_analyses']}/3")
        print(f"   ✓ Primary recommendations: {result['summary']['primary_recommendations']}")
        print(f"   ✓ Execution time: {result['execution_time_seconds']:.2f}s")
        
        # Store evidence
        validation_results["evidence"]["full_analysis_result"] = {
            "status": result["status"],
            "execution_time": result["execution_time_seconds"],
            "successful_analyses": result["summary"]["successful_analyses"],
            "primary_recommendations": result["summary"]["primary_recommendations"],
            "primary_algorithm": result.get("primary_algorithm"),
            "best_nq_ev_trade": result["synthesis"]["trading_recommendations"][0] if result["synthesis"]["trading_recommendations"] else None
        }
        
    except Exception as e:
        validation_results["integration_tests"].append({
            "name": "full_analysis_engine",
            "passed": False,
            "error": str(e)
        })
        print(f"   ✗ Error: {e}")
    
    # Determine overall status
    all_passed = all(test['passed'] for test in validation_results['integration_tests'])
    validation_results['status'] = "VALIDATED" if all_passed else "FAILED"
    
    # Summary
    print("\n" + "-" * 50)
    print(f"VALIDATION COMPLETE: {validation_results['status']}")
    print(f"Tests passed: {sum(1 for t in validation_results['integration_tests'] if t['passed'])}/{len(validation_results['integration_tests'])}")
    
    return validation_results


# Removed duplicate save_evidence - now using canonical implementation from test_utils


if __name__ == "__main__":
    # Execute validation
    results = validate_analysis_engine()
    
    # Save evidence
    save_evidence(results)
    
    # Exit with appropriate code
    exit(0 if results['status'] == "VALIDATED" else 1)
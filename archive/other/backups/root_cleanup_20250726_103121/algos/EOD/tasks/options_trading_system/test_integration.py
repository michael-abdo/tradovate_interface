#!/usr/bin/env python3
"""
TASK: options_trading_system
TYPE: Root Task Integration Test
PURPOSE: Validate complete NQ Options Trading System orchestration
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from integration import NQOptionsTradingSystem, run_complete_nq_trading_system
from tasks.test_utils import save_evidence


def validate_options_trading_system():
    """
    Validate the complete options trading system integration functionality
    
    Returns:
        Dict with validation results and evidence
    """
    print("EXECUTING VALIDATION: options_trading_system (ROOT)")
    print("-" * 50)
    
    validation_results = {
        "task": "options_trading_system",
        "type": "root",
        "timestamp": datetime.now().isoformat(),
        "integration_tests": [],
        "status": "FAILED",
        "evidence": {}
    }
    
    # Test configuration
    master_config = {
        "data": {
            "barchart": {
                "file_path": os.path.join(project_root, "data/api_responses/options_data_20250602_141553.json")
            },
            "tradovate": {
                "mode": "demo",
                "cid": "6540",
                "secret": "f7a2b8f5-8348-424f-8ffa-047ab7502b7c",
                "use_mock": True
            }
        },
        "analysis": {
            "expected_value": {
                "weights": {
                    "oi_factor": 0.35,
                    "vol_factor": 0.25,
                    "pcr_factor": 0.25,
                    "distance_factor": 0.15
                },
                "min_ev": 15,
                "min_probability": 0.60,
                "max_risk": 150,
                "min_risk_reward": 1.0
            },
            "momentum": {
                "volume_threshold": 100,
                "price_change_threshold": 0.05,
                "momentum_window": 5,
                "min_momentum_score": 0.6
            },
            "volatility": {
                "iv_percentile_threshold": 75,
                "iv_skew_threshold": 0.05,
                "term_structure_slope_threshold": 0.02,
                "min_volume_for_iv": 10
            }
        },
        "output": {
            "report": {
                "style": "professional",
                "include_details": True,
                "include_market_context": True
            },
            "json": {
                "include_raw_data": False,
                "include_metadata": True,
                "format_pretty": True,
                "include_analysis_details": True
            }
        },
        "save": {
            "save_report": True,
            "save_json": True,
            "output_dir": "test_outputs",
            "timestamp_suffix": True
        }
    }
    
    # Test 1: Verify child task validations
    print("\n1. Checking child task validations...")
    try:
        child_validations = []
        
        # Check hierarchy.json for child validation status
        hierarchy_path = os.path.join(project_root, "coordination/hierarchy.json")
        if os.path.exists(hierarchy_path):
            with open(hierarchy_path, 'r') as f:
                hierarchy = json.load(f)
                
                # Check direct children: data_ingestion, analysis_engine, output_generation
                children = ["data_ingestion", "analysis_engine", "output_generation"]
                for child in children:
                    if child in hierarchy["hierarchy"]:
                        child_info = hierarchy["hierarchy"][child]
                        child_validations.append({
                            "task": child,
                            "status": child_info.get("status"),
                            "type": child_info.get("type"),
                            "evidence_path": child_info.get("evidence_path")
                        })
        
        all_children_validated = all(child["status"] == "validated" for child in child_validations)
        
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
    
    # Test 2: System initialization
    print("\n2. Testing NQ Options Trading System initialization...")
    try:
        system = NQOptionsTradingSystem(master_config)
        init_valid = (
            system is not None and
            hasattr(system, 'config') and
            hasattr(system, 'system_results') and
            hasattr(system, 'version') and
            system.config == master_config
        )
        
        validation_results["integration_tests"].append({
            "name": "system_initialization",
            "passed": init_valid,
            "details": f"System initialized successfully: {init_valid}"
        })
        
        print(f"   ✓ System initialized: {init_valid}")
        print(f"   ✓ System version: {system.version}")
        
    except Exception as e:
        validation_results["integration_tests"].append({
            "name": "system_initialization",
            "passed": False,
            "error": str(e)
        })
        print(f"   ✗ Error: {e}")
        return validation_results
    
    # Test 3: Configuration validation
    print("\n3. Testing configuration validation...")
    try:
        config_validation = system.validate_configuration()
        config_valid = (
            config_validation["status"] == "valid" and
            all(config_validation["checks"].values()) and
            len(config_validation["missing_sections"]) == 0
        )
        
        validation_results["integration_tests"].append({
            "name": "configuration_validation",
            "passed": config_valid,
            "details": {
                "status": config_validation["status"],
                "checks": config_validation["checks"],
                "missing_sections": config_validation["missing_sections"]
            }
        })
        
        print(f"   ✓ Configuration validation: {config_valid}")
        print(f"   ✓ All config sections present: {all(config_validation['checks'].values())}")
        
    except Exception as e:
        validation_results["integration_tests"].append({
            "name": "configuration_validation",
            "passed": False,
            "error": str(e)
        })
        print(f"   ✗ Error: {e}")
    
    # Test 4: Individual pipeline execution
    print("\n4. Testing individual pipeline execution...")
    try:
        # Test data pipeline
        data_result = system.run_data_pipeline()
        data_valid = (
            data_result["status"] == "success" and
            "result" in data_result and
            data_result["result"]["pipeline_status"] == "success"
        )
        
        # Test analysis pipeline (with data config from data pipeline result)
        if data_valid:
            analysis_result = system.run_analysis_pipeline(master_config["data"])
            analysis_valid = (
                analysis_result["status"] == "success" and
                "result" in analysis_result and
                analysis_result["result"]["status"] == "success"
            )
        else:
            analysis_valid = False
            analysis_result = {"status": "skipped", "reason": "data pipeline failed"}
        
        # Test output pipeline
        if data_valid:
            output_result = system.run_output_pipeline(master_config["data"])
            output_valid = (
                output_result["status"] == "success" and
                "result" in output_result and
                output_result["result"]["status"] == "success"
            )
        else:
            output_valid = False
            output_result = {"status": "skipped", "reason": "data pipeline failed"}
        
        pipeline_valid = data_valid and analysis_valid
        
        validation_results["integration_tests"].append({
            "name": "individual_pipelines",
            "passed": pipeline_valid,
            "details": {
                "data_pipeline": data_valid,
                "analysis_pipeline": analysis_valid,
                "output_pipeline": output_valid,
                "data_status": data_result.get("status"),
                "analysis_status": analysis_result.get("status"),
                "output_status": output_result.get("status")
            }
        })
        
        print(f"   ✓ Data Pipeline: {data_valid}")
        print(f"   ✓ Analysis Pipeline: {analysis_valid}")
        print(f"   ✓ Output Pipeline: {output_valid}")
        
        # Store pipeline results in system for next test
        system.system_results["data"] = data_result
        system.system_results["analysis"] = analysis_result
        system.system_results["output"] = output_result
        
    except Exception as e:
        validation_results["integration_tests"].append({
            "name": "individual_pipelines",
            "passed": False,
            "error": str(e)
        })
        print(f"   ✗ Error: {e}")
    
    # Test 5: System summary generation
    print("\n5. Testing system summary generation...")
    try:
        if hasattr(system, 'system_results') and system.system_results:
            summary = system.create_system_summary()
            
            summary_valid = (
                "timestamp" in summary and
                "system_version" in summary and
                "execution_status" in summary and
                "performance_metrics" in summary and
                "system_health" in summary and
                summary["system_health"]["status"] in ["excellent", "good", "degraded", "failed"]
            )
            
            validation_results["integration_tests"].append({
                "name": "system_summary",
                "passed": summary_valid,
                "details": {
                    "system_health": summary.get("system_health", {}).get("status"),
                    "successful_pipelines": summary.get("performance_metrics", {}).get("successful_pipelines"),
                    "has_trading_summary": "trading_summary" in summary,
                    "has_primary_recommendation": bool(summary.get("trading_summary", {}).get("primary_recommendation"))
                }
            })
            
            print(f"   ✓ System summary generated: {summary_valid}")
            print(f"   ✓ System health: {summary.get('system_health', {}).get('status', 'unknown')}")
            
        else:
            validation_results["integration_tests"].append({
                "name": "system_summary",
                "passed": False,
                "details": "No system results available for summary"
            })
            
    except Exception as e:
        validation_results["integration_tests"].append({
            "name": "system_summary",
            "passed": False,
            "error": str(e)
        })
        print(f"   ✗ Error: {e}")
    
    # Test 6: Complete system execution
    print("\n6. Testing complete system execution...")
    try:
        # Use module-level function
        result = run_complete_nq_trading_system(master_config)
        
        complete_system_valid = (
            result is not None and
            result["status"] == "success" and
            "config_validation" in result and
            "pipeline_results" in result and
            "system_summary" in result and
            result["config_validation"]["status"] == "valid" and
            result["system_summary"]["system_health"]["status"] in ["excellent", "good", "degraded"]
        )
        
        validation_results["integration_tests"].append({
            "name": "complete_system_execution",
            "passed": complete_system_valid,
            "details": {
                "status": result.get("status"),
                "execution_time": result.get("execution_time_seconds"),
                "system_health": result.get("system_summary", {}).get("system_health", {}).get("status"),
                "pipeline_success_rate": result.get("system_summary", {}).get("system_health", {}).get("pipeline_success_rate"),
                "has_trading_recommendation": bool(result.get("system_summary", {}).get("trading_summary", {}).get("primary_recommendation"))
            }
        })
        
        print(f"   ✓ Complete system execution: {complete_system_valid}")
        print(f"   ✓ Execution time: {result.get('execution_time_seconds', 0):.2f}s")
        print(f"   ✓ System health: {result.get('system_summary', {}).get('system_health', {}).get('status', 'unknown')}")
        
        # Store evidence
        validation_results["evidence"]["complete_system_result"] = {
            "status": result["status"],
            "execution_time": result["execution_time_seconds"],
            "system_version": result["system_version"],
            "system_health": result["system_summary"]["system_health"],
            "pipeline_success_rate": result["system_summary"]["system_health"]["pipeline_success_rate"],
            "trading_summary": result["system_summary"].get("trading_summary"),
            "config_validation": result["config_validation"]
        }
        
        # Clean up test files
        if result.get("pipeline_results", {}).get("output", {}).get("result", {}).get("save_results", {}).get("files_saved"):
            for file_info in result["pipeline_results"]["output"]["result"]["save_results"]["files_saved"]:
                if os.path.exists(file_info["filepath"]):
                    os.remove(file_info["filepath"])
        
        # Remove test output directory if empty
        if os.path.exists(master_config["save"]["output_dir"]) and not os.listdir(master_config["save"]["output_dir"]):
            os.rmdir(master_config["save"]["output_dir"])
        
    except Exception as e:
        validation_results["integration_tests"].append({
            "name": "complete_system_execution",
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
    results = validate_options_trading_system()
    
    # Save evidence
    save_evidence(results)
    
    # Exit with appropriate code
    exit(0 if results['status'] == "VALIDATED" else 1)
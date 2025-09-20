#!/usr/bin/env python3
"""
TASK: output_generation
TYPE: Parent Task Integration Test
PURPOSE: Validate that output generation coordinates all output formats correctly
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

from integration import OutputGenerationEngine, run_output_generation


def validate_output_generation():
    """
    Validate the output generation integration functionality
    
    Returns:
        Dict with validation results and evidence
    """
    print("EXECUTING VALIDATION: output_generation")
    print("-" * 50)
    
    validation_results = {
        "task": "output_generation",
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
    
    output_config = {
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
    }
    
    save_config = {
        "save_report": True,
        "save_json": True,
        "output_dir": "test_outputs",
        "timestamp_suffix": True
    }
    
    # Test 1: Verify child task validations
    print("\n1. Checking child task validations...")
    try:
        child_validations = []
        
        # Check report_generator evidence
        report_evidence_path = os.path.join(project_root, "tasks/options_trading_system/output_generation/report_generator/evidence.json")
        if os.path.exists(report_evidence_path):
            with open(report_evidence_path, 'r') as f:
                report_evidence = json.load(f)
                child_validations.append({
                    "task": "report_generator",
                    "status": report_evidence.get("status"),
                    "tests_passed": sum(1 for t in report_evidence.get("tests", []) if t.get("passed")),
                    "tests_total": len(report_evidence.get("tests", []))
                })
        
        # Check json_exporter evidence
        json_evidence_path = os.path.join(project_root, "tasks/options_trading_system/output_generation/json_exporter/evidence.json")
        if os.path.exists(json_evidence_path):
            with open(json_evidence_path, 'r') as f:
                json_evidence = json.load(f)
                child_validations.append({
                    "task": "json_exporter",
                    "status": json_evidence.get("status"),
                    "tests_passed": sum(1 for t in json_evidence.get("tests", []) if t.get("passed")),
                    "tests_total": len(json_evidence.get("tests", []))
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
    print("\n2. Testing output generation engine initialization...")
    try:
        engine = OutputGenerationEngine(output_config)
        init_valid = (
            engine is not None and
            hasattr(engine, 'config') and
            hasattr(engine, 'generation_results') and
            engine.config == output_config
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
    
    # Test 3: Individual output generation
    print("\n3. Testing individual output generation...")
    try:
        # Test Trading Report Generation
        report_result = engine.generate_trading_report(data_config)
        report_valid = (
            report_result["status"] == "success" and
            "result" in report_result and
            len(report_result["result"]["report_text"]) > 1000
        )
        
        # Test JSON Export Generation
        json_result = engine.generate_json_export(data_config)
        json_valid = (
            json_result["status"] == "success" and
            "result" in json_result and
            json_result["result"]["metadata"]["json_size_bytes"] > 1000
        )
        
        individual_valid = report_valid and json_valid
        
        validation_results["integration_tests"].append({
            "name": "individual_generation",
            "passed": individual_valid,
            "details": {
                "report_generation": report_valid,
                "json_generation": json_valid,
                "report_length": len(report_result["result"]["report_text"]) if report_valid else 0,
                "json_size": json_result["result"]["metadata"]["json_size_bytes"] if json_valid else 0
            }
        })
        
        print(f"   ✓ Report Generation: {report_valid}")
        print(f"   ✓ JSON Generation: {json_valid}")
        
        # Store generation results in engine for next test
        engine.generation_results["report"] = report_result
        engine.generation_results["json"] = json_result
        
    except Exception as e:
        validation_results["integration_tests"].append({
            "name": "individual_generation",
            "passed": False,
            "error": str(e)
        })
        print(f"   ✗ Error: {e}")
    
    # Test 4: File saving
    print("\n4. Testing file saving...")
    try:
        if hasattr(engine, 'generation_results') and engine.generation_results:
            save_results = engine.save_outputs(save_config)
            
            save_valid = (
                isinstance(save_results, dict) and
                save_results["total_files"] >= 0 and
                len(save_results["errors"]) == 0 and
                save_results["total_size_bytes"] > 0
            )
            
            validation_results["integration_tests"].append({
                "name": "file_saving",
                "passed": save_valid,
                "details": {
                    "files_saved": save_results["total_files"],
                    "total_size": save_results["total_size_bytes"],
                    "errors": save_results["errors"],
                    "saved_files": [f["filename"] for f in save_results["files_saved"]]
                }
            })
            
            print(f"   ✓ File saving: {save_valid}")
            print(f"   ✓ Files saved: {save_results['total_files']}")
            print(f"   ✓ Total size: {save_results['total_size_bytes']} bytes")
            
            # Clean up test files
            for file_info in save_results["files_saved"]:
                if os.path.exists(file_info["filepath"]):
                    os.remove(file_info["filepath"])
            
            # Remove test output directory if empty
            if os.path.exists(save_config["output_dir"]) and not os.listdir(save_config["output_dir"]):
                os.rmdir(save_config["output_dir"])
                
        else:
            validation_results["integration_tests"].append({
                "name": "file_saving",
                "passed": False,
                "details": "No generation results available for saving"
            })
            
    except Exception as e:
        validation_results["integration_tests"].append({
            "name": "file_saving",
            "passed": False,
            "error": str(e)
        })
        print(f"   ✗ Error: {e}")
    
    # Test 5: Full output generation engine
    print("\n5. Testing full output generation engine...")
    try:
        # Use module-level function
        result = run_output_generation(data_config, output_config, save_config)
        
        full_generation_valid = (
            result is not None and
            result["status"] == "success" and
            "generation_results" in result and
            "save_results" in result and
            "output_summary" in result and
            result["summary"]["successful_generations"] >= 1
        )
        
        validation_results["integration_tests"].append({
            "name": "full_output_generation",
            "passed": full_generation_valid,
            "details": {
                "status": result.get("status"),
                "successful_generations": result.get("summary", {}).get("successful_generations"),
                "files_saved": result.get("summary", {}).get("files_saved"),
                "total_output_size": result.get("summary", {}).get("total_output_size"),
                "execution_time": result.get("execution_time_seconds")
            }
        })
        
        print(f"   ✓ Full generation complete: {full_generation_valid}")
        print(f"   ✓ Successful generations: {result['summary']['successful_generations']}/2")
        print(f"   ✓ Files saved: {result['summary']['files_saved']}")
        print(f"   ✓ Total output size: {result['summary']['total_output_size']} bytes")
        print(f"   ✓ Execution time: {result['execution_time_seconds']:.2f}s")
        
        # Store evidence
        validation_results["evidence"]["full_generation_result"] = {
            "status": result["status"],
            "execution_time": result["execution_time_seconds"],
            "successful_generations": result["summary"]["successful_generations"],
            "files_saved": result["summary"]["files_saved"],
            "total_output_size": result["summary"]["total_output_size"],
            "recommended_action": result["summary"]["recommended_action"],
            "output_summary": result["output_summary"]
        }
        
        # Clean up test files
        if result.get("save_results", {}).get("files_saved"):
            for file_info in result["save_results"]["files_saved"]:
                if os.path.exists(file_info["filepath"]):
                    os.remove(file_info["filepath"])
        
        # Remove test output directory if empty
        if os.path.exists(save_config["output_dir"]) and not os.listdir(save_config["output_dir"]):
            os.rmdir(save_config["output_dir"])
        
    except Exception as e:
        validation_results["integration_tests"].append({
            "name": "full_output_generation",
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
    results = validate_output_generation()
    
    # Save evidence
    save_evidence(results)
    
    # Exit with appropriate code
    exit(0 if results['status'] == "VALIDATED" else 1)
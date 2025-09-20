#!/usr/bin/env python3
"""
TASK: json_exporter
TYPE: Validation Test
PURPOSE: Validate that JSON export functionality works correctly
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from tasks.test_utils import save_evidence
from tasks.common_utils import add_validation_error
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

from solution import JSONExporter, export_analysis_json


def validate_json_exporter():
    """
    Validate the JSON exporter functionality
    
    Returns:
        Dict with validation results and evidence
    """
    print("EXECUTING VALIDATION: json_exporter")
    print("-" * 50)
    
    validation_results = {
        "task": "json_exporter",
        "timestamp": datetime.now().isoformat(),
        "tests": [],
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
    
    export_config = {
        "include_raw_data": False,
        "include_metadata": True,
        "format_pretty": True,
        "include_analysis_details": True
    }
    
    # Test 1: Initialize JSON exporter
    print("\n1. Testing JSON exporter initialization...")
    try:
        exporter = JSONExporter(export_config)
        init_valid = (
            exporter is not None and
            hasattr(exporter, 'include_raw_data') and
            hasattr(exporter, 'format_pretty') and
            exporter.format_pretty == True
        )
        
        validation_results["tests"].append({
            "name": "exporter_init",
            "passed": init_valid,
            "details": {
                "include_raw_data": exporter.include_raw_data,
                "include_metadata": exporter.include_metadata,
                "format_pretty": exporter.format_pretty,
                "include_analysis_details": exporter.include_analysis_details
            }
        })
        print(f"   ✓ Exporter initialized: {init_valid}")
        print(f"   ✓ Pretty format: {exporter.format_pretty}")
        
    except Exception as e:
        add_validation_error(validation_results, "exporter_init", e)
        return validation_results
    
    # Test 2: Data cleaning and serialization
    print("\n2. Testing data cleaning and serialization...")
    try:
        # Test with various data types
        test_data = {
            "string": "test",
            "number": 123.45,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "nested_dict": {"a": 1, "b": 2}
        }
        
        cleaned_data = exporter.clean_analysis_data(test_data)
        
        # Test JSON serialization
        json_string = json.dumps(cleaned_data)
        parsed_back = json.loads(json_string)
        
        serialization_valid = (
            isinstance(cleaned_data, dict) and
            len(json_string) > 10 and
            parsed_back == cleaned_data
        )
        
        validation_results["tests"].append({
            "name": "data_serialization",
            "passed": serialization_valid,
            "details": {
                "original_keys": list(test_data.keys()),
                "cleaned_keys": list(cleaned_data.keys()),
                "json_length": len(json_string),
                "round_trip_success": parsed_back == cleaned_data
            }
        })
        
        print(f"   ✓ Data serialization: {serialization_valid}")
        print(f"   ✓ JSON length: {len(json_string)} chars")
        
    except Exception as e:
        add_validation_error(validation_results, "data_serialization", e)
    
    # Test 3: Export complete JSON using integration function
    print("\n3. Testing complete JSON export...")
    try:
        export_result = export_analysis_json(data_config, export_config)
        
        export_valid = (
            isinstance(export_result, dict) and
            "json_data" in export_result and
            "json_string" in export_result and
            "metadata" in export_result and
            len(export_result["json_string"]) > 100
        )
        
        # Check JSON structure
        json_data = export_result["json_data"]
        structure_checks = {
            "has_metadata": "metadata" in json_data,
            "has_trading_signals": "trading_signals" in json_data,
            "has_market_analysis": "market_analysis" in json_data,
            "has_execution_summary": "execution_summary" in json_data,
            "signals_is_list": isinstance(json_data.get("trading_signals"), list),
            "market_analysis_is_dict": isinstance(json_data.get("market_analysis"), dict)
        }
        
        structure_valid = all(structure_checks.values())
        
        validation_results["tests"].append({
            "name": "complete_json_export",
            "passed": export_valid and structure_valid,
            "details": {
                "export_structure_valid": export_valid,
                "json_structure_checks": structure_checks,
                "json_size": len(export_result["json_string"]),
                "signals_count": len(json_data.get("trading_signals", [])),
                "metadata": export_result["metadata"]
            }
        })
        
        print(f"   ✓ Complete JSON export: {export_valid and structure_valid}")
        print(f"   ✓ JSON size: {len(export_result['json_string'])} chars")
        print(f"   ✓ Trading signals: {len(json_data.get('trading_signals', []))}")
        
        # Store evidence
        validation_results["evidence"]["export_sample"] = {
            "json_size": len(export_result["json_string"]),
            "signals_count": len(json_data.get("trading_signals", [])),
            "structure_checks": structure_checks,
            "metadata": export_result["metadata"],
            "recommended_action": json_data.get("execution_summary", {}).get("recommended_action"),
            "sample_signal": json_data.get("trading_signals", [{}])[0] if json_data.get("trading_signals") else {}
        }
        
    except Exception as e:
        add_validation_error(validation_results, "complete_json_export", e)
    
    # Test 4: Trading signals extraction
    print("\n4. Testing trading signals extraction...")
    try:
        if 'export_result' in locals():
            json_data = export_result["json_data"]
            trading_signals = json_data.get("trading_signals", [])
            
            # Check signal structure
            if trading_signals:
                signal = trading_signals[0]
                signal_checks = {
                    "has_signal_id": "signal_id" in signal,
                    "has_timestamp": "timestamp" in signal,
                    "has_trade_data": "trade" in signal,
                    "has_direction": signal.get("trade", {}).get("direction") is not None,
                    "has_prices": all(key in signal.get("trade", {}) for key in ["entry_price", "target_price", "stop_price"]),
                    "has_expected_value": "expected_value" in signal.get("trade", {}),
                    "has_probability": "win_probability" in signal.get("trade", {})
                }
                
                signals_valid = all(signal_checks.values())
            else:
                signals_valid = True  # No signals is valid if no quality setups
                signal_checks = {"no_signals_found": True}
            
            validation_results["tests"].append({
                "name": "trading_signals_extraction",
                "passed": signals_valid,
                "details": {
                    "signals_count": len(trading_signals),
                    "signal_structure_checks": signal_checks,
                    "sample_signal_keys": list(trading_signals[0].keys()) if trading_signals else []
                }
            })
            
            print(f"   ✓ Trading signals extraction: {signals_valid}")
            print(f"   ✓ Signals extracted: {len(trading_signals)}")
        else:
            validation_results["tests"].append({
                "name": "trading_signals_extraction",
                "passed": False,
                "details": "No export result available"
            })
            
    except Exception as e:
        add_validation_error(validation_results, "trading_signals_extraction", e)
    
    # Test 5: JSON file saving
    print("\n5. Testing JSON file saving...")
    try:
        if 'export_result' in locals():
            # Save JSON to file
            json_filename = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            json_path = os.path.join(os.path.dirname(__file__), json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(export_result["json_string"])
            
            # Verify file was created and has valid JSON
            file_exists = os.path.exists(json_path)
            file_size = os.path.getsize(json_path) if file_exists else 0
            
            # Test loading the saved JSON
            if file_exists:
                with open(json_path, 'r', encoding='utf-8') as f:
                    loaded_json = json.load(f)
                json_valid = isinstance(loaded_json, dict)
            else:
                json_valid = False
            
            save_valid = file_exists and file_size > 100 and json_valid
            
            validation_results["tests"].append({
                "name": "json_file_saving",
                "passed": save_valid,
                "details": {
                    "file_created": file_exists,
                    "file_size": file_size,
                    "json_valid": json_valid,
                    "file_path": json_path
                }
            })
            
            print(f"   ✓ JSON file saving: {save_valid}")
            print(f"   ✓ File size: {file_size} bytes")
            print(f"   ✓ Saved to: {json_filename}")
            
            # Clean up test file
            if file_exists:
                os.remove(json_path)
        else:
            validation_results["tests"].append({
                "name": "json_file_saving",
                "passed": False,
                "details": "No export result available for file saving"
            })
            
    except Exception as e:
        add_validation_error(validation_results, "json_file_saving", e)
    
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
    results = validate_json_exporter()
    
    # Save evidence
    save_evidence(results)
    
    # Exit with appropriate code
    exit(0 if results['status'] == "VALIDATED" else 1)
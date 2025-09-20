#!/usr/bin/env python3
"""
TASK: report_generator
TYPE: Validation Test
PURPOSE: Validate that trading report generation works correctly
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

from solution import TradingReportGenerator, generate_trading_report


def validate_report_generator():
    """
    Validate the trading report generator functionality
    
    Returns:
        Dict with validation results and evidence
    """
    print("EXECUTING VALIDATION: report_generator")
    print("-" * 50)
    
    validation_results = {
        "task": "report_generator",
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
    
    report_config = {
        "style": "professional",
        "include_details": True,
        "include_market_context": True
    }
    
    # Test 1: Initialize report generator
    print("\n1. Testing report generator initialization...")
    try:
        generator = TradingReportGenerator(report_config)
        init_valid = (
            generator is not None and
            hasattr(generator, 'report_style') and
            hasattr(generator, 'include_details') and
            generator.report_style == "professional"
        )
        
        validation_results["tests"].append({
            "name": "generator_init",
            "passed": init_valid,
            "details": {
                "report_style": generator.report_style,
                "include_details": generator.include_details,
                "include_market_context": generator.include_market_context
            }
        })
        print(f"   ✓ Generator initialized: {init_valid}")
        print(f"   ✓ Report style: {generator.report_style}")
        
    except Exception as e:
        add_validation_error(validation_results, "generator_init", e)
        return validation_results
    
    # Test 2: Generate report sections
    print("\n2. Testing report section generation...")
    try:
        # Mock analysis results for testing
        mock_analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": 1.5,
            "primary_algorithm": "nq_ev_analysis",
            "summary": {"successful_analyses": 3, "primary_recommendations": 1},
            "synthesis": {
                "trading_recommendations": [{
                    "trade_direction": "SHORT",
                    "entry_price": 21376.75,
                    "target": 14000.0,
                    "stop": 21380.0,
                    "expected_value": 5964.4,
                    "probability": 0.809,
                    "position_size": "LARGE (15-20%)",
                    "confidence": "HIGH"
                }],
                "market_context": {
                    "nq_price": 21376.75,
                    "quality_setups": 7678,
                    "momentum_sentiment": "neutral",
                    "iv_regime": "low"
                },
                "execution_priorities": []
            }
        }
        
        # Test header generation
        header = generator.generate_header(mock_analysis_results)
        header_valid = (
            isinstance(header, str) and
            "NQ OPTIONS TRADING SYSTEM" in header and
            "ANALYSIS REPORT" in header and
            len(header) > 100
        )
        
        # Test executive summary
        summary = generator.generate_executive_summary(mock_analysis_results)
        summary_valid = (
            isinstance(summary, str) and
            "EXECUTIVE SUMMARY" in summary and
            "PRIMARY RECOMMENDATION" in summary and
            len(summary) > 50
        )
        
        sections_valid = header_valid and summary_valid
        
        validation_results["tests"].append({
            "name": "section_generation",
            "passed": sections_valid,
            "details": {
                "header_valid": header_valid,
                "summary_valid": summary_valid,
                "header_length": len(header),
                "summary_length": len(summary)
            }
        })
        
        print(f"   ✓ Section generation: {sections_valid}")
        print(f"   ✓ Header length: {len(header)} chars")
        print(f"   ✓ Summary length: {len(summary)} chars")
        
    except Exception as e:
        add_validation_error(validation_results, "section_generation", e)
    
    # Test 3: Generate complete report using integration function
    print("\n3. Testing complete report generation...")
    try:
        report_result = generate_trading_report(data_config, report_config)
        
        report_valid = (
            isinstance(report_result, dict) and
            "report_text" in report_result and
            "analysis_results" in report_result and
            "metadata" in report_result and
            len(report_result["report_text"]) > 1000
        )
        
        # Check report content
        report_text = report_result["report_text"]
        content_checks = {
            "has_header": "NQ OPTIONS TRADING SYSTEM" in report_text,
            "has_executive_summary": "EXECUTIVE SUMMARY" in report_text,
            "has_nq_ev_section": "NQ OPTIONS EV ANALYSIS" in report_text,
            "has_execution_priorities": "EXECUTION PRIORITIES" in report_text,
            "has_footer": "RISK DISCLAIMER" in report_text
        }
        
        content_valid = all(content_checks.values())
        
        validation_results["tests"].append({
            "name": "complete_report_generation",
            "passed": report_valid and content_valid,
            "details": {
                "report_structure_valid": report_valid,
                "content_checks": content_checks,
                "report_length": len(report_text),
                "metadata": report_result["metadata"]
            }
        })
        
        print(f"   ✓ Complete report generation: {report_valid and content_valid}")
        print(f"   ✓ Report length: {len(report_text)} chars")
        print(f"   ✓ Sections included: {report_result['metadata']['sections_included']}")
        
        # Store evidence
        validation_results["evidence"]["sample_report"] = {
            "report_length": len(report_text),
            "sections_included": report_result["metadata"]["sections_included"],
            "content_checks": content_checks,
            "first_100_chars": report_text[:100],
            "analysis_summary": {
                "successful_analyses": report_result["analysis_results"]["summary"]["successful_analyses"],
                "primary_recommendations": report_result["analysis_results"]["summary"]["primary_recommendations"],
                "execution_time": report_result["analysis_results"]["execution_time_seconds"]
            }
        }
        
    except Exception as e:
        add_validation_error(validation_results, "complete_report_generation", e)
    
    # Test 4: Report formatting and structure
    print("\n4. Testing report formatting...")
    try:
        if 'report_result' in locals():
            report_text = report_result["report_text"]
            
            # Check formatting elements
            format_checks = {
                "has_section_dividers": "-" * 50 in report_text,
                "has_headers": "=" * 80 in report_text,
                "has_bullet_points": "•" in report_text or "→" in report_text,
                "has_emojis": any(emoji in report_text for emoji in ["📊", "🎯", "💡", "⚡"]),
                "proper_line_breaks": "\n\n" in report_text
            }
            
            formatting_valid = sum(format_checks.values()) >= 3  # At least 3 formatting elements
            
            validation_results["tests"].append({
                "name": "report_formatting",
                "passed": formatting_valid,
                "details": {
                    "format_checks": format_checks,
                    "formatting_score": f"{sum(format_checks.values())}/5"
                }
            })
            
            print(f"   ✓ Report formatting: {formatting_valid}")
            print(f"   ✓ Formatting score: {sum(format_checks.values())}/5")
        else:
            validation_results["tests"].append({
                "name": "report_formatting",
                "passed": False,
                "details": "No report available for formatting check"
            })
            
    except Exception as e:
        add_validation_error(validation_results, "report_formatting", e)
    
    # Test 5: Save report to file
    print("\n5. Testing report file saving...")
    try:
        if 'report_result' in locals():
            # Save report to file
            report_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            report_path = os.path.join(os.path.dirname(__file__), report_filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_result["report_text"])
            
            # Verify file was created and has content
            file_exists = os.path.exists(report_path)
            file_size = os.path.getsize(report_path) if file_exists else 0
            
            save_valid = file_exists and file_size > 1000
            
            validation_results["tests"].append({
                "name": "report_file_saving",
                "passed": save_valid,
                "details": {
                    "file_created": file_exists,
                    "file_size": file_size,
                    "file_path": report_path
                }
            })
            
            print(f"   ✓ Report file saving: {save_valid}")
            print(f"   ✓ File size: {file_size} bytes")
            print(f"   ✓ Saved to: {report_filename}")
            
            # Clean up test file
            if file_exists:
                os.remove(report_path)
        else:
            validation_results["tests"].append({
                "name": "report_file_saving",
                "passed": False,
                "details": "No report available for file saving"
            })
            
    except Exception as e:
        add_validation_error(validation_results, "report_file_saving", e)
    
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
    results = validate_report_generator()
    
    # Save evidence
    save_evidence(results)
    
    # Exit with appropriate code
    exit(0 if results['status'] == "VALIDATED" else 1)
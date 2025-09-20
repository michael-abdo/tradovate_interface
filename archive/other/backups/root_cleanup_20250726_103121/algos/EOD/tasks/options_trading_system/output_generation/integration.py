#!/usr/bin/env python3
"""
TASK: output_generation
TYPE: Parent Task Integration
PURPOSE: Coordinate all output generation methods (reports and JSON exports)
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add tasks directory to path for common utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common_utils import PathManager

# Add current directory to path for child task imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import child task modules
from report_generator.solution import generate_trading_report
from json_exporter.solution import export_analysis_json


class OutputGenerationEngine:
    """Unified output generation engine coordinating reports and JSON exports"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the output generation engine
        
        Args:
            config: Configuration containing output settings for each format
        """
        self.config = config
        self.generation_results = {}
        
    def generate_trading_report(self, data_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate human-readable trading report"""
        print("  Generating Trading Report...")
        
        report_config = self.config.get("report", {
            "style": "professional",
            "include_details": True,
            "include_market_context": True
        })
        
        analysis_config = self.config.get("analysis", None)
        
        try:
            result = generate_trading_report(data_config, report_config, analysis_config)
            report_text = result["report_text"]
            
            print(f"    ✓ Trading Report: {len(report_text)} characters generated")
            print(f"    ✓ Sections: {result['metadata']['sections_included']}")
            
            return {
                "status": "success",
                "result": result,
                "timestamp": get_utc_timestamp()
            }
        except Exception as e:
            print(f"    ✗ Trading Report failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": get_utc_timestamp()
            }
    
    def generate_json_export(self, data_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured JSON export"""
        print("  Generating JSON Export...")
        
        export_config = self.config.get("json", {
            "include_raw_data": False,
            "include_metadata": True,
            "format_pretty": True,
            "include_analysis_details": True
        })
        
        analysis_config = self.config.get("analysis", None)
        
        try:
            result = export_analysis_json(data_config, export_config, analysis_config)
            json_size = result["metadata"]["json_size_bytes"]
            signals_count = result["metadata"]["total_signals"]
            
            print(f"    ✓ JSON Export: {json_size} bytes generated")
            print(f"    ✓ Trading Signals: {signals_count}")
            print(f"    ✓ Recommended Action: {result['metadata']['recommended_action']}")
            
            return {
                "status": "success",
                "result": result,
                "timestamp": get_utc_timestamp()
            }
        except Exception as e:
            print(f"    ✗ JSON Export failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": get_utc_timestamp()
            }
    
    def save_outputs(self, save_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save generated outputs to files"""
        print("  Saving Outputs to Files...")
        
        if save_config is None:
            save_config = {
                "save_report": True,
                "save_json": True,
                "output_dir": "outputs",
                "timestamp_suffix": True
            }
        
        save_results = {
            "files_saved": [],
            "errors": [],
            "total_files": 0,
            "total_size_bytes": 0
        }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        date_str = datetime.now().strftime('%Y%m%d')
        base_output_dir = save_config.get("output_dir", "outputs")
        
        # Create organized output directories
        output_dir = base_output_dir  # For backwards compatibility
        reports_dir = os.path.join(base_output_dir, date_str, "reports")
        exports_dir = os.path.join(base_output_dir, date_str, "analysis_exports")
        
        os.makedirs(reports_dir, exist_ok=True)
        os.makedirs(exports_dir, exist_ok=True)
        
        # Save trading report
        if save_config.get("save_report", True) and "report" in self.generation_results:
            report_result = self.generation_results["report"]
            if report_result["status"] == "success":
                try:
                    if save_config.get("timestamp_suffix", True):
                        filename = f"nq_trading_report_{timestamp}.txt"
                    else:
                        filename = "nq_trading_report.txt"
                    
                    filepath = os.path.join(reports_dir, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(report_result["result"]["report_text"])
                    
                    file_size = os.path.getsize(filepath)
                    save_results["files_saved"].append({
                        "type": "trading_report",
                        "filename": filename,
                        "filepath": filepath,
                        "size_bytes": file_size
                    })
                    save_results["total_size_bytes"] += file_size
                    
                    print(f"    ✓ Report saved: {filename} ({file_size} bytes)")
                    
                except Exception as e:
                    save_results["errors"].append(f"Failed to save report: {str(e)}")
                    print(f"    ✗ Report save failed: {str(e)}")
        
        # Save JSON export
        if save_config.get("save_json", True) and "json" in self.generation_results:
            json_result = self.generation_results["json"]
            if json_result["status"] == "success":
                try:
                    if save_config.get("timestamp_suffix", True):
                        filename = f"nq_analysis_export_{timestamp}.json"
                    else:
                        filename = "nq_analysis_export.json"
                    
                    filepath = os.path.join(exports_dir, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(json_result["result"]["json_string"])
                    
                    file_size = os.path.getsize(filepath)
                    save_results["files_saved"].append({
                        "type": "json_export",
                        "filename": filename,
                        "filepath": filepath,
                        "size_bytes": file_size
                    })
                    save_results["total_size_bytes"] += file_size
                    
                    print(f"    ✓ JSON saved: {filename} ({file_size} bytes)")
                    
                except Exception as e:
                    save_results["errors"].append(f"Failed to save JSON: {str(e)}")
                    print(f"    ✗ JSON save failed: {str(e)}")
        
        save_results["total_files"] = len(save_results["files_saved"])
        return save_results
    
    def create_output_summary(self) -> Dict[str, Any]:
        """Create a summary of all generated outputs"""
        
        summary = {
            "timestamp": get_utc_timestamp(),
            "generation_status": {
                "report": self.generation_results.get("report", {}).get("status", "not_attempted"),
                "json": self.generation_results.get("json", {}).get("status", "not_attempted")
            },
            "content_summary": {},
            "recommendations": []
        }
        
        # Extract content summaries
        if "report" in self.generation_results and self.generation_results["report"]["status"] == "success":
            report_data = self.generation_results["report"]["result"]
            summary["content_summary"]["report"] = {
                "length_chars": report_data["metadata"]["total_length"],
                "sections": report_data["metadata"]["sections_included"],
                "style": report_data["metadata"]["report_style"]
            }
        
        if "json" in self.generation_results and self.generation_results["json"]["status"] == "success":
            json_data = self.generation_results["json"]["result"]
            summary["content_summary"]["json"] = {
                "size_bytes": json_data["metadata"]["json_size_bytes"],
                "signals_count": json_data["metadata"]["total_signals"],
                "recommended_action": json_data["metadata"]["recommended_action"]
            }
            
            # Extract key recommendations
            if json_data["json_data"]["trading_signals"]:
                primary_signal = json_data["json_data"]["trading_signals"][0]
                summary["recommendations"].append({
                    "priority": primary_signal.get("priority", "UNKNOWN"),
                    "direction": primary_signal["trade"]["direction"],
                    "expected_value": primary_signal["trade"]["expected_value"],
                    "confidence": primary_signal.get("confidence", "UNKNOWN")
                })
        
        return summary
    
    def run_full_output_generation(self, data_config: Dict[str, Any], 
                                  save_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run complete output generation with all formats"""
        print("EXECUTING OUTPUT GENERATION ENGINE")
        print("-" * 40)
        
        start_time = datetime.now()
        
        # Generate both output formats in parallel
        print("  Generating all outputs simultaneously...")
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both generation tasks concurrently
            futures = {
                executor.submit(self.generate_trading_report, data_config): "report",
                executor.submit(self.generate_json_export, data_config): "json"
            }
            
            # Collect results as they complete
            for future in as_completed(futures):
                output_type = futures[future]
                try:
                    self.generation_results[output_type] = future.result()
                    if self.generation_results[output_type]["status"] == "success":
                        print(f"    ✓ {output_type.title()} generation completed")
                except Exception as e:
                    print(f"    ✗ {output_type} generation failed: {str(e)}")
                    self.generation_results[output_type] = {
                        "status": "failed",
                        "error": str(e),
                        "timestamp": get_utc_timestamp()
                    }
        
        # Save outputs to files
        save_results = self.save_outputs(save_config)
        
        # Create output summary
        output_summary = self.create_output_summary()
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Final results
        final_results = {
            "timestamp": get_utc_timestamp(),
            "execution_time_seconds": execution_time,
            "output_config": self.config,
            "generation_results": self.generation_results,
            "save_results": save_results,
            "output_summary": output_summary,
            "status": "success",
            "summary": {
                "successful_generations": len([r for r in self.generation_results.values() if r["status"] == "success"]),
                "files_saved": save_results["total_files"],
                "total_output_size": save_results["total_size_bytes"],
                "recommended_action": output_summary.get("content_summary", {}).get("json", {}).get("recommended_action", "unknown")
            }
        }
        
        print(f"\nOUTPUT GENERATION COMPLETE")
        print(f"✓ Execution time: {execution_time:.2f}s")
        print(f"✓ Successful generations: {final_results['summary']['successful_generations']}/2")
        print(f"✓ Files saved: {final_results['summary']['files_saved']}")
        print(f"✓ Total output size: {final_results['summary']['total_output_size']} bytes")
        
        return final_results


# Module-level function for easy integration
def run_output_generation(data_config: Dict[str, Any], 
                         output_config: Dict[str, Any] = None,
                         save_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Run the complete output generation engine
    
    Args:
        data_config: Configuration for data sources
        output_config: Configuration for output generation (optional)
        save_config: Configuration for file saving (optional)
        
    Returns:
        Dict with comprehensive output generation results
    """
    if output_config is None:
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
            }
        }
    
    engine = OutputGenerationEngine(output_config)
    return engine.run_full_output_generation(data_config, save_config)
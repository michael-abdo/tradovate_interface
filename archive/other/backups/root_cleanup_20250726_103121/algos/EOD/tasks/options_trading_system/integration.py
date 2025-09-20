#!/usr/bin/env python3
"""
TASK: options_trading_system
TYPE: Root Task Integration
PURPOSE: Complete NQ Options Trading System orchestrating all components
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List

# Add current directory to path for child task imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Add tasks directory to path for common utilities
sys.path.insert(0, os.path.dirname(current_dir))
from common_utils import get_utc_timestamp, PathManager, create_success_response, create_failure_response, create_status_response

# Import parent task modules
from data_ingestion.integration import run_data_ingestion
from analysis_engine.integration import run_analysis_engine
from output_generation.integration import run_output_generation


class NQOptionsTradingSystem:
    """Complete NQ Options Trading System with your actual EV algorithm"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the complete trading system
        
        Args:
            config: Master configuration for all system components
        """
        self.config = config
        self.system_results = {}
        self.version = "1.0"
        
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate system configuration"""
        print("  Validating System Configuration...")
        
        validation = {
            "data_config_valid": "data" in self.config,
            "analysis_config_valid": "analysis" in self.config,
            "output_config_valid": "output" in self.config,
            "save_config_valid": "save" in self.config,
        }
        
        all_valid = all(validation.values())
        
        print(f"    ✓ Configuration validation: {all_valid}")
        
        return create_status_response(
            status="valid" if all_valid else "invalid",
            checks=validation,
            missing_sections=[k.replace("_config_valid", "") for k, v in validation.items() if not v]
        )
    
    def run_data_pipeline(self) -> Dict[str, Any]:
        """Execute data ingestion pipeline"""
        print("  Running Data Pipeline...")
        
        data_config = self.config.get("data", {})
        
        try:
            result = run_data_ingestion(data_config)
            
            print(f"    ✓ Data Pipeline: {result['pipeline_status']}")
            print(f"    ✓ Total Contracts: {result['summary']['total_contracts']}")
            print(f"    ✓ Data Quality: {result['quality_metrics']['overall_volume_coverage']:.1%} volume coverage")
            
            return create_success_response(result=result)
        except Exception as e:
            print(f"    ✗ Data Pipeline failed: {str(e)}")
            return create_failure_response(e)
    
    def run_analysis_pipeline(self, data_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis engine with your NQ EV algorithm"""
        print("  Running Analysis Pipeline (NQ EV Algorithm Primary)...")
        
        analysis_config = self.config.get("analysis", {})
        
        try:
            result = run_analysis_engine(data_config, analysis_config)
            
            print(f"    ✓ Analysis Pipeline: {result['status']}")
            print(f"    ✓ Successful Analyses: {result['summary']['successful_analyses']}/2")
            print(f"    ✓ Primary Algorithm: {result['primary_algorithm']}")
            
            # Show best NQ EV trade
            if result.get("synthesis", {}).get("trading_recommendations"):
                best_rec = result["synthesis"]["trading_recommendations"][0]
                print(f"    ✓ Best NQ EV Trade: {best_rec['trade_direction']} EV={best_rec['expected_value']:+.1f} points")
            
            return create_success_response(result=result)
        except Exception as e:
            print(f"    ✗ Analysis Pipeline failed: {str(e)}")
            return create_failure_response(e)
    
    def run_output_pipeline(self, data_config: Dict[str, Any], analysis_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute output generation pipeline"""
        print("  Running Output Pipeline...")
        
        output_config = self.config.get("output", {})
        save_config = self.config.get("save", {})
        
        # Pass cached analysis results if available
        if analysis_results:
            data_config = {**data_config, "_cached_analysis_results": analysis_results}
        
        try:
            result = run_output_generation(data_config, output_config, save_config)
            
            print(f"    ✓ Output Pipeline: {result['status']}")
            print(f"    ✓ Successful Generations: {result['summary']['successful_generations']}/2")
            print(f"    ✓ Files Saved: {result['summary']['files_saved']}")
            print(f"    ✓ Total Output Size: {result['summary']['total_output_size']} bytes")
            
            return create_success_response(result=result)
        except Exception as e:
            print(f"    ✗ Output Pipeline failed: {str(e)}")
            return create_failure_response(e)
    
    def create_system_summary(self) -> Dict[str, Any]:
        """Create comprehensive system execution summary"""
        
        summary = {
            "timestamp": get_utc_timestamp(),
            "system_version": self.version,
            "execution_status": {
                "data": self.system_results.get("data", {}).get("status", "not_attempted"),
                "analysis": self.system_results.get("analysis", {}).get("status", "not_attempted"),
                "output": self.system_results.get("output", {}).get("status", "not_attempted")
            },
            "performance_metrics": {},
            "trading_summary": {},
            "system_health": {}
        }
        
        # Performance metrics
        total_execution_time = 0
        if "analysis" in self.system_results and self.system_results["analysis"]["status"] == "success":
            total_execution_time += self.system_results["analysis"]["result"]["execution_time_seconds"]
        if "output" in self.system_results and self.system_results["output"]["status"] == "success":
            total_execution_time += self.system_results["output"]["result"]["execution_time_seconds"]
        
        summary["performance_metrics"] = {
            "total_execution_time": total_execution_time,
            "successful_pipelines": len([s for s in summary["execution_status"].values() if s == "success"]),
            "failed_pipelines": len([s for s in summary["execution_status"].values() if s == "failed"])
        }
        
        # Trading summary (from analysis results)
        if "analysis" in self.system_results and self.system_results["analysis"]["status"] == "success":
            analysis_result = self.system_results["analysis"]["result"]
            
            # Extract NQ EV results
            if analysis_result.get("individual_results", {}).get("expected_value", {}).get("status") == "success":
                ev_result = analysis_result["individual_results"]["expected_value"]["result"]
                
                summary["trading_summary"] = {
                    "underlying_price": ev_result["underlying_price"],
                    "algorithm": "nq_options_ev",
                    "quality_setups": ev_result["quality_setups"],
                    "best_ev": ev_result["metrics"]["best_ev"],
                    "avg_probability": ev_result["metrics"]["avg_probability"],
                    "primary_recommendation": None
                }
                
                # Primary recommendation
                if analysis_result.get("synthesis", {}).get("trading_recommendations"):
                    primary_rec = analysis_result["synthesis"]["trading_recommendations"][0]
                    summary["trading_summary"]["primary_recommendation"] = {
                        "direction": primary_rec["trade_direction"],
                        "entry": primary_rec["entry_price"],
                        "target": primary_rec["target"],
                        "stop": primary_rec["stop"],
                        "expected_value": primary_rec["expected_value"],
                        "probability": primary_rec["probability"],
                        "position_size": primary_rec["position_size"]
                    }
        
        # System health
        successful_pipelines = summary["performance_metrics"]["successful_pipelines"]
        total_pipelines = 3
        
        if successful_pipelines == total_pipelines:
            health_status = "excellent"
        elif successful_pipelines >= 2:
            health_status = "good"
        elif successful_pipelines >= 1:
            health_status = "degraded"
        else:
            health_status = "failed"
        
        summary["system_health"] = {
            "status": health_status,
            "pipeline_success_rate": successful_pipelines / total_pipelines,
            "critical_systems_operational": summary["execution_status"]["analysis"] == "success",
            "data_quality_acceptable": summary["execution_status"]["data"] == "success",
            "output_generation_operational": summary["execution_status"]["output"] == "success"
        }
        
        return summary
    
    def run_complete_system(self) -> Dict[str, Any]:
        """Execute the complete NQ Options Trading System"""
        print("=" * 60)
        print("NQ OPTIONS TRADING SYSTEM - COMPLETE EXECUTION")
        print("=" * 60)
        print(f"System Version: {self.version}")
        print(f"Primary Algorithm: Your NQ Options EV Algorithm")
        print(f"Execution Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Step 1: Configuration validation
        config_validation = self.validate_configuration()
        if config_validation["status"] != "valid":
            return create_failure_response(
                "Invalid configuration",
                config_validation=config_validation
            )
        
        # Step 2: Data pipeline
        data_config = self.config.get("data", {})
        self.system_results["data"] = self.run_data_pipeline()
        
        if self.system_results["data"]["status"] != "success":
            print("\n✗ SYSTEM FAILURE: Data pipeline failed")
            return self._create_failure_result("Data pipeline failure")
        
        # Step 3: Analysis pipeline (Your NQ EV Algorithm)
        self.system_results["analysis"] = self.run_analysis_pipeline(data_config)
        
        if self.system_results["analysis"]["status"] != "success":
            print("\n✗ SYSTEM FAILURE: Analysis pipeline failed")
            return self._create_failure_result("Analysis pipeline failure")
        
        # Step 4: Output pipeline (with cached analysis results to avoid re-running)
        analysis_results = self.system_results["analysis"].get("result")
        self.system_results["output"] = self.run_output_pipeline(data_config, analysis_results)
        
        # Output pipeline failure is not critical for system success
        
        # Step 5: System summary
        system_summary = self.create_system_summary()
        
        # Calculate total execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Final system results
        final_results = {
            "timestamp": get_utc_timestamp(),
            "execution_time_seconds": execution_time,
            "system_version": self.version,
            "status": "success",
            "config_validation": config_validation,
            "pipeline_results": self.system_results,
            "system_summary": system_summary,
            "master_config": self.config
        }
        
        # Print success summary
        print(f"\n{'='*60}")
        print("SYSTEM EXECUTION COMPLETE - SUCCESS!")
        print(f"{'='*60}")
        print(f"⏱️  Total Execution Time: {execution_time:.2f}s")
        print(f"📊 System Health: {system_summary['system_health']['status'].title()}")
        print(f"🎯 Pipeline Success Rate: {system_summary['system_health']['pipeline_success_rate']:.1%}")
        
        if system_summary.get("trading_summary", {}).get("primary_recommendation"):
            rec = system_summary["trading_summary"]["primary_recommendation"]
            print(f"💰 Primary Trade: {rec['direction']} EV={rec['expected_value']:+.1f} points")
            print(f"📈 Entry: {rec['entry']:,.2f} → Target: {rec['target']:,.0f}")
            print(f"🛡️  Stop: {rec['stop']:,.0f} | Probability: {rec['probability']:.1%}")
        
        print(f"{'='*60}")
        
        return final_results
    
    def _create_failure_result(self, reason: str) -> Dict[str, Any]:
        """Create failure result structure"""
        return {
            "status": "failed",
            "error": reason,
            "timestamp": get_utc_timestamp(),
            "pipeline_results": self.system_results,
            "system_summary": self.create_system_summary()
        }


# Module-level function for easy integration
def run_complete_nq_trading_system(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Run the complete NQ Options Trading System
    
    Args:
        config: Master system configuration (optional)
        
    Returns:
        Dict with complete system execution results
    """
    if config is None:
        config = {
            "data": {
                "barchart": {
                    "file_path": "data/api_responses/options_data_20250602_141553.json",
                    "use_live_api": True,  # Enable live API by default
                    "futures_symbol": "NQM25",
                    "headless": True
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
                    # Your actual algorithm configuration
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
                "output_dir": "outputs",
                "timestamp_suffix": True
            }
        }
    
    system = NQOptionsTradingSystem(config)
    return system.run_complete_system()
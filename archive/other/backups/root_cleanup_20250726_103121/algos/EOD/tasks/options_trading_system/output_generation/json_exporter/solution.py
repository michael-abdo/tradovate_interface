#!/usr/bin/env python3
"""
TASK: json_exporter
TYPE: Leaf Task
PURPOSE: Export analysis results as structured JSON for programmatic use
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent task to path for analysis access
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

# Add tasks directory for common utilities - work backwards from current location
# Current: tasks/options_trading_system/output_generation/json_exporter/solution.py  
# Target: tasks/common_utils.py
# Go up: json_exporter -> output_generation -> options_trading_system -> tasks
tasks_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, tasks_dir)
from common_utils import PathManager

from analysis_engine.integration import run_analysis_engine


class JSONExporter:
    """Export trading analysis results as structured JSON data"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the JSON exporter
        
        Args:
            config: Configuration for JSON export options
        """
        self.config = config
        self.include_raw_data = config.get("include_raw_data", False)
        self.include_metadata = config.get("include_metadata", True)
        self.format_pretty = config.get("format_pretty", True)
        self.include_analysis_details = config.get("include_analysis_details", True)
        
    def clean_analysis_data(self, data: Any) -> Any:
        """Clean and sanitize analysis data for JSON serialization"""
        if isinstance(data, dict):
            return {k: self.clean_analysis_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.clean_analysis_data(item) for item in data]
        elif hasattr(data, '__dict__'):
            # Handle custom objects by converting to dict
            return self.clean_analysis_data(data.__dict__)
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            # Convert other types to string
            return str(data)
    
    def extract_trading_signals(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract trading signals in a standardized format"""
        signals = []
        
        synthesis = analysis_results.get("synthesis", {})
        trading_recs = synthesis.get("trading_recommendations", [])
        
        for i, rec in enumerate(trading_recs):
            signal = {
                "signal_id": f"nq_ev_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": get_utc_timestamp(),
                "source": rec.get("source", "nq_ev_algorithm"),
                "priority": rec.get("priority", "UNKNOWN"),
                "confidence": rec.get("confidence", "UNKNOWN"),
                "trade": {
                    "direction": rec.get("trade_direction", "UNKNOWN"),
                    "entry_price": rec.get("entry_price", 0),
                    "target_price": rec.get("target", 0),
                    "stop_price": rec.get("stop", 0),
                    "expected_value": rec.get("expected_value", 0),
                    "win_probability": rec.get("probability", 0),
                    "position_size": rec.get("position_size", "N/A"),
                    "risk_reward_ratio": 0
                },
                "reasoning": rec.get("reasoning", ""),
                "metadata": {
                    "rank": i + 1,
                    "total_signals": len(trading_recs)
                }
            }
            
            # Calculate risk/reward ratio
            if signal["trade"]["entry_price"] and signal["trade"]["target_price"] and signal["trade"]["stop_price"]:
                if signal["trade"]["direction"] == "LONG":
                    reward = signal["trade"]["target_price"] - signal["trade"]["entry_price"]
                    risk = signal["trade"]["entry_price"] - signal["trade"]["stop_price"]
                else:  # SHORT
                    reward = signal["trade"]["entry_price"] - signal["trade"]["target_price"]
                    risk = signal["trade"]["stop_price"] - signal["trade"]["entry_price"]
                
                if risk > 0:
                    signal["trade"]["risk_reward_ratio"] = round(reward / risk, 2)
            
            signals.append(signal)
        
        return signals
    
    def extract_market_analysis(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract market analysis data"""
        market_data = {
            "timestamp": get_utc_timestamp(),
            "underlying": {
                "symbol": "NQ",
                "price": 0,
                "analysis_time": analysis_results.get("timestamp", "")
            },
            "sentiment": {
                "overall": "neutral",
                "momentum": "neutral",
                "volatility_regime": "normal"
            },
            "quality_metrics": {},
            "analysis_summary": {}
        }
        
        # Extract market context
        market_context = analysis_results.get("synthesis", {}).get("market_context", {})
        if market_context:
            market_data["underlying"]["price"] = market_context.get("nq_price", 0)
            market_data["sentiment"]["momentum"] = market_context.get("momentum_sentiment", "neutral")
            market_data["sentiment"]["volatility_regime"] = market_context.get("iv_regime", "normal")
            
            # Overall sentiment based on momentum
            market_data["sentiment"]["overall"] = market_context.get("momentum_sentiment", "neutral")
        
        # Extract quality metrics from individual analyses
        individual_results = analysis_results.get("individual_results", {})
        
        # NQ EV Analysis metrics
        if "expected_value" in individual_results and individual_results["expected_value"].get("status") == "success":
            ev_result = individual_results["expected_value"]["result"]
            market_data["quality_metrics"]["nq_ev"] = {
                "quality_setups": ev_result.get("quality_setups", 0),
                "total_setups": ev_result.get("setups_generated", 0),
                "strikes_analyzed": ev_result.get("strikes_analyzed", 0),
                "best_ev": ev_result.get("metrics", {}).get("best_ev", 0),
                "avg_probability": ev_result.get("metrics", {}).get("avg_probability", 0)
            }
        
        # Momentum analysis metrics
        if "momentum" in individual_results and individual_results["momentum"].get("status") == "success":
            momentum_result = individual_results["momentum"]["result"]
            market_data["quality_metrics"]["momentum"] = {
                "momentum_contracts": momentum_result.get("momentum_contracts", 0),
                "sentiment_confidence": momentum_result.get("market_sentiment", {}).get("confidence", 0),
                "bullish_momentum": momentum_result.get("market_sentiment", {}).get("bullish_momentum", 0),
                "bearish_momentum": momentum_result.get("market_sentiment", {}).get("bearish_momentum", 0)
            }
        
        # Volatility analysis metrics
        if "volatility" in individual_results and individual_results["volatility"].get("status") == "success":
            vol_result = individual_results["volatility"]["result"]
            market_data["quality_metrics"]["volatility"] = {
                "iv_opportunities": vol_result.get("total_opportunities", 0),
                "avg_iv": vol_result.get("metrics", {}).get("avg_implied_volatility", 0),
                "iv_spread": vol_result.get("metrics", {}).get("iv_spread", 0),
                "skew_type": vol_result.get("iv_skew_analysis", {}).get("skew_type", "neutral")
            }
        
        # Analysis summary
        summary = analysis_results.get("summary", {})
        market_data["analysis_summary"] = {
            "successful_analyses": summary.get("successful_analyses", 0),
            "total_analyses": 3,
            "execution_time": analysis_results.get("execution_time_seconds", 0),
            "primary_algorithm": analysis_results.get("primary_algorithm", "nq_ev_analysis")
        }
        
        return market_data
    
    def create_export_structure(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create the main export data structure"""
        
        export_data = {
            "metadata": {
                "export_timestamp": get_utc_timestamp(),
                "export_version": "1.0",
                "data_source": "nq_options_trading_system",
                "exporter_config": self.config
            },
            "trading_signals": self.extract_trading_signals(analysis_results),
            "market_analysis": self.extract_market_analysis(analysis_results),
            "execution_summary": {
                "total_signals": 0,
                "high_priority_signals": 0,
                "recommended_action": "hold",
                "next_analysis_recommended": get_utc_timestamp()
            }
        }
        
        # Calculate execution summary
        signals = export_data["trading_signals"]
        export_data["execution_summary"]["total_signals"] = len(signals)
        export_data["execution_summary"]["high_priority_signals"] = len([s for s in signals if s["priority"] in ["PRIMARY", "IMMEDIATE"]])
        
        # Determine recommended action
        if export_data["execution_summary"]["high_priority_signals"] > 0:
            primary_signal = next((s for s in signals if s["priority"] == "PRIMARY"), None)
            if primary_signal:
                export_data["execution_summary"]["recommended_action"] = primary_signal["trade"]["direction"].lower()
            else:
                export_data["execution_summary"]["recommended_action"] = "review_signals"
        else:
            export_data["execution_summary"]["recommended_action"] = "hold"
        
        # Include detailed analysis if requested
        if self.include_analysis_details:
            export_data["detailed_analysis"] = {
                "raw_analysis_results": self.clean_analysis_data(analysis_results) if self.include_raw_data else {},
                "individual_analysis_status": {
                    name: result.get("status", "unknown") 
                    for name, result in analysis_results.get("individual_results", {}).items()
                }
            }
        
        return export_data
    
    def export_json(self, data_config: Dict[str, Any], analysis_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Export analysis results as JSON"""
        
        # Check for cached analysis results first
        if "_cached_analysis_results" in data_config:
            analysis_results = data_config["_cached_analysis_results"]
        else:
            # Run analysis engine to get results
            analysis_results = run_analysis_engine(data_config, analysis_config)
        
        # Create export structure
        export_data = self.create_export_structure(analysis_results)
        
        # Format JSON
        if self.format_pretty:
            json_output = json.dumps(export_data, indent=2, default=str)
        else:
            json_output = json.dumps(export_data, default=str)
        
        return {
            "json_data": export_data,
            "json_string": json_output,
            "metadata": {
                "export_timestamp": get_utc_timestamp(),
                "total_signals": len(export_data["trading_signals"]),
                "json_size_bytes": len(json_output),
                "recommended_action": export_data["execution_summary"]["recommended_action"]
            }
        }


# Module-level function for easy integration
def export_analysis_json(data_config: Dict[str, Any], 
                        export_config: Dict[str, Any] = None,
                        analysis_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Export analysis results as structured JSON
    
    Args:
        data_config: Configuration for data sources
        export_config: Configuration for JSON export (optional)
        analysis_config: Configuration for analysis engine (optional)
        
    Returns:
        Dict with JSON data and metadata
    """
    if export_config is None:
        export_config = {
            "include_raw_data": False,
            "include_metadata": True,
            "format_pretty": True,
            "include_analysis_details": True
        }
    
    exporter = JSONExporter(export_config)
    return exporter.export_json(data_config, analysis_config)
#!/usr/bin/env python3
"""
TASK: analysis_engine
TYPE: Parent Task Integration
PURPOSE: Coordinate all analysis strategies including your actual NQ EV algorithm
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Add current directory to path for child task imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Add tasks directory for common utilities
tasks_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, tasks_dir)
from common_utils import PathManager, get_utc_timestamp, create_success_response, create_failure_response

# Add project root for test_utils  
project_root = os.path.dirname(tasks_dir)
sys.path.insert(0, project_root)
from tasks.test_utils import estimate_underlying_price

# Import child task modules - using your actual NQ EV algorithm
from expected_value_analysis.solution import analyze_expected_value
from risk_analysis.solution import run_risk_analysis
from volume_shock_analysis.solution import analyze_volume_shocks
from volume_spike_dead_simple.solution import (
    DeadSimpleVolumeSpike, 
    create_enhanced_dead_simple_analyzer,
    create_configured_analyzer
)


class AnalysisEngine:
    """Unified analysis engine coordinating your NQ EV algorithm with risk analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the analysis engine
        
        Args:
            config: Configuration containing analysis settings for each strategy
        """
        self.config = config
        self.analysis_results = {}
        
    def run_nq_ev_analysis(self, data_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run your actual NQ Options Expected Value analysis"""
        print("  Running NQ Options EV Analysis (Your Algorithm)...")
        
        # Use your algorithm's configuration with strict quality criteria
        ev_config = self.config.get("expected_value", {
            "weights": {
                "oi_factor": 0.35,
                "vol_factor": 0.25,
                "pcr_factor": 0.25,
                "distance_factor": 0.15
            },
            "min_ev": 15,  # Your algorithm's strict threshold
            "min_probability": 0.60,  # Your algorithm's strict threshold
            "max_risk": 150,  # Your algorithm's strict threshold
            "min_risk_reward": 1.0  # Your algorithm's strict threshold
        })
        
        try:
            result = analyze_expected_value(data_config, ev_config)
            print(f"    ✓ NQ EV Analysis: {result['quality_setups']} quality setups found")
            
            if result.get("trading_report", {}).get("execution_recommendation"):
                rec = result["trading_report"]["execution_recommendation"]
                print(f"    ✓ Best trade: {rec['trade_direction']} EV={rec['expected_value']:+.1f} points")
            
            return create_success_response(result=result)
        except Exception as e:
            print(f"    ✗ NQ EV Analysis failed: {str(e)}")
            return create_failure_response(e)
    
    def run_risk_analysis(self, data_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run risk analysis (institutional positioning)"""
        print("  Running Risk Analysis...")
        
        risk_config = self.config.get("risk", {
            "multiplier": 20,
            "immediate_threat_distance": 10,
            "near_term_distance": 25,
            "medium_term_distance": 50
        })
        
        try:
            result = run_risk_analysis(data_config, risk_config)
            
            if result["status"] == "success":
                print(f"    ✓ Risk Analysis: {result['metrics']['total_positions_at_risk']} positions at risk, "
                      f"bias: {result['summary']['bias']}")
                return create_success_response(result=result)
            else:
                print(f"    ✗ Risk Analysis failed: {result.get('error', 'Unknown error')}")
                return create_failure_response(result.get('error', 'Unknown error'))
        except Exception as e:
            print(f"    ✗ Risk Analysis failed: {str(e)}")
            return create_failure_response(e)
    
    def run_volume_shock_analysis(self, data_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run volume shock analysis (The Egg Rush Strategy)"""
        print("  Running Volume Shock Analysis (Front-Running Market Makers)...")
        
        volume_shock_config = self.config.get("volume_shock", {
            "volume_ratio_threshold": 4.0,
            "min_volume_threshold": 100,
            "pressure_threshold": 50.0,
            "high_delta_threshold": 2000,
            "emergency_delta_threshold": 5000,
            "validation_mode": True
        })
        
        try:
            result = analyze_volume_shocks(data_config, volume_shock_config)
            
            if result["status"] == "success":
                alerts = result.get("alerts", [])
                recommendations = result.get("execution_recommendations", [])
                
                print(f"    ✓ Volume Shock Analysis: {len(alerts)} alerts, {len(recommendations)} signals")
                
                if recommendations:
                    primary_signal = recommendations[0]
                    print(f"    ✓ Primary signal: {primary_signal['trade_direction']} "
                          f"EV={primary_signal['expected_value']:+.1f} points "
                          f"({primary_signal['flow_type']})")
                
                return create_success_response(result=result)
            else:
                print(f"    ✗ Volume Shock Analysis failed: {result.get('error', 'Unknown error')}")
                return create_failure_response(result.get('error', 'Unknown error'))
        except Exception as e:
            print(f"    ✗ Volume Shock Analysis failed: {str(e)}")
            return create_failure_response(e)
    
    def run_dead_simple_analysis(self, data_config: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced DEAD Simple institutional flow detection with comprehensive logging"""
        print("  Running Enhanced DEAD Simple Analysis (Institutional Flow with Relative Thresholds)...")
        
        dead_simple_config = self.config.get("dead_simple", {
            "threshold_mode": "relative",  # Enable enhanced mode by default
            "enable_cross_strike": True,
            "enable_premium_velocity": True,
            "min_vol_oi_ratio": 8,  # Slightly more sensitive for relative mode
            "min_volume": 400,
            "min_dollar_size": 75000,
            "max_distance_percent": 2.0,
            "confidence_thresholds": {
                "extreme": 50,
                "very_high": 30,
                "high": 20,
                "moderate": 10
            }
        })
        
        try:
            # Import data ingestion pipeline (following pattern of other analyses)
            from data_ingestion.integration import run_data_ingestion
            
            # Load normalized data like other analyses do
            print("    Fetching options data via data ingestion pipeline...")
            pipeline_result = run_data_ingestion(data_config)
            
            if pipeline_result["pipeline_status"] != "success":
                print("    ✗ Data ingestion pipeline failed")
                return create_failure_response("Data ingestion pipeline failed")
            
            # Extract normalized contracts
            contracts = pipeline_result["normalized_data"]["contracts"]
            
            if not contracts:
                print("    ✗ No options contracts available")
                return create_failure_response("No options contracts available")
            
            # Estimate underlying price from contracts
            current_price = self._estimate_underlying_price(contracts)
            
            # Convert normalized contracts to enhanced format
            options_data = self._convert_to_dead_simple_format(contracts)
            
            # Extract contract identifier for enhanced analysis
            contract = self._extract_contract_identifier(contracts)
            
            print(f"    ✓ Loaded {len(contracts)} contracts for {contract}, underlying price: ${current_price:,.2f}")
            
            # Initialize enhanced analyzer based on configuration
            if dead_simple_config.get("threshold_mode") == "relative":
                print(f"    ✓ Using enhanced relative analysis mode")
                analyzer = create_enhanced_dead_simple_analyzer(dead_simple_config)
            elif dead_simple_config.get("template"):
                template_name = dead_simple_config["template"]
                print(f"    ✓ Using configuration template: {template_name}")
                analyzer = create_configured_analyzer(template_name, dead_simple_config)
            else:
                print(f"    ✓ Using traditional absolute threshold mode")
                analyzer = DeadSimpleVolumeSpike(dead_simple_config)
            
            # Enhanced institutional flow analysis
            analysis_result = analyzer.find_institutional_flow(options_data, current_price, contract)
            
            # Handle both old and new result formats
            if isinstance(analysis_result, dict):
                # New enhanced format
                signals = analysis_result.get('signals', [])
                cross_strike_analysis = analysis_result.get('cross_strike_analysis', {})
                summary = analysis_result.get('summary', {})
                metadata = analysis_result.get('metadata', {})
                
                print(f"    ✓ Enhanced analysis mode: {metadata.get('analysis_mode', 'unknown')}")
                print(f"    ✓ Cross-strike analysis: {metadata.get('cross_strike_enabled', False)}")
                print(f"    ✓ Filter pass rate: {metadata.get('filter_pass_rate', 0):.1f}%")
                
                if cross_strike_analysis:
                    institutional_pressure = cross_strike_analysis.get('institutional_pressure', 'NEUTRAL')
                    print(f"    ✓ Institutional pressure: {institutional_pressure}")
                    
                    if cross_strike_analysis.get('coordinated_flow_detected'):
                        print(f"    ⚠️  Coordinated institutional flow detected!")
            else:
                # Old format (list of signals) - convert for compatibility
                signals = analysis_result if isinstance(analysis_result, list) else []
                cross_strike_analysis = {}
                summary = analyzer.summarize_institutional_activity(signals) if signals else {}
                metadata = {
                    'analysis_mode': 'absolute',
                    'signals_detected': len(signals),
                    'cross_strike_enabled': False
                }
            
            # Filter for actionable signals
            actionable_signals = []
            max_distance = dead_simple_config.get("max_distance_percent", 2.0)
            
            for signal in signals:
                distance_pct = abs(signal.strike - current_price) / current_price * 100
                if distance_pct <= max_distance:
                    actionable_signals.append(signal)
            
            # Generate enhanced trade plans for top signals
            trade_plans = []
            for signal in actionable_signals[:3]:  # Top 3 actionable signals
                trade_plan = analyzer.generate_trade_plan(signal, current_price)
                
                # Enhance trade plan with relative analysis data if available
                if signal.is_enhanced_analysis():
                    trade_plan["enhanced_metrics"] = {
                        "relative_volume_ratio": signal.relative_volume_ratio,
                        "volume_percentile_rank": signal.volume_percentile_rank,
                        "dynamic_confidence_score": signal.dynamic_confidence_score,
                        "baseline_data_source": signal.baseline_data_source,
                        "enhanced_confidence_description": signal.get_enhanced_confidence_description()
                    }
                
                trade_plans.append(trade_plan)
            
            print(f"    ✓ Enhanced DEAD Simple Analysis: {len(signals)} institutional signals found")
            print(f"    ✓ Actionable signals (within {max_distance}%): {len(actionable_signals)}")
            
            if signals:
                top_signal = signals[0]
                enhanced_desc = (top_signal.get_enhanced_confidence_description() 
                               if top_signal.is_enhanced_analysis() else top_signal.confidence)
                print(f"    ✓ Top signal: {top_signal.strike}{top_signal.option_type[0]} "
                      f"Vol/OI={top_signal.vol_oi_ratio:.1f}x ${top_signal.dollar_size:,.0f} "
                      f"({enhanced_desc})")
                
                # Log enhanced metrics if available
                if top_signal.is_enhanced_analysis():
                    print(f"    ✓ Enhanced metrics: {top_signal.relative_volume_ratio:.1f}x historical avg, "
                          f"{top_signal.volume_percentile_rank:.0f}th percentile")
            
            # Enhanced result structure
            enhanced_result = {
                "signals": [s.to_dict() for s in signals],
                "actionable_signals": [s.to_dict() for s in actionable_signals],
                "trade_plans": trade_plans,
                "summary": summary,
                "cross_strike_analysis": cross_strike_analysis,
                "metadata": metadata,
                "total_signals": len(signals),
                "actionable_signals_count": len(actionable_signals),
                "extreme_signals": len([s for s in signals if s.confidence == "EXTREME"]),
                "enhanced_signals": len([s for s in signals if s.is_enhanced_analysis()]),
                "contract_analyzed": contract
            }
            
            return create_success_response(result=enhanced_result)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"    ✗ Enhanced DEAD Simple Analysis failed: {str(e)}")
            print(f"    ✗ Error details: {error_details}")
            return {
                "status": "failed",
                "error": str(e),
                "error_details": error_details,
                "timestamp": get_utc_timestamp()
            }
    
    def _estimate_underlying_price(self, contracts: List[Dict]) -> float:
        """Estimate underlying price from contracts (following pattern of other analyses)"""
        # Use canonical implementation from test_utils
        return estimate_underlying_price(contracts)
    
    def _extract_contract_identifier(self, contracts: List[Dict]) -> str:
        """Extract contract identifier for enhanced analysis"""
        if not contracts:
            return "MC7M25"  # Default fallback
        
        # Try to extract from contract metadata
        for contract in contracts[:10]:  # Check first 10 contracts
            if contract.get('symbol'):
                symbol = str(contract['symbol'])
                # Extract contract root (e.g., MC7M25 from various formats)
                if len(symbol) >= 5:
                    return symbol[:6] if symbol[5:6].isdigit() else symbol[:5]
            
            if contract.get('expiration'):
                # Try to construct from expiration date
                exp_str = str(contract['expiration'])
                if '2025' in exp_str:
                    if '07' in exp_str or 'Jul' in exp_str:
                        return "MC7M25"  # July 2025
                    elif '01' in exp_str or 'Jan' in exp_str:
                        return "MC1M25"  # January 2025
                    elif '03' in exp_str or 'Mar' in exp_str:
                        return "MC3M25"  # March 2025
        
        return "MC7M25"  # Default fallback
    
    def _convert_to_dead_simple_format(self, contracts: List[Dict]) -> List[Dict]:
        """Convert normalized contracts to DEAD Simple expected format"""
        options_data = []
        
        for contract in contracts:
            # Convert normalized contract to DEAD Simple format with proper null handling
            option_data = {
                'strike': contract.get('strike') or 0,
                'optionType': (contract.get('type') or '').upper(),  # 'call' -> 'CALL', 'put' -> 'PUT'
                'volume': contract.get('volume') or 0,
                'openInterest': contract.get('open_interest') or 0,
                'lastPrice': contract.get('last_price') or 0,
                'expirationDate': contract.get('expiration') or '',
                'bid': contract.get('bid') or 0,
                'ask': contract.get('ask') or 0
            }
            
            # Only include if we have the required fields
            if (option_data['strike'] > 0 and 
                option_data['optionType'] in ['CALL', 'PUT'] and
                option_data['volume'] >= 0 and
                option_data['openInterest'] >= 0):
                options_data.append(option_data)
        
        return options_data
    
    def synthesize_analysis_results(self) -> Dict[str, Any]:
        """Synthesize results prioritizing your NQ EV algorithm"""
        print("  Synthesizing Analysis Results (NQ EV Algorithm Priority)...")
        
        synthesis = {
            "timestamp": get_utc_timestamp(),
            "primary_algorithm": "nq_ev_analysis",
            "analysis_summary": {},
            "trading_recommendations": [],
            "market_context": {},
            "execution_priorities": []
        }
        
        # Extract key insights from each analysis
        successful_analyses = [name for name, result in self.analysis_results.items() 
                             if result["status"] == "success"]
        
        synthesis["analysis_summary"] = {
            "total_analyses": len(self.analysis_results),
            "successful_analyses": len(successful_analyses),
            "failed_analyses": len(self.analysis_results) - len(successful_analyses),
            "analysis_types": list(self.analysis_results.keys())
        }
        
        # Prioritize your NQ EV algorithm results
        primary_recommendations = []
        
        # Your NQ EV algorithm (highest priority)
        if "expected_value" in successful_analyses:
            nq_result = self.analysis_results["expected_value"]["result"]
            
            # Extract trading recommendations from your algorithm
            if nq_result.get("trading_report", {}).get("execution_recommendation"):
                rec = nq_result["trading_report"]["execution_recommendation"]
                primary_recommendations.append({
                    "source": "nq_ev_algorithm",
                    "priority": "PRIMARY",
                    "trade_direction": rec["trade_direction"],
                    "entry_price": rec["entry_price"],
                    "target": rec["target"],
                    "stop": rec["stop"],
                    "expected_value": rec["expected_value"],
                    "probability": rec["probability"],
                    "position_size": rec["position_size"],
                    "confidence": "HIGH",
                    "reasoning": f"Your NQ EV algorithm found high-quality setup with EV={rec['expected_value']:+.1f} points"
                })
            
            # Add top opportunities from your algorithm
            for i, opp in enumerate(nq_result.get("trading_report", {}).get("top_opportunities", [])[:3], 1):
                if i > 1:  # Skip first one as it's already in primary recommendation
                    primary_recommendations.append({
                        "source": "nq_ev_algorithm",
                        "priority": "SECONDARY",
                        "rank": i,
                        "trade_direction": opp["direction"].upper(),
                        "target": opp["tp"],
                        "stop": opp["sl"],
                        "expected_value": opp["expected_value"],
                        "probability": opp["probability"],
                        "confidence": "MEDIUM",
                        "reasoning": f"Your NQ EV algorithm setup #{i} with EV={opp['expected_value']:+.1f}"
                    })
        
        # Enhanced DEAD Simple Analysis (HIGHEST PRIORITY for EXTREME signals)
        if "dead_simple" in successful_analyses:
            dead_simple_result = self.analysis_results["dead_simple"]["result"]
            dead_simple_plans = dead_simple_result.get("trade_plans", [])
            cross_strike_analysis = dead_simple_result.get("cross_strike_analysis", {})
            
            for i, plan in enumerate(dead_simple_plans[:3]):  # Top 3 institutional signals
                signal = plan["signal"]
                enhanced_metrics = plan.get("enhanced_metrics", {})
                
                # Enhanced priority calculation
                if signal["confidence"] == "EXTREME":
                    priority = "IMMEDIATE"
                    confidence = "EXTREME"
                    probability = 0.80  # Higher confidence for enhanced analysis
                elif signal["confidence"] == "VERY_HIGH":
                    priority = "PRIMARY"
                    confidence = "VERY_HIGH"
                    probability = 0.70
                else:
                    priority = "HIGH"
                    confidence = signal["confidence"]
                    probability = 0.65
                
                # Boost confidence and probability for enhanced signals
                if enhanced_metrics.get("dynamic_confidence_score"):
                    dynamic_score = enhanced_metrics["dynamic_confidence_score"]
                    if dynamic_score > 80:
                        priority = "IMMEDIATE"
                        probability = min(0.85, probability + 0.05)
                
                # Enhanced reasoning with relative metrics
                reasoning_parts = [f"Institutional ${signal['dollar_size']:,.0f} flow at {signal['strike']}{signal['option_type'][0]}"]
                reasoning_parts.append(f"({signal['vol_oi_ratio']:.1f}x Vol/OI)")
                
                if enhanced_metrics.get("relative_volume_ratio"):
                    reasoning_parts.append(f"{enhanced_metrics['relative_volume_ratio']:.1f}x historical avg")
                
                if enhanced_metrics.get("volume_percentile_rank"):
                    reasoning_parts.append(f"{enhanced_metrics['volume_percentile_rank']:.0f}th percentile")
                
                if cross_strike_analysis.get('coordinated_flow_detected'):
                    reasoning_parts.append("COORDINATED FLOW")
                    priority = "IMMEDIATE"  # Coordinated flow gets immediate priority
                
                rec = {
                    "source": "enhanced_dead_simple_analysis",
                    "priority": priority,
                    "rank": i + 1,
                    "trade_direction": signal["direction"],
                    "entry_price": plan["entry_price"],
                    "target": plan["take_profit"],
                    "stop": plan["stop_loss"],
                    "expected_value": (plan["take_profit"] - plan["entry_price"]) * (1 if signal["direction"] == "LONG" else -1),
                    "probability": probability,
                    "position_size": plan["size_multiplier"],
                    "confidence": confidence,
                    "vol_oi_ratio": signal["vol_oi_ratio"],
                    "dollar_size": signal["dollar_size"],
                    "strike": signal["strike"],
                    "option_type": signal["option_type"],
                    "reasoning": " - ".join(reasoning_parts)
                }
                
                # Add enhanced metrics to recommendation if available
                if enhanced_metrics:
                    rec["enhanced_metrics"] = enhanced_metrics
                    rec["analysis_mode"] = "relative" if enhanced_metrics.get("baseline_data_source") != "absolute_thresholds" else "absolute"
                
                # Add cross-strike context if available
                if cross_strike_analysis:
                    rec["institutional_pressure"] = cross_strike_analysis.get("institutional_pressure", "NEUTRAL")
                    rec["coordinated_flow"] = cross_strike_analysis.get("coordinated_flow_detected", False)
                
                primary_recommendations.append(rec)
        
        # Volume Shock Analysis (High Priority - Time Sensitive)
        if "volume_shock" in successful_analyses:
            volume_result = self.analysis_results["volume_shock"]["result"]
            volume_recommendations = volume_result.get("execution_recommendations", [])
            
            for i, rec in enumerate(volume_recommendations[:2]):  # Top 2 volume shock signals
                primary_recommendations.append({
                    "source": "volume_shock_analysis",
                    "priority": "IMMEDIATE" if rec["priority"] == "PRIMARY" else "HIGH",
                    "rank": i + 1,
                    "trade_direction": rec["trade_direction"],
                    "entry_price": rec["entry_price"],
                    "target": rec["target_price"],
                    "stop": rec["stop_price"],
                    "expected_value": rec["expected_value"],
                    "probability": rec["confidence"],
                    "position_size": rec["position_size"],
                    "confidence": rec["execution_urgency"],
                    "max_hold_time": rec["max_hold_time_minutes"],
                    "flow_type": rec["flow_type"],
                    "reasoning": rec["reasoning"]
                })
        
        # Sort all recommendations by priority
        priority_order = {"IMMEDIATE": 0, "PRIMARY": 1, "SECONDARY": 2, "HIGH": 3, "MEDIUM": 4}
        primary_recommendations.sort(key=lambda x: (priority_order.get(x["priority"], 999), -x.get("dollar_size", 0)))
        
        synthesis["trading_recommendations"] = primary_recommendations
        
        # Market context from analyses
        market_context = {}
        
        if "risk" in successful_analyses:
            risk_result = self.analysis_results["risk"]["result"]
            market_context["risk_bias"] = risk_result["summary"]["bias"]
            market_context["risk_verdict"] = risk_result["summary"]["verdict"]
            market_context["critical_zones"] = len(risk_result.get("battle_zones", []))
            market_context["total_risk_exposure"] = risk_result["metrics"]["total_risk_exposure"]
        
        if "expected_value" in successful_analyses:
            nq_result = self.analysis_results["expected_value"]["result"]
            market_context["nq_price"] = nq_result["underlying_price"]
            market_context["quality_setups"] = nq_result["quality_setups"]
            market_context["best_ev"] = nq_result["metrics"]["best_ev"]
        
        if "volume_shock" in successful_analyses:
            volume_result = self.analysis_results["volume_shock"]["result"]
            market_context["volume_shock_alerts"] = len(volume_result.get("alerts", []))
            market_context["volume_shock_intensity"] = volume_result.get("market_context", {}).get("volume_shock_intensity", {})
            market_context["execution_window"] = volume_result.get("market_context", {}).get("optimal_trading_window", {})
        
        if "dead_simple" in successful_analyses:
            dead_simple_result = self.analysis_results["dead_simple"]["result"]
            market_context["institutional_signals"] = dead_simple_result["total_signals"]
            market_context["extreme_institutional_signals"] = dead_simple_result["extreme_signals"]
            market_context["actionable_signals"] = dead_simple_result.get("actionable_signals_count", 0)
            market_context["enhanced_signals"] = dead_simple_result.get("enhanced_signals", 0)
            market_context["contract_analyzed"] = dead_simple_result.get("contract_analyzed", "unknown")
            
            # Enhanced institutional context
            if dead_simple_result.get("summary"):
                market_context["institutional_positioning"] = dead_simple_result["summary"].get("net_positioning", "NEUTRAL")
                market_context["institutional_dollar_volume"] = dead_simple_result["summary"].get("total_dollar_volume", 0)
                market_context["top_institutional_strikes"] = dead_simple_result["summary"].get("top_strikes", [])[:3]
            
            # Cross-strike analysis context
            if dead_simple_result.get("cross_strike_analysis"):
                cross_strike = dead_simple_result["cross_strike_analysis"]
                market_context["institutional_pressure"] = cross_strike.get("institutional_pressure", "NEUTRAL")
                market_context["coordinated_flow_detected"] = cross_strike.get("coordinated_flow_detected", False)
                market_context["volume_weighted_skew"] = cross_strike.get("volume_weighted_skew", 0.0)
                
                if cross_strike.get("call_correlation"):
                    market_context["call_correlation_strength"] = cross_strike["call_correlation"].get("correlation_strength", 0.0)
                
                if cross_strike.get("put_correlation"):
                    market_context["put_correlation_strength"] = cross_strike["put_correlation"].get("correlation_strength", 0.0)
            
            # Enhanced metadata
            if dead_simple_result.get("metadata"):
                metadata = dead_simple_result["metadata"]
                market_context["analysis_mode"] = metadata.get("analysis_mode", "unknown")
                market_context["filter_pass_rate"] = metadata.get("filter_pass_rate", 0)
                market_context["analysis_duration"] = metadata.get("analysis_duration_seconds", 0)
        
        synthesis["market_context"] = market_context
        
        # Execution priorities (your NQ EV algorithm gets highest priority)
        execution_priorities = []
        
        for i, rec in enumerate(primary_recommendations):
            if rec["priority"] == "PRIMARY":
                priority_level = "IMMEDIATE"
                reasoning = f"Your NQ EV algorithm's top recommendation with EV={rec['expected_value']:+.1f}"
            elif rec["priority"] == "SECONDARY" and i < 3:
                priority_level = "HIGH"
                reasoning = f"Your NQ EV algorithm's alternative setup #{rec.get('rank', i)}"
            else:
                priority_level = "MEDIUM"
                reasoning = f"Additional opportunity from {rec['source']}"
            
            execution_priorities.append({
                "recommendation": rec,
                "priority": priority_level,
                "reasoning": reasoning
            })
        
        synthesis["execution_priorities"] = execution_priorities
        
        print(f"    ✓ Synthesis complete: {len(primary_recommendations)} NQ EV recommendations prioritized")
        return synthesis
    
    def run_full_analysis(self, data_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete analysis engine with NQ EV, Risk Analysis, Volume Shock, and DEAD Simple"""
        print("EXECUTING ANALYSIS ENGINE (NQ EV + Risk + Volume Shock + DEAD Simple)")
        print("-" * 50)
        
        start_time = datetime.now()
        
        # Run all analyses in parallel for speed
        print("  Running all analyses simultaneously...")
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all analyses to run concurrently
            futures = {
                executor.submit(self.run_nq_ev_analysis, data_config): "expected_value",
                executor.submit(self.run_risk_analysis, data_config): "risk",
                executor.submit(self.run_volume_shock_analysis, data_config): "volume_shock",
                executor.submit(self.run_dead_simple_analysis, data_config): "dead_simple"
            }
            
            # Collect results as they complete
            for future in as_completed(futures):
                analysis_name = futures[future]
                try:
                    self.analysis_results[analysis_name] = future.result()
                    if self.analysis_results[analysis_name]["status"] == "success":
                        print(f"    ✓ {analysis_name.replace('_', ' ').title()} completed")
                except Exception as e:
                    print(f"    ✗ {analysis_name} failed: {str(e)}")
                    self.analysis_results[analysis_name] = {
                        "status": "failed",
                        "error": str(e),
                        "timestamp": get_utc_timestamp()
                    }
        
        print("  All analyses complete. Synthesizing results...")
        
        # Synthesize results with NQ EV priority
        synthesis = self.synthesize_analysis_results()
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Final results
        final_results = {
            "timestamp": get_utc_timestamp(),
            "execution_time_seconds": execution_time,
            "primary_algorithm": "nq_ev_analysis",
            "analysis_config": self.config,
            "individual_results": self.analysis_results,
            "synthesis": synthesis,
            "status": "success",
            "summary": {
                "successful_analyses": len([r for r in self.analysis_results.values() if r["status"] == "success"]),
                "primary_recommendations": len([r for r in synthesis["trading_recommendations"] if r["priority"] == "PRIMARY"]),
                "market_context": synthesis["market_context"],
                "execution_priorities": len(synthesis["execution_priorities"])
            }
        }
        
        print(f"\nANALYSIS ENGINE COMPLETE")
        print(f"✓ Execution time: {execution_time:.2f}s")
        print(f"✓ Successful analyses: {final_results['summary']['successful_analyses']}/4")
        print(f"✓ Primary recommendations: {final_results['summary']['primary_recommendations']}")
        
        # Show best NQ EV recommendation
        if synthesis["trading_recommendations"]:
            best = synthesis["trading_recommendations"][0]
            print(f"✓ Best NQ EV trade: {best['trade_direction']} EV={best['expected_value']:+.1f} points")
        
        return final_results


# Module-level function for easy integration
def run_analysis_engine(data_config: Dict[str, Any], analysis_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Run the complete analysis engine with your NQ EV algorithm as primary
    
    Args:
        data_config: Configuration for data sources
        analysis_config: Configuration for analysis strategies (optional)
        
    Returns:
        Dict with comprehensive analysis results prioritizing your NQ EV algorithm
    """
    if analysis_config is None:
        analysis_config = {
            "expected_value": {
                # Your algorithm's configuration
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
            "risk": {
                "multiplier": 20,
                "immediate_threat_distance": 10,
                "near_term_distance": 25,
                "medium_term_distance": 50
            },
            "volume_shock": {
                "volume_ratio_threshold": 4.0,
                "min_volume_threshold": 100,
                "pressure_threshold": 50.0,
                "high_delta_threshold": 2000,
                "emergency_delta_threshold": 5000,
                "validation_mode": True
            },
            "dead_simple": {
                "threshold_mode": "relative",  # Enhanced mode by default
                "enable_cross_strike": True,
                "enable_premium_velocity": True,
                "min_vol_oi_ratio": 8,  # More sensitive for relative mode
                "min_volume": 400,
                "min_dollar_size": 75000,
                "max_distance_percent": 2.0,
                "confidence_thresholds": {
                    "extreme": 50,
                    "very_high": 30,
                    "high": 20,
                    "moderate": 10
                }
            }
        }
    
    engine = AnalysisEngine(analysis_config)
    return engine.run_full_analysis(data_config)
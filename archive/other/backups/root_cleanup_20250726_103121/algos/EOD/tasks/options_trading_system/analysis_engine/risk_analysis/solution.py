#!/usr/bin/env python3
"""
TASK: risk_analysis
TYPE: Leaf Task  
PURPOSE: Analyze options positioning risk to identify institutional commitments and battle zones
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add tasks directory to path for common utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from common_utils import get_utc_timestamp, create_success_response, create_failure_response

# Add project root to path for data model imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

# Import canonical estimate_underlying_price
from tasks.test_utils import estimate_underlying_price


class RiskAnalyzer:
    """Options Risk Analyzer - 'Who Has More Skin in the Game?'"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the risk analyzer
        
        Args:
            config: Risk analysis configuration
        """
        self.config = config
        self.multiplier = config.get("multiplier", 20)  # NQ multiplier
        self.immediate_distance = config.get("immediate_threat_distance", 10)
        self.near_term_distance = config.get("near_term_distance", 25)
        self.medium_term_distance = config.get("medium_term_distance", 50)
        
    def calculate_reinforcement_strength(self, open_interest: float, volume: float) -> str:
        """Calculate reinforcement strength based on volume vs OI"""
        if open_interest > 0:
            activity_ratio = volume / open_interest
            if activity_ratio > 1.0:
                return "HEAVY REINFORCEMENTS"
            elif activity_ratio > 0.5:
                return "MODERATE ACTIVITY"
            else:
                return "EXISTING POSITIONS"
        else:
            return "NEW POSITIONS ONLY"
    
    def calculate_danger_score(self, risk_amount: float, distance: float) -> tuple:
        """Calculate danger score and urgency based on proximity"""
        if distance <= self.immediate_distance:
            urgency = "IMMEDIATE"
            multiplier = 3.0
        elif distance <= self.near_term_distance:
            urgency = "NEAR TERM"
            multiplier = 2.0
        elif distance <= self.medium_term_distance:
            urgency = "MEDIUM TERM"
            multiplier = 1.0
        else:
            urgency = "DISTANT"
            multiplier = 0.5
        
        return risk_amount * multiplier, urgency
    
    def _estimate_underlying_price(self, contracts: List[Dict]) -> float:
        """Estimate current underlying price from contract data"""
        # Use canonical implementation from test_utils
        return estimate_underlying_price(contracts)
    
    def analyze_risk(self, data_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive options risk analysis
        
        Args:
            data_config: Configuration with normalized data
            
        Returns:
            Dict with risk analysis results
        """
        print("    Running Risk Analysis (Skin in the Game)...")
        
        try:
            # Check if data is already normalized (for testing) or needs pipeline processing
            if "normalized_data" in data_config:
                # Direct normalized data (testing scenario)
                normalized_data = data_config["normalized_data"]
                contracts = normalized_data.get("contracts", [])
                underlying_price = normalized_data.get("underlying_price", 0)
            else:
                # Load data using data ingestion pipeline (production scenario)
                sys.path.insert(0, os.path.join(project_root, 'tasks', 'options_trading_system'))
                from data_ingestion.integration import run_data_ingestion
                
                pipeline_result = run_data_ingestion(data_config)
                
                if pipeline_result["pipeline_status"] != "success":
                    return create_failure_response("Data ingestion pipeline failed for risk analysis")
                
                # Extract normalized data
                normalized_data = pipeline_result["normalized_data"]
                contracts = normalized_data.get("contracts", [])
                underlying_price = self._estimate_underlying_price(contracts)
            
            if not contracts:
                return create_failure_response("No contract data available for risk analysis")
            
            # Initialize risk containers
            calls_at_risk = []
            puts_at_risk = []
            total_call_risk = 0
            total_put_risk = 0
            
            # STEP 1: CLASSIFY RISK BY STRIKE
            for contract in contracts:
                strike = contract.get("strike", 0)
                call_oi = contract.get("call_open_interest", 0)
                put_oi = contract.get("put_open_interest", 0)
                call_premium = contract.get("call_mark_price", 0)
                put_premium = contract.get("put_mark_price", 0)
                volume = contract.get("volume", 0)
                
                call_risk = call_oi * call_premium * self.multiplier
                put_risk = put_oi * put_premium * self.multiplier
                distance = abs(strike - underlying_price)
                
                # Calls at risk if OTM (strike > current price)
                if strike > underlying_price and call_risk > 0:
                    calls_at_risk.append({
                        "strike": strike,
                        "open_interest": call_oi,
                        "premium": call_premium,
                        "total_risk": call_risk,
                        "distance": strike - underlying_price,
                        "volume": volume,
                        "reinforcement": self.calculate_reinforcement_strength(call_oi, volume)
                    })
                    total_call_risk += call_risk
                
                # Puts at risk if OTM (strike < current price)
                if strike < underlying_price and put_risk > 0:
                    puts_at_risk.append({
                        "strike": strike,
                        "open_interest": put_oi,
                        "premium": put_premium,
                        "total_risk": put_risk,
                        "distance": underlying_price - strike,
                        "volume": volume,
                        "reinforcement": self.calculate_reinforcement_strength(put_oi, volume)
                    })
                    total_put_risk += put_risk
            
            # STEP 2: CALCULATE DOMINANCE METRICS
            if total_put_risk > 0:
                risk_ratio = total_call_risk / total_put_risk
            else:
                risk_ratio = float('inf') if total_call_risk > 0 else 0
            
            if risk_ratio > 2.0:
                verdict = "STRONG CALL DOMINANCE - Bulls have much more to lose"
                bias = "UPWARD PRESSURE EXPECTED"
            elif risk_ratio < 0.5:
                verdict = "STRONG PUT DOMINANCE - Bears have much more to lose"
                bias = "DOWNWARD PRESSURE EXPECTED"
            else:
                verdict = "BALANCED RISK - Contested territory"
                bias = "SIDEWAYS/CHOPPY ACTION EXPECTED"
            
            # STEP 3: FIND CRITICAL BATTLE ZONES
            calls_at_risk.sort(key=lambda x: x["distance"])
            puts_at_risk.sort(key=lambda x: x["distance"])
            
            nearest_call_threat = calls_at_risk[0] if calls_at_risk else None
            nearest_put_threat = puts_at_risk[0] if puts_at_risk else None
            
            # STEP 4: BATTLE ZONE MAPPING
            battle_zones = []
            
            # Process calls at risk
            for call_risk in calls_at_risk:
                danger_score, urgency = self.calculate_danger_score(call_risk["total_risk"], call_risk["distance"])
                battle_zones.append({
                    "strike": call_risk["strike"],
                    "type": "CALL DEFENSE",
                    "risk_amount": call_risk["total_risk"],
                    "distance": call_risk["distance"],
                    "danger_score": danger_score,
                    "urgency": urgency,
                    "open_interest": call_risk["open_interest"],
                    "reinforcement": call_risk["reinforcement"]
                })
            
            # Process puts at risk
            for put_risk in puts_at_risk:
                danger_score, urgency = self.calculate_danger_score(put_risk["total_risk"], put_risk["distance"])
                battle_zones.append({
                    "strike": put_risk["strike"],
                    "type": "PUT DEFENSE", 
                    "risk_amount": put_risk["total_risk"],
                    "distance": put_risk["distance"],
                    "danger_score": danger_score,
                    "urgency": urgency,
                    "open_interest": put_risk["open_interest"],
                    "reinforcement": put_risk["reinforcement"]
                })
            
            # Sort by danger score
            battle_zones.sort(key=lambda x: x["danger_score"], reverse=True)
            
            # STEP 5: GENERATE TRADING SIGNALS
            signals = []
            
            # Immediate threats
            for zone in battle_zones:
                if zone["urgency"] == "IMMEDIATE":
                    if zone["type"] == "CALL DEFENSE":
                        signals.append(f"STRONG SUPPORT expected at {zone['strike']}")
                    else:
                        signals.append(f"STRONG RESISTANCE expected at {zone['strike']}")
            
            # Directional bias
            if nearest_call_threat and nearest_put_threat:
                if nearest_call_threat["distance"] < nearest_put_threat["distance"]:
                    signals.append("UPWARD BIAS - Calls closer to danger")
                else:
                    signals.append("DOWNWARD BIAS - Puts closer to danger")
            
            # Risk concentration signals
            if len(battle_zones) > 0:
                top_zone = battle_zones[0]
                signals.append(f"CRITICAL BATTLE ZONE: {top_zone['strike']} ({top_zone['type']}) - ${top_zone['risk_amount']:,.0f} at risk")
            
            # Calculate metrics
            total_positions = len(calls_at_risk) + len(puts_at_risk)
            immediate_threats = len([z for z in battle_zones if z["urgency"] == "IMMEDIATE"])
            
            return {
                "status": "success",
                "underlying_price": underlying_price,
                "summary": {
                    "total_call_risk": total_call_risk,
                    "total_put_risk": total_put_risk,
                    "risk_ratio": risk_ratio,
                    "verdict": verdict,
                    "bias": bias
                },
                "threats": {
                    "nearest_call_threat": nearest_call_threat,
                    "nearest_put_threat": nearest_put_threat
                },
                "battle_zones": battle_zones[:5],  # Top 5 critical zones
                "signals": signals,
                "metrics": {
                    "total_positions_at_risk": total_positions,
                    "call_positions_at_risk": len(calls_at_risk),
                    "put_positions_at_risk": len(puts_at_risk),
                    "immediate_threats": immediate_threats,
                    "total_risk_exposure": total_call_risk + total_put_risk
                },
                "timestamp": get_utc_timestamp()
            }
            
        except Exception as e:
            return create_failure_response(f"Risk analysis failed: {str(e)}")


def run_risk_analysis(data_config: Dict[str, Any], analysis_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Run options risk analysis
    
    Args:
        data_config: Configuration with normalized data
        analysis_config: Risk analysis configuration
        
    Returns:
        Dict with risk analysis results
    """
    if analysis_config is None:
        analysis_config = {
            "multiplier": 20,
            "immediate_threat_distance": 10,
            "near_term_distance": 25,
            "medium_term_distance": 50
        }
    
    analyzer = RiskAnalyzer(analysis_config)
    return analyzer.analyze_risk(data_config)


if __name__ == "__main__":
    # Test configuration
    test_config = {
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
                }
            ]
        }
    }
    
    result = run_risk_analysis(test_config)
    print("Risk Analysis Result:", result)
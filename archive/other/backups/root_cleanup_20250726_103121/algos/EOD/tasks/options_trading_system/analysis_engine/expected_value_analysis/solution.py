#!/usr/bin/env python3
"""
TASK: expected_value_analysis
TYPE: Leaf Task
PURPOSE: NQ Options Expected Value Analysis using actual algorithm from nq_options_ev_algo.py
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Add parent task to path for data access
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, parent_dir)
from data_ingestion.integration import run_data_ingestion

# Add project root for test_utils
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)
from tasks.test_utils import estimate_underlying_price


# Configuration from your actual algorithm
WEIGHTS = {
    'oi_factor': 0.35,
    'vol_factor': 0.25,
    'pcr_factor': 0.25,
    'distance_factor': 0.15
}

# Quality thresholds from your actual algorithm
MIN_EV = 15
MIN_PROBABILITY = 0.60
MAX_RISK = 150
MIN_RISK_REWARD = 1.0


class OptionsStrike:
    """Represents a single options strike with call and put data (from your algorithm)"""
    def __init__(self, price: float, call_volume: int, call_oi: int, call_premium: float,
                 put_volume: int, put_oi: int, put_premium: float):
        self.price = price
        self.call_volume = call_volume
        self.call_oi = call_oi
        self.call_premium = call_premium
        self.put_volume = put_volume
        self.put_oi = put_oi
        self.put_premium = put_premium


class TradeSetup:
    """Represents a potential trade setup with calculated metrics (from your algorithm)"""
    def __init__(self, tp: float, sl: float, direction: str, probability: float,
                 reward: float, risk: float, ev: float):
        self.tp = tp
        self.sl = sl
        self.direction = direction
        self.probability = probability
        self.reward = reward
        self.risk = risk
        self.ev = ev
        self.risk_reward = reward / risk if risk > 0 else 0


class ExpectedValueAnalyzer:
    """NQ Options Expected Value Analyzer using your actual algorithm"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with analysis configuration
        
        Args:
            config: Configuration containing weights and thresholds
        """
        self.config = config
        
        # Use your algorithm's configuration with fallback to defaults
        self.weights = config.get("weights", WEIGHTS)
        self.min_ev = config.get("min_ev", MIN_EV)
        self.min_probability = config.get("min_probability", MIN_PROBABILITY)
        self.max_risk = config.get("max_risk", MAX_RISK)
        self.min_risk_reward = config.get("min_risk_reward", MIN_RISK_REWARD)
        
        self.data = None
        self.analysis_results = None
        
    def load_normalized_data(self, data_config: Dict[str, Any]) -> Dict[str, Any]:
        """Load normalized data from data ingestion pipeline"""
        pipeline_result = run_data_ingestion(data_config)
        
        if pipeline_result["pipeline_status"] != "success":
            raise ValueError("Data ingestion pipeline failed")
        
        self.data = {
            "contracts": pipeline_result["normalized_data"]["contracts"],
            "summary": pipeline_result["normalized_data"]["summary"],
            "quality": pipeline_result["quality_metrics"],
            "underlying_price": self._estimate_underlying_price(pipeline_result["normalized_data"]["contracts"])
        }
        
        return self.data
    
    def _estimate_underlying_price(self, contracts: List[Dict]) -> float:
        """Estimate current underlying price from contract data"""
        # Use canonical implementation from test_utils
        return estimate_underlying_price(contracts)
    
    def convert_to_options_strikes(self, contracts: List[Dict]) -> List[OptionsStrike]:
        """Convert normalized contract data to OptionsStrike objects"""
        strikes_dict = {}
        
        # Group contracts by strike price
        for contract in contracts:
            strike = contract.get("strike")
            if not strike or strike <= 0:
                continue
                
            if strike not in strikes_dict:
                strikes_dict[strike] = {
                    "call_volume": 0, "call_oi": 0, "call_premium": 0,
                    "put_volume": 0, "put_oi": 0, "put_premium": 0
                }
            
            contract_type = contract.get("type", "").lower()
            volume = contract.get("volume") or 0
            oi = contract.get("open_interest") or 0
            premium = contract.get("last_price") or 0
            
            if contract_type == "call":
                strikes_dict[strike]["call_volume"] = volume
                strikes_dict[strike]["call_oi"] = oi
                strikes_dict[strike]["call_premium"] = premium
            elif contract_type == "put":
                strikes_dict[strike]["put_volume"] = volume
                strikes_dict[strike]["put_oi"] = oi
                strikes_dict[strike]["put_premium"] = premium
        
        # Convert to OptionsStrike objects
        strikes = []
        for price, data in strikes_dict.items():
            strikes.append(OptionsStrike(
                price,
                data["call_volume"], data["call_oi"], data["call_premium"],
                data["put_volume"], data["put_oi"], data["put_premium"]
            ))
        
        return strikes
    
    def get_distance_weight(self, distance_pct: float) -> float:
        """Get weight based on distance from current price (from your algorithm)"""
        distance_pct = abs(distance_pct)
        
        if distance_pct <= 0.01:
            return 1.0
        elif distance_pct <= 0.02:
            return 0.8
        elif distance_pct <= 0.05:
            return 0.5
        else:
            return 0.2
    
    def calculate_probability(self, current_price: float, tp: float, sl: float, 
                             strikes: List[OptionsStrike], direction: str) -> float:
        """Calculate probability of reaching TP before SL (from your algorithm)"""
        
        # Calculate factors
        oi_factor = 0
        vol_factor = 0
        
        max_oi = max([s.call_oi + s.put_oi for s in strikes]) if strikes else 1
        max_vol = max([s.call_volume + s.put_volume for s in strikes]) if strikes else 1
        
        total_call_premium = sum([s.call_premium * s.call_oi for s in strikes])
        total_put_premium = sum([s.put_premium * s.put_oi for s in strikes])
        
        for strike in strikes:
            distance_pct = (strike.price - current_price) / current_price
            distance_weight = self.get_distance_weight(distance_pct)
            
            # Determine if strike supports direction
            if direction == 'long':
                direction_modifier = 1 if strike.price > current_price else -0.5
            else:
                direction_modifier = 1 if strike.price < current_price else -0.5
            
            # OI Factor
            strike_oi = strike.call_oi + strike.put_oi
            oi_contribution = (strike_oi * distance_weight * direction_modifier) / max_oi
            oi_factor += oi_contribution
            
            # Volume Factor
            strike_vol = strike.call_volume + strike.put_volume
            vol_contribution = (strike_vol * distance_weight * direction_modifier) / max_vol
            vol_factor += vol_contribution
        
        # PCR Factor
        pcr_factor = 0
        if total_call_premium + total_put_premium > 0:
            pcr_factor = (total_call_premium - total_put_premium) / (total_call_premium + total_put_premium)
            if direction == 'short':
                pcr_factor = -pcr_factor
        
        # Distance Factor
        distance_factor = 1 - (abs(current_price - tp) / current_price)
        
        # Normalize factors
        oi_factor = max(0, min(1, oi_factor))
        vol_factor = max(0, min(1, vol_factor))
        pcr_factor = (pcr_factor + 1) / 2  # Convert from [-1, 1] to [0, 1]
        distance_factor = max(0, min(1, distance_factor))
        
        # Calculate weighted probability (from your algorithm)
        probability = (
            self.weights['oi_factor'] * oi_factor +
            self.weights['vol_factor'] * vol_factor +
            self.weights['pcr_factor'] * pcr_factor +
            self.weights['distance_factor'] * distance_factor
        )
        
        # Clamp between 10% and 90%
        probability = max(0.1, min(0.9, probability))
        
        return probability
    
    def calculate_ev_combinations(self, current_price: float, 
                                 strikes: List[OptionsStrike]) -> List[TradeSetup]:
        """Calculate EV for all valid TP/SL combinations (from your algorithm)"""
        
        setups = []
        
        # Get all strike prices
        strike_prices = sorted([s.price for s in strikes])
        
        if not strike_prices:
            return setups
        
        # Test all combinations
        for tp in strike_prices:
            for sl in strike_prices:
                # Long setup
                if tp > current_price > sl:
                    reward = tp - current_price
                    risk = current_price - sl
                    
                    if risk <= self.max_risk and reward / risk >= self.min_risk_reward:
                        prob = self.calculate_probability(current_price, tp, sl, strikes, 'long')
                        ev = (prob * reward) - ((1 - prob) * risk)
                        
                        setup = TradeSetup(tp, sl, 'long', prob, reward, risk, ev)
                        setups.append(setup)
                
                # Short setup
                elif tp < current_price < sl:
                    reward = current_price - tp
                    risk = sl - current_price
                    
                    if risk <= self.max_risk and reward / risk >= self.min_risk_reward:
                        prob = self.calculate_probability(current_price, tp, sl, strikes, 'short')
                        ev = (prob * reward) - ((1 - prob) * risk)
                        
                        setup = TradeSetup(tp, sl, 'short', prob, reward, risk, ev)
                        setups.append(setup)
        
        # Sort by EV
        setups.sort(key=lambda x: x.ev, reverse=True)
        return setups
    
    def filter_quality_setups(self, setups: List[TradeSetup]) -> List[TradeSetup]:
        """Filter setups by quality criteria (from your algorithm)"""
        
        quality_setups = []
        
        for setup in setups:
            if (setup.ev >= self.min_ev and 
                setup.probability >= self.min_probability and 
                setup.risk <= self.max_risk and 
                setup.risk_reward >= self.min_risk_reward):
                quality_setups.append(setup)
        
        return quality_setups
    
    def generate_trading_report(self, current_price: float, setups: List[TradeSetup]) -> Dict[str, Any]:
        """Generate trading report (adapted from your algorithm)"""
        
        report_data = {
            "timestamp": get_utc_timestamp(),
            "current_nq_price": current_price,
            "total_setups": len(setups),
            "top_opportunities": [],
            "execution_recommendation": None
        }
        
        # Top 5 opportunities
        for i, setup in enumerate(setups[:5], 1):
            opportunity = {
                "rank": i,
                "direction": setup.direction,
                "tp": setup.tp,
                "sl": setup.sl,
                "probability": setup.probability,
                "risk_reward": setup.risk_reward,
                "expected_value": setup.ev,
                "reward": setup.reward,
                "risk": setup.risk
            }
            report_data["top_opportunities"].append(opportunity)
        
        # Execution recommendation
        if setups:
            best = setups[0]
            position_size = "LARGE (15-20%)" if best.ev > 50 else "MEDIUM (10-15%)" if best.ev > 30 else "SMALL (5-10%)"
            
            report_data["execution_recommendation"] = {
                "trade_direction": best.direction.upper(),
                "entry_price": current_price,
                "target": best.tp,
                "stop": best.sl,
                "position_size": position_size,
                "expected_value": best.ev,
                "reward_points": best.reward,
                "risk_points": -best.risk,
                "probability": best.probability
            }
        
        return report_data
    
    def analyze_expected_value(self, data_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete expected value analysis using your algorithm"""
        
        # Load data
        data = self.load_normalized_data(data_config)
        
        # Convert to OptionsStrike format
        strikes = self.convert_to_options_strikes(data["contracts"])
        
        # Calculate EV for all combinations
        all_setups = self.calculate_ev_combinations(data["underlying_price"], strikes)
        
        # Filter quality setups
        quality_setups = self.filter_quality_setups(all_setups)
        
        # Generate trading report
        trading_report = self.generate_trading_report(data["underlying_price"], quality_setups)
        
        # Results
        self.analysis_results = {
            "timestamp": get_utc_timestamp(),
            "underlying_symbol": "NQ",
            "underlying_price": data["underlying_price"],
            "data_quality": data["quality"],
            "analysis_config": self.config,
            "strikes_analyzed": len(strikes),
            "contracts_analyzed": len(data["contracts"]),
            "setups_generated": len(all_setups),
            "quality_setups": len(quality_setups),
            "trading_report": trading_report,
            "top_setups": [
                {
                    "direction": s.direction,
                    "tp": s.tp,
                    "sl": s.sl,
                    "probability": s.probability,
                    "risk_reward": s.risk_reward,
                    "expected_value": s.ev,
                    "reward": s.reward,
                    "risk": s.risk
                }
                for s in quality_setups[:10]
            ],
            "metrics": {
                "total_strikes": len(strikes),
                "valid_combinations": len(all_setups),
                "quality_ratio": len(quality_setups) / len(all_setups) if all_setups else 0,
                "best_ev": quality_setups[0].ev if quality_setups else 0,
                "avg_probability": sum(s.probability for s in quality_setups) / len(quality_setups) if quality_setups else 0
            }
        }
        
        return self.analysis_results


# Module-level function for easy integration
def analyze_expected_value(data_config: Dict[str, Any], analysis_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze expected value using your actual NQ EV algorithm
    
    Args:
        data_config: Configuration for data sources
        analysis_config: Configuration for EV analysis
        
    Returns:
        Dict with analysis results
    """
    analyzer = ExpectedValueAnalyzer(analysis_config)
    return analyzer.analyze_expected_value(data_config)
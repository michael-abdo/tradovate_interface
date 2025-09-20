#!/usr/bin/env python3
"""
TASK: volume_shock_analysis
TYPE: Leaf Task
PURPOSE: Detect volume anomalies and front-run market maker delta hedging flows

EXPERIMENTAL HYPOTHESIS: Large unexpected options orders create measurable delta 
imbalances that force market makers into predictable hedging behavior within 
2-10 minutes, generating tradeable opportunities with 80-90% win rate.

STRATEGY: "The Egg Rush Strategy" - Position ahead of forced hedging flow when
market makers must buy/sell futures to maintain delta neutrality after large
options orders create instant imbalances.
"""

import sys
import os
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import math

# Add tasks directory to path for common utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from common_utils import create_success_response, create_failure_response, create_status_response, get_utc_timestamp

# Add parent directories to path for data access
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, parent_dir)
from data_ingestion.integration import run_data_ingestion

# Add project root for test_utils
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)
from tasks.test_utils import estimate_underlying_price

class FlowType(Enum):
    """Classification of volume shock patterns"""
    INSTITUTIONAL_SWEEP = "INSTITUTIONAL_SWEEP"
    GAMMA_EMERGENCY = "GAMMA_EMERGENCY"
    AMBIGUOUS_SIGNAL = "AMBIGUOUS_SIGNAL"

class HedgeDirection(Enum):
    """Required hedge direction for market makers"""
    BUY_FUTURES = "BUY_FUTURES"
    SELL_FUTURES = "SELL_FUTURES"

@dataclass
class VolumeShockAlert:
    """Volume shock detection with hedging flow prediction"""
    strike: float
    flow_type: FlowType
    hedge_direction: HedgeDirection
    delta_exposure: float
    volume_ratio: float
    pressure_score: float
    response_time_estimate: float
    confidence: float
    expected_magnitude_points: float
    urgency_level: str
    reasoning: str
    timestamp: datetime
    
    # Validation tracking
    validation_id: str
    detection_latency_ms: float

@dataclass
class VolumeShockAnalysisResult:
    """Complete volume shock analysis with trading signals"""
    alerts: List[VolumeShockAlert]
    market_context: Dict[str, Any]
    flow_classification_summary: Dict[str, Any]
    execution_recommendations: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    validation_framework: Dict[str, Any]


class VolumeShockDetectionEngine:
    """
    EXPERIMENTAL FRAMEWORK: Real-time detection of volume anomalies
    with delta exposure calculations and hedging flow predictions
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize volume shock detection engine
        
        Args:
            config: Configuration including thresholds and validation settings
        """
        self.config = config
        
        # Detection thresholds from strategy documentation
        self.VOLUME_RATIO_THRESHOLD = config.get("volume_ratio_threshold", 4.0)
        self.MIN_VOLUME_THRESHOLD = config.get("min_volume_threshold", 100)
        self.PRESSURE_THRESHOLD = config.get("pressure_threshold", 50.0)
        self.HIGH_DELTA_THRESHOLD = config.get("high_delta_threshold", 3000)
        self.EMERGENCY_DELTA_THRESHOLD = config.get("emergency_delta_threshold", 5000)
        
        # Historical baselines (mock for now - would be real historical data)
        self.volume_baselines = {}
        self.detection_history = []
        
        # Validation framework
        self.validation_mode = config.get("validation_mode", True)
        self.detection_accuracy_tracker = []
        
    def detect_volume_shocks(self, options_data: Dict[str, Any]) -> List[VolumeShockAlert]:
        """
        CORE DETECTION ALGORITHM: Identify volume anomalies and predict hedging flows
        
        Implementation of "The Egg Rush Strategy" detection system:
        1. Detect volume anomalies (>4x baseline + >100 contracts)
        2. Calculate net delta exposure created
        3. Estimate market maker response time based on exposure magnitude
        4. Calculate pressure score: Delta Exposure / Response Time²
        5. Classify flow type and predict hedging direction
        
        Args:
            options_data: Real-time options chain data
            
        Returns:
            List of volume shock alerts ranked by pressure score
        """
        detection_start_time = time.time()
        volume_alerts = []
        
        # Extract options contracts
        contracts = options_data.get("contracts", [])
        if not contracts:
            return []
        
        # Calculate underlying price for context
        underlying_price = self._estimate_underlying_price(contracts)
        
        # Analyze each strike for volume anomalies
        for contract in contracts:
            strike = contract.get("strike", 0)
            if strike == 0:
                continue
                
            # Calculate recent volume (mock 5-minute window)
            recent_call_volume = contract.get("call_volume", 0) or 0
            recent_put_volume = contract.get("put_volume", 0) or 0
            total_recent_volume = recent_call_volume + recent_put_volume
            
            # Calculate historical baseline (mock - would use real 10-day average)
            historical_baseline = self._get_volume_baseline(strike)
            
            # Volume anomaly detection
            volume_ratio = total_recent_volume / max(historical_baseline, 1)
            
            # Check if this qualifies as a volume shock
            if volume_ratio > self.VOLUME_RATIO_THRESHOLD and total_recent_volume > self.MIN_VOLUME_THRESHOLD:
                
                # Calculate net delta exposure
                net_delta_exposure = self._calculate_net_delta_exposure(
                    contract, recent_call_volume, recent_put_volume
                )
                
                # Estimate market maker response time
                response_time_estimate = self._estimate_mm_response_time(net_delta_exposure)
                
                # Calculate pressure score: Delta Exposure / Time²
                pressure_score = abs(net_delta_exposure) / max(1, response_time_estimate ** 2)
                
                if pressure_score > self.PRESSURE_THRESHOLD:
                    # Generate volume shock alert
                    alert = self._generate_volume_shock_alert(
                        strike=strike,
                        contract=contract,
                        volume_ratio=volume_ratio,
                        net_delta_exposure=net_delta_exposure,
                        pressure_score=pressure_score,
                        response_time_estimate=response_time_estimate,
                        underlying_price=underlying_price,
                        detection_start_time=detection_start_time
                    )
                    
                    volume_alerts.append(alert)
        
        # Rank alerts by pressure score (highest first)
        volume_alerts.sort(key=lambda x: x.pressure_score, reverse=True)
        
        # Record detection latency
        detection_latency = (time.time() - detection_start_time) * 1000  # ms
        
        return volume_alerts
    
    def _calculate_net_delta_exposure(self, contract: Dict[str, Any], 
                                    call_volume: int, put_volume: int) -> float:
        """
        Calculate net delta exposure created by recent volume
        
        VALIDATION REQUIREMENT: Track correlation between calculated delta
        and observed futures hedging volume
        
        Formula:
        - Call Delta Exposure = Call Volume × Call Delta × 100 (shares per contract)
        - Put Delta Exposure = Put Volume × Put Delta × -100 (puts are negative delta)
        - Net Delta = Call Delta Exposure + Put Delta Exposure
        """
        
        # Get deltas (estimated if not available)
        call_delta = contract.get("call_delta")
        put_delta = contract.get("put_delta")
        
        if call_delta is None or put_delta is None:
            # Estimate deltas based on moneyness
            strike = contract.get("strike", 0)
            underlying_price = contract.get("underlying_price", 21000)
            call_delta, put_delta = self._estimate_deltas(strike, underlying_price)
        
        # Calculate exposures
        call_delta_exposure = call_volume * call_delta * 100  # 100 shares per contract
        put_delta_exposure = put_volume * put_delta * -100   # Puts negative delta
        
        net_delta = call_delta_exposure + put_delta_exposure
        
        return net_delta
    
    def _estimate_mm_response_time(self, delta_exposure: float) -> float:
        """
        Estimate market maker response time based on delta exposure magnitude
        
        EMPIRICALLY DERIVED thresholds from strategy documentation:
        - >5000 delta: 2 minutes (emergency response)
        - >2000 delta: 5 minutes (urgent response)
        - else: 10 minutes (routine response)
        """
        abs_exposure = abs(delta_exposure)
        
        if abs_exposure > self.EMERGENCY_DELTA_THRESHOLD:
            return 2.0  # Emergency response
        elif abs_exposure > self.HIGH_DELTA_THRESHOLD:
            return 5.0  # Urgent response
        else:
            return 10.0  # Routine response
    
    def _generate_volume_shock_alert(self, strike: float, contract: Dict[str, Any],
                                   volume_ratio: float, net_delta_exposure: float,
                                   pressure_score: float, response_time_estimate: float,
                                   underlying_price: float, detection_start_time: float) -> VolumeShockAlert:
        """Generate comprehensive volume shock alert with flow classification"""
        
        # Determine hedge direction
        hedge_direction = HedgeDirection.BUY_FUTURES if net_delta_exposure > 0 else HedgeDirection.SELL_FUTURES
        
        # Classify flow type
        flow_type, urgency_level = self._classify_flow_type(
            volume_ratio, net_delta_exposure, response_time_estimate, contract
        )
        
        # Calculate confidence based on signal strength
        confidence = min(0.95, volume_ratio / 10.0)
        
        # Estimate expected price movement magnitude
        expected_magnitude = self._estimate_price_movement_magnitude(
            flow_type, net_delta_exposure, confidence
        )
        
        # Generate reasoning
        reasoning = self._generate_alert_reasoning(
            flow_type, hedge_direction, net_delta_exposure, volume_ratio, response_time_estimate
        )
        
        # Create validation ID for tracking
        validation_id = f"vs_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{strike}"
        
        # Calculate detection latency
        detection_latency = (time.time() - detection_start_time) * 1000
        
        return VolumeShockAlert(
            strike=strike,
            flow_type=flow_type,
            hedge_direction=hedge_direction,
            delta_exposure=net_delta_exposure,
            volume_ratio=volume_ratio,
            pressure_score=pressure_score,
            response_time_estimate=response_time_estimate,
            confidence=confidence,
            expected_magnitude_points=expected_magnitude,
            urgency_level=urgency_level,
            reasoning=reasoning,
            timestamp=datetime.now(),
            validation_id=validation_id,
            detection_latency_ms=detection_latency
        )
    
    def _classify_flow_type(self, volume_ratio: float, delta_exposure: float, 
                           response_time: float, contract: Dict[str, Any]) -> Tuple[FlowType, str]:
        """
        Classify volume pattern as institutional sweep vs gamma emergency
        
        INSTITUTIONAL_SWEEP: Multiple strikes, gradual hedging, 5-15min response
        GAMMA_EMERGENCY: Single strike concentration, immediate hedging, 1-5min response
        """
        
        abs_exposure = abs(delta_exposure)
        
        # Gamma Emergency criteria
        if (volume_ratio > 8.0 and 
            abs_exposure > self.HIGH_DELTA_THRESHOLD and 
            response_time < 5):
            return FlowType.GAMMA_EMERGENCY, "HIGH"
        
        # Institutional Sweep criteria  
        elif (volume_ratio > 3.0 and 
              abs_exposure > 1000 and 
              response_time >= 5):
            return FlowType.INSTITUTIONAL_SWEEP, "LOW"
        
        # Ambiguous signal
        else:
            return FlowType.AMBIGUOUS_SIGNAL, "UNKNOWN"
    
    def _estimate_price_movement_magnitude(self, flow_type: FlowType, 
                                         delta_exposure: float, confidence: float) -> float:
        """
        Estimate expected price movement based on flow type and exposure
        
        From strategy documentation:
        - Institutional Sweep: 8-15 points average
        - Gamma Emergency: 15-30 points average
        """
        
        base_magnitude = min(25, abs(delta_exposure) / 200)  # Empirically derived
        
        if flow_type == FlowType.GAMMA_EMERGENCY:
            return base_magnitude * 1.5 * confidence  # 15-30 points range
        elif flow_type == FlowType.INSTITUTIONAL_SWEEP:
            return base_magnitude * confidence        # 8-15 points range
        else:
            return base_magnitude * 0.5 * confidence  # Lower for ambiguous
    
    def _generate_alert_reasoning(self, flow_type: FlowType, hedge_direction: HedgeDirection,
                                delta_exposure: float, volume_ratio: float, 
                                response_time: float) -> str:
        """Generate human-readable reasoning for the alert"""
        
        direction_text = "buy futures" if hedge_direction == HedgeDirection.BUY_FUTURES else "sell futures"
        
        if flow_type == FlowType.GAMMA_EMERGENCY:
            return (f"GAMMA EMERGENCY: {volume_ratio:.1f}x volume spike created "
                   f"{delta_exposure:,.0f} delta exposure. Market makers must {direction_text} "
                   f"within {response_time:.0f} minutes to hedge position. High urgency = higher profit potential.")
        
        elif flow_type == FlowType.INSTITUTIONAL_SWEEP:
            return (f"INSTITUTIONAL SWEEP: {volume_ratio:.1f}x volume surge indicates "
                   f"large order flow creating {delta_exposure:,.0f} delta imbalance. "
                   f"Systematic hedging expected via {direction_text} over {response_time:.0f} minute window.")
        
        else:
            return (f"VOLUME ANOMALY: {volume_ratio:.1f}x normal volume but unclear flow pattern. "
                   f"Delta exposure {delta_exposure:,.0f} suggests {direction_text} hedging needed.")
    
    def _get_volume_baseline(self, strike: float) -> float:
        """
        Get historical volume baseline for strike
        
        Mock implementation - in production would use 10-day rolling average
        """
        # Mock baseline based on strike distance from ATM
        base_volume = 50  # Base daily volume
        
        # Adjust based on moneyness (ATM options have higher volume)
        estimated_underlying = 21000  # Mock current price
        distance_from_atm = abs(strike - estimated_underlying)
        volume_decay = max(0.1, 1.0 - (distance_from_atm / 1000.0))
        
        return base_volume * volume_decay
    
    def _estimate_underlying_price(self, contracts: List[Dict[str, Any]]) -> float:
        """Estimate underlying price from options data"""
        # Use canonical implementation from test_utils
        return estimate_underlying_price(contracts)
    
    def _estimate_deltas(self, strike: float, underlying_price: float) -> Tuple[float, float]:
        """
        Estimate call and put deltas based on moneyness
        
        Simplified Black-Scholes approximation for delta estimation
        """
        moneyness = underlying_price / strike
        
        # Simplified delta approximation
        if moneyness > 1.1:  # Deep ITM call
            call_delta = 0.8
            put_delta = -0.2
        elif moneyness > 1.05:  # ITM call
            call_delta = 0.65
            put_delta = -0.35
        elif moneyness > 0.95:  # ATM
            call_delta = 0.5
            put_delta = -0.5
        elif moneyness > 0.9:  # OTM call
            call_delta = 0.3
            put_delta = -0.7
        else:  # Deep OTM call
            call_delta = 0.15
            put_delta = -0.85
        
        return call_delta, put_delta


class VolumeShockAnalysisEngine:
    """
    Main volume shock analysis engine coordinating detection, classification,
    and trading signal generation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize volume shock analysis engine
        
        Args:
            config: Configuration for volume shock detection and analysis
        """
        self.config = config
        self.detection_engine = VolumeShockDetectionEngine(config)
        
    def analyze_volume_shocks(self, options_data: Dict[str, Any]) -> VolumeShockAnalysisResult:
        """
        Complete volume shock analysis with trading recommendations
        
        EXPERIMENTAL FRAMEWORK: Detect volume anomalies, classify flow types,
        and generate executable trading signals for front-running market maker hedging
        
        Args:
            options_data: Real-time options chain data
            
        Returns:
            Complete analysis with alerts, classifications, and trading signals
        """
        
        analysis_start_time = datetime.now()
        
        # Step 1: Detect volume shocks
        volume_alerts = self.detection_engine.detect_volume_shocks(options_data)
        
        # Step 2: Analyze market context
        market_context = self._analyze_market_context(options_data, volume_alerts)
        
        # Step 3: Generate flow classification summary
        flow_summary = self._generate_flow_classification_summary(volume_alerts)
        
        # Step 4: Create execution recommendations
        execution_recs = self._generate_execution_recommendations(volume_alerts, market_context)
        
        # Step 5: Assess risks
        risk_assessment = self._assess_volume_shock_risks(volume_alerts, market_context)
        
        # Step 6: Calculate performance metrics
        performance_metrics = self._calculate_analysis_metrics(
            volume_alerts, analysis_start_time
        )
        
        # Step 7: Setup validation framework
        validation_framework = self._setup_validation_framework(volume_alerts)
        
        return VolumeShockAnalysisResult(
            alerts=volume_alerts,
            market_context=market_context,
            flow_classification_summary=flow_summary,
            execution_recommendations=execution_recs,
            risk_assessment=risk_assessment,
            performance_metrics=performance_metrics,
            validation_framework=validation_framework
        )
    
    def _analyze_market_context(self, options_data: Dict[str, Any], 
                               alerts: List[VolumeShockAlert]) -> Dict[str, Any]:
        """Analyze current market conditions affecting volume shock strategy"""
        
        # Extract market data
        underlying_symbol = options_data.get("underlying_symbol", "NQ")
        underlying_price = options_data.get("underlying_price", 21000)
        total_contracts = len(options_data.get("contracts", []))
        
        # Calculate alert intensity
        total_alerts = len(alerts)
        high_urgency_alerts = len([a for a in alerts if a.urgency_level == "HIGH"])
        avg_pressure = statistics.mean([a.pressure_score for a in alerts]) if alerts else 0
        
        return {
            "underlying_symbol": underlying_symbol,
            "underlying_price": underlying_price,
            "market_timestamp": get_utc_timestamp(),
            "total_strikes_analyzed": total_contracts,
            "volume_shock_intensity": {
                "total_alerts": total_alerts,
                "high_urgency_alerts": high_urgency_alerts,
                "average_pressure_score": avg_pressure,
                "market_stress_level": "HIGH" if high_urgency_alerts > 2 else "NORMAL"
            },
            "optimal_trading_window": self._calculate_optimal_trading_window(alerts)
        }
    
    def _generate_flow_classification_summary(self, alerts: List[VolumeShockAlert]) -> Dict[str, Any]:
        """Generate summary of detected flow patterns"""
        
        flow_counts = {
            "institutional_sweeps": len([a for a in alerts if a.flow_type == FlowType.INSTITUTIONAL_SWEEP]),
            "gamma_emergencies": len([a for a in alerts if a.flow_type == FlowType.GAMMA_EMERGENCY]),
            "ambiguous_signals": len([a for a in alerts if a.flow_type == FlowType.AMBIGUOUS_SIGNAL])
        }
        
        # Calculate dominant flow pattern
        if flow_counts["gamma_emergencies"] > 0:
            dominant_pattern = "GAMMA_EMERGENCY_DOMINANT"
            market_behavior = "High volatility, immediate hedging pressure"
        elif flow_counts["institutional_sweeps"] > flow_counts["ambiguous_signals"]:
            dominant_pattern = "INSTITUTIONAL_SWEEP_DOMINANT"
            market_behavior = "Systematic large order flow, methodical hedging"
        else:
            dominant_pattern = "MIXED_OR_UNCLEAR"
            market_behavior = "No clear dominant pattern"
        
        return {
            "flow_type_counts": flow_counts,
            "dominant_pattern": dominant_pattern,
            "market_behavior_assessment": market_behavior,
            "total_detections": sum(flow_counts.values()),
            "confidence_distribution": {
                "high_confidence": len([a for a in alerts if a.confidence > 0.8]),
                "medium_confidence": len([a for a in alerts if 0.6 <= a.confidence <= 0.8]),
                "low_confidence": len([a for a in alerts if a.confidence < 0.6])
            }
        }
    
    def _generate_execution_recommendations(self, alerts: List[VolumeShockAlert], 
                                          market_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate executable trading recommendations based on volume shock alerts
        
        Implementation of execution logic from strategy documentation
        """
        
        recommendations = []
        
        # Process top 3 alerts (ranked by pressure score)
        top_alerts = alerts[:3]
        
        for i, alert in enumerate(top_alerts):
            
            # Calculate position size based on flow type and confidence
            position_size = self._calculate_position_size(alert)
            
            # Determine entry, target, and stop prices
            current_price = market_context["underlying_price"]
            target_price, stop_price = self._calculate_trade_levels(alert, current_price)
            
            # Calculate time limits
            max_hold_time = self._calculate_max_hold_time(alert)
            
            # Generate recommendation
            recommendation = {
                "signal_id": f"vs_{alert.validation_id}_{i+1}",
                "priority": "PRIMARY" if i == 0 else "SECONDARY",
                "alert_source": alert.validation_id,
                "trade_direction": alert.hedge_direction.value,
                "entry_price": current_price,
                "target_price": target_price,
                "stop_price": stop_price,
                "position_size": position_size,
                "max_hold_time_minutes": max_hold_time,
                "confidence": alert.confidence,
                "expected_value": self._calculate_expected_value(alert, target_price, stop_price, current_price),
                "flow_type": alert.flow_type.value,
                "reasoning": alert.reasoning,
                "execution_urgency": alert.urgency_level,
                "risk_reward_ratio": self._calculate_risk_reward_ratio(
                    current_price, target_price, stop_price, alert.hedge_direction
                )
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_position_size(self, alert: VolumeShockAlert) -> float:
        """Calculate position size based on flow type and confidence"""
        
        base_size = 2.0  # contracts
        
        # Flow type multipliers from strategy documentation
        flow_multipliers = {
            FlowType.INSTITUTIONAL_SWEEP: 1.2,  # 75-85% win rate
            FlowType.GAMMA_EMERGENCY: 2.0,      # 85-95% win rate
            FlowType.AMBIGUOUS_SIGNAL: 0.5      # Lower confidence
        }
        
        # Delta exposure adjustment
        delta_multiplier = min(2.0, abs(alert.delta_exposure) / 2000)
        
        position_size = (base_size * 
                        alert.confidence * 
                        flow_multipliers.get(alert.flow_type, 0.5) * 
                        delta_multiplier)
        
        # Maximum position limit
        return min(position_size, 6.0)
    
    def _calculate_trade_levels(self, alert: VolumeShockAlert, 
                               current_price: float) -> Tuple[float, float]:
        """Calculate target and stop prices based on flow type"""
        
        # Target distance based on expected magnitude
        target_distance = alert.expected_magnitude_points
        
        # Stop distance based on urgency (tighter for high urgency)
        stop_distance = 8 if alert.urgency_level == "HIGH" else 12
        
        if alert.hedge_direction == HedgeDirection.BUY_FUTURES:
            target_price = current_price + target_distance
            stop_price = current_price - stop_distance
        else:  # SELL_FUTURES
            target_price = current_price - target_distance
            stop_price = current_price + stop_distance
        
        return target_price, stop_price
    
    def _calculate_max_hold_time(self, alert: VolumeShockAlert) -> float:
        """Calculate maximum hold time based on flow type"""
        
        # Time limits from strategy documentation
        time_limits = {
            FlowType.GAMMA_EMERGENCY: 8,     # 3-8 minutes
            FlowType.INSTITUTIONAL_SWEEP: 15, # 8-15 minutes
            FlowType.AMBIGUOUS_SIGNAL: 10    # Conservative limit
        }
        
        base_time = time_limits.get(alert.flow_type, 10)
        
        # Add buffer for response time estimate
        return base_time + 3  # 3-minute buffer
    
    def _calculate_expected_value(self, alert: VolumeShockAlert, target: float, 
                                 stop: float, entry: float) -> float:
        """Calculate expected value of the trade"""
        
        # Expected win rates from strategy documentation
        win_rates = {
            FlowType.GAMMA_EMERGENCY: 0.90,     # 85-95%
            FlowType.INSTITUTIONAL_SWEEP: 0.80, # 75-85%
            FlowType.AMBIGUOUS_SIGNAL: 0.60     # Conservative estimate
        }
        
        win_rate = win_rates.get(alert.flow_type, 0.60) * alert.confidence
        
        # Calculate potential profit/loss
        if alert.hedge_direction == HedgeDirection.BUY_FUTURES:
            potential_profit = target - entry
            potential_loss = entry - stop
        else:
            potential_profit = entry - target
            potential_loss = stop - entry
        
        expected_value = (win_rate * potential_profit) - ((1 - win_rate) * potential_loss)
        
        return expected_value
    
    def _calculate_risk_reward_ratio(self, entry: float, target: float, 
                                   stop: float, direction: HedgeDirection) -> float:
        """Calculate risk/reward ratio"""
        
        if direction == HedgeDirection.BUY_FUTURES:
            reward = target - entry
            risk = entry - stop
        else:
            reward = entry - target
            risk = stop - entry
        
        return reward / max(risk, 1) if risk > 0 else 0
    
    def _assess_volume_shock_risks(self, alerts: List[VolumeShockAlert], 
                                  market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risks specific to volume shock strategy"""
        
        # Calculate aggregate exposure
        total_delta_exposure = sum(abs(alert.delta_exposure) for alert in alerts)
        max_single_exposure = max([abs(alert.delta_exposure) for alert in alerts], default=0)
        
        # Assess market stress level
        stress_indicators = {
            "high_urgency_count": len([a for a in alerts if a.urgency_level == "HIGH"]),
            "average_detection_latency": statistics.mean([a.detection_latency_ms for a in alerts]) if alerts else 0,
            "concentration_risk": max_single_exposure / max(total_delta_exposure, 1)
        }
        
        # Risk level assessment
        if stress_indicators["high_urgency_count"] > 2:
            risk_level = "HIGH"
            risk_reason = "Multiple gamma emergencies detected - high market stress"
        elif stress_indicators["average_detection_latency"] > 5000:  # 5 seconds
            risk_level = "MEDIUM"
            risk_reason = "Elevated detection latency may impact execution"
        else:
            risk_level = "LOW"
            risk_reason = "Normal market conditions"
        
        return {
            "risk_level": risk_level,
            "risk_reason": risk_reason,
            "stress_indicators": stress_indicators,
            "total_delta_exposure": total_delta_exposure,
            "max_single_exposure": max_single_exposure,
            "execution_timing_risk": stress_indicators["average_detection_latency"] > 3000,
            "recommended_position_scaling": 1.0 if risk_level == "LOW" else (0.5 if risk_level == "MEDIUM" else 0.25)
        }
    
    def _calculate_analysis_metrics(self, alerts: List[VolumeShockAlert], 
                                   start_time: datetime) -> Dict[str, Any]:
        """Calculate performance metrics for the analysis"""
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "analysis_execution_time_seconds": execution_time,
            "total_volume_shocks_detected": len(alerts),
            "high_confidence_signals": len([a for a in alerts if a.confidence > 0.8]),
            "gamma_emergencies_detected": len([a for a in alerts if a.flow_type == FlowType.GAMMA_EMERGENCY]),
            "institutional_sweeps_detected": len([a for a in alerts if a.flow_type == FlowType.INSTITUTIONAL_SWEEP]),
            "average_pressure_score": statistics.mean([a.pressure_score for a in alerts]) if alerts else 0,
            "average_confidence": statistics.mean([a.confidence for a in alerts]) if alerts else 0,
            "detection_latency_stats": {
                "average_ms": statistics.mean([a.detection_latency_ms for a in alerts]) if alerts else 0,
                "max_ms": max([a.detection_latency_ms for a in alerts], default=0),
                "min_ms": min([a.detection_latency_ms for a in alerts], default=0)
            }
        }
    
    def _setup_validation_framework(self, alerts: List[VolumeShockAlert]) -> Dict[str, Any]:
        """Setup validation framework for tracking prediction accuracy"""
        
        validation_targets = []
        
        for alert in alerts:
            validation_targets.append({
                "validation_id": alert.validation_id,
                "predicted_direction": alert.hedge_direction.value,
                "predicted_magnitude": alert.expected_magnitude_points,
                "predicted_timing": alert.response_time_estimate,
                "flow_classification": alert.flow_type.value,
                "confidence_level": alert.confidence,
                "validation_window_end": (alert.timestamp + timedelta(minutes=alert.response_time_estimate + 5)).isoformat()
            })
        
        return {
            "validation_targets": validation_targets,
            "validation_metrics_to_track": [
                "direction_accuracy",
                "magnitude_error_percentage", 
                "timing_error_minutes",
                "flow_classification_accuracy"
            ],
            "validation_schedule": "Real-time monitoring with 1-hour summary reports",
            "accuracy_targets": {
                "direction_accuracy": 0.80,
                "magnitude_error_threshold": 0.25,  # 25%
                "timing_error_threshold": 3.0       # 3 minutes
            }
        }
    
    def _calculate_optimal_trading_window(self, alerts: List[VolumeShockAlert]) -> Dict[str, Any]:
        """Calculate optimal time window for executing trades"""
        
        if not alerts:
            return create_status_response("no_signals", window=None)
        
        # Find the earliest and latest response times
        min_response_time = min(alert.response_time_estimate for alert in alerts)
        max_response_time = max(alert.response_time_estimate for alert in alerts)
        
        # Optimal window is before the earliest expected hedging
        optimal_window_end = datetime.now() + timedelta(minutes=min_response_time - 1)
        
        return create_status_response(
            "active_window",
            optimal_execution_deadline=optimal_window_end.isoformat(),
            minutes_remaining=min_response_time - 1,
            hedging_window_start=min_response_time,
            hedging_window_end=max_response_time,
            execution_priority="IMMEDIATE" if min_response_time < 3 else "HIGH"
        )


# Module-level function for easy integration
def analyze_volume_shocks(data_config: Dict[str, Any], 
                         analysis_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Analyze volume shocks and generate front-running trading signals
    
    EXPERIMENTAL IMPLEMENTATION: "The Egg Rush Strategy" for exploiting
    market maker delta hedging flows
    
    Args:
        data_config: Configuration for data sources
        analysis_config: Configuration for volume shock analysis (optional)
        
    Returns:
        Dict with volume shock analysis results and trading signals
    """
    if analysis_config is None:
        analysis_config = {
            "volume_ratio_threshold": 4.0,
            "min_volume_threshold": 100,
            "pressure_threshold": 50.0,
            "high_delta_threshold": 2000,
            "emergency_delta_threshold": 5000,
            "validation_mode": True
        }
    
    try:
        # Load options data using data ingestion pipeline
        pipeline_result = run_data_ingestion(data_config)
        options_data = pipeline_result.get("normalized_data", {})
        
        # Initialize analysis engine
        engine = VolumeShockAnalysisEngine(analysis_config)
        
        # Run volume shock analysis
        analysis_result = engine.analyze_volume_shocks(options_data)
        
        # Convert to dictionary format
        result_dict = asdict(analysis_result)
        
        # Add metadata
        result_dict.update({
            "status": "success",
            "timestamp": get_utc_timestamp(),
            "analysis_type": "volume_shock_analysis",
            "strategy": "front_running_market_maker_hedging",
            "config_used": analysis_config
        })
        
        return result_dict
        
    except Exception as e:
        return create_failure_response(
            e,
            analysis_type="volume_shock_analysis"
        )
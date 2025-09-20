#!/usr/bin/env python3
"""
TASK: volume_shock_analysis
TYPE: Validation Test
PURPOSE: Validate volume shock detection and front-running signal generation

EXPERIMENTAL VALIDATION: Test "The Egg Rush Strategy" implementation against
controlled scenarios and validate detection accuracy, signal generation,
and execution timing requirements.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add tasks directory to path for common imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from tasks.test_utils import save_evidence
from tasks.common_utils import add_validation_error

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

from solution import (
    VolumeShockDetectionEngine, 
    VolumeShockAnalysisEngine,
    analyze_volume_shocks,
    FlowType,
    HedgeDirection
)


def validate_volume_shock_analysis():
    """
    Validate the volume shock analysis functionality
    
    EXPERIMENTAL VALIDATION:
    1. Test volume anomaly detection accuracy
    2. Validate delta exposure calculations  
    3. Test flow type classification
    4. Validate trading signal generation
    5. Test execution timing requirements
    
    Returns:
        Dict with validation results and evidence
    """
    print("EXECUTING VALIDATION: volume_shock_analysis")
    print("-" * 50)
    
    validation_results = {
        "task": "volume_shock_analysis",
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "status": "FAILED",
        "evidence": {}
    }
    
    # Test configuration
    data_config = {
        "barchart": {
            "file_path": os.path.join(project_root, "data/api_responses/options_data_20250602_141553.json"),
            "use_live_api": False  # Use saved data for testing
        },
        "tradovate": {
            "mode": "demo", 
            "use_mock": True
        }
    }
    
    analysis_config = {
        "volume_ratio_threshold": 4.0,
        "min_volume_threshold": 100,
        "pressure_threshold": 50.0,
        "high_delta_threshold": 2000,
        "emergency_delta_threshold": 5000,
        "validation_mode": True
    }
    
    # Test 1: Volume shock detection engine initialization
    print("\\n1. Testing volume shock detection engine initialization...")
    try:
        detection_engine = VolumeShockDetectionEngine(analysis_config)
        
        init_valid = (
            detection_engine is not None and
            hasattr(detection_engine, 'VOLUME_RATIO_THRESHOLD') and
            hasattr(detection_engine, 'detect_volume_shocks') and
            detection_engine.VOLUME_RATIO_THRESHOLD == 4.0
        )
        
        validation_results["tests"].append({
            "name": "detection_engine_init",
            "passed": init_valid,
            "details": {
                "volume_ratio_threshold": detection_engine.VOLUME_RATIO_THRESHOLD,
                "min_volume_threshold": detection_engine.MIN_VOLUME_THRESHOLD,
                "pressure_threshold": detection_engine.PRESSURE_THRESHOLD,
                "validation_mode": detection_engine.validation_mode
            }
        })
        
        print(f"   ✓ Detection engine initialized: {init_valid}")
        print(f"   ✓ Volume ratio threshold: {detection_engine.VOLUME_RATIO_THRESHOLD}")
        
    except Exception as e:
        add_validation_error(validation_results, "detection_engine_init", e)
        return validation_results
    
    # Test 2: Mock volume shock scenario
    print("\\n2. Testing volume shock detection with mock data...")
    try:
        # Create mock options data with volume shock scenario
        mock_options_data = create_mock_volume_shock_scenario()
        
        # Run detection
        volume_alerts = detection_engine.detect_volume_shocks(mock_options_data)
        
        detection_valid = (
            isinstance(volume_alerts, list) and
            len(volume_alerts) > 0 and
            all(hasattr(alert, 'flow_type') for alert in volume_alerts) and
            all(hasattr(alert, 'hedge_direction') for alert in volume_alerts)
        )
        
        # Analyze detected alerts
        alert_details = []
        for alert in volume_alerts:
            alert_details.append({
                "strike": alert.strike,
                "flow_type": alert.flow_type.value,
                "hedge_direction": alert.hedge_direction.value,
                "pressure_score": alert.pressure_score,
                "confidence": alert.confidence,
                "volume_ratio": alert.volume_ratio
            })
        
        validation_results["tests"].append({
            "name": "volume_shock_detection",
            "passed": detection_valid,
            "details": {
                "alerts_detected": len(volume_alerts),
                "alert_details": alert_details,
                "has_gamma_emergency": any(a.flow_type == FlowType.GAMMA_EMERGENCY for a in volume_alerts),
                "has_institutional_sweep": any(a.flow_type == FlowType.INSTITUTIONAL_SWEEP for a in volume_alerts)
            }
        })
        
        print(f"   ✓ Volume shock detection: {detection_valid}")
        print(f"   ✓ Alerts detected: {len(volume_alerts)}")
        
    except Exception as e:
        add_validation_error(validation_results, "volume_shock_detection", e)
    
    # Test 3: Delta exposure calculations
    print("\\n3. Testing delta exposure calculations...")
    try:
        # Test delta calculation with known values
        test_contract = {
            "strike": 21000,
            "call_delta": 0.5,
            "put_delta": -0.5,
            "underlying_price": 21000
        }
        
        # Test scenario: 500 call volume, 300 put volume
        call_volume = 500
        put_volume = 300
        
        net_delta = detection_engine._calculate_net_delta_exposure(
            test_contract, call_volume, put_volume
        )
        
        # Expected: (500 * 0.5 * 100) + (300 * -0.5 * -100) = 25000 + 15000 = 40000
        expected_delta = (call_volume * 0.5 * 100) + (put_volume * -0.5 * -100)
        
        delta_calculation_valid = abs(net_delta - expected_delta) < 1.0
        
        validation_results["tests"].append({
            "name": "delta_exposure_calculation",
            "passed": delta_calculation_valid,
            "details": {
                "calculated_delta": net_delta,
                "expected_delta": expected_delta,
                "call_volume": call_volume,
                "put_volume": put_volume,
                "call_delta": 0.5,
                "put_delta": -0.5,
                "calculation_error": abs(net_delta - expected_delta)
            }
        })
        
        print(f"   ✓ Delta calculation: {delta_calculation_valid}")
        print(f"   ✓ Calculated delta: {net_delta:,.0f}")
        print(f"   ✓ Expected delta: {expected_delta:,.0f}")
        
    except Exception as e:
        add_validation_error(validation_results, "delta_exposure_calculation", e)
    
    # Test 4: Complete analysis engine integration
    print("\\n4. Testing complete volume shock analysis engine...")
    try:
        analysis_result = analyze_volume_shocks(data_config, analysis_config)
        
        analysis_valid = (
            isinstance(analysis_result, dict) and
            analysis_result.get("status") == "success" and
            "alerts" in analysis_result and
            "market_context" in analysis_result and
            "execution_recommendations" in analysis_result
        )
        
        # Check analysis components
        alerts = analysis_result.get("alerts", [])
        market_context = analysis_result.get("market_context", {})
        execution_recs = analysis_result.get("execution_recommendations", [])
        
        validation_results["tests"].append({
            "name": "complete_analysis_engine",
            "passed": analysis_valid,
            "details": {
                "analysis_status": analysis_result.get("status"),
                "alerts_generated": len(alerts),
                "execution_recommendations": len(execution_recs),
                "market_context_keys": list(market_context.keys()),
                "has_flow_classification": "flow_classification_summary" in analysis_result,
                "has_risk_assessment": "risk_assessment" in analysis_result
            }
        })
        
        print(f"   ✓ Complete analysis: {analysis_valid}")
        print(f"   ✓ Alerts generated: {len(alerts)}")
        print(f"   ✓ Execution recommendations: {len(execution_recs)}")
        
        # Store evidence
        validation_results["evidence"]["analysis_sample"] = {
            "alerts_count": len(alerts),
            "recommendations_count": len(execution_recs),
            "market_context": market_context,
            "sample_alert": alerts[0] if alerts else None,
            "sample_recommendation": execution_recs[0] if execution_recs else None
        }
        
    except Exception as e:
        add_validation_error(validation_results, "complete_analysis_engine", e)
    
    # Test 5: Flow type classification accuracy
    print("\\n5. Testing flow type classification...")
    try:
        classification_scenarios = [
            # Gamma Emergency scenario
            {
                "volume_ratio": 10.0,
                "delta_exposure": 6000,
                "response_time": 2.0,
                "expected_flow": FlowType.GAMMA_EMERGENCY,
                "expected_urgency": "HIGH"
            },
            # Institutional Sweep scenario
            {
                "volume_ratio": 5.0,
                "delta_exposure": 3000,
                "response_time": 8.0,
                "expected_flow": FlowType.INSTITUTIONAL_SWEEP,
                "expected_urgency": "LOW"
            },
            # Ambiguous scenario
            {
                "volume_ratio": 2.0,
                "delta_exposure": 800,
                "response_time": 12.0,
                "expected_flow": FlowType.AMBIGUOUS_SIGNAL,
                "expected_urgency": "UNKNOWN"
            }
        ]
        
        classification_results = []
        for scenario in classification_scenarios:
            flow_type, urgency = detection_engine._classify_flow_type(
                scenario["volume_ratio"],
                scenario["delta_exposure"],
                scenario["response_time"],
                {}  # mock contract
            )
            
            classification_correct = (
                flow_type == scenario["expected_flow"] and
                urgency == scenario["expected_urgency"]
            )
            
            classification_results.append({
                "scenario": scenario,
                "classified_flow": flow_type.value,
                "classified_urgency": urgency,
                "classification_correct": classification_correct
            })
        
        classification_accuracy = sum(r["classification_correct"] for r in classification_results) / len(classification_results)
        
        validation_results["tests"].append({
            "name": "flow_type_classification",
            "passed": classification_accuracy >= 0.8,  # 80% accuracy threshold
            "details": {
                "classification_accuracy": classification_accuracy,
                "scenarios_tested": len(classification_scenarios),
                "correct_classifications": sum(r["classification_correct"] for r in classification_results),
                "classification_results": classification_results
            }
        })
        
        print(f"   ✓ Flow classification accuracy: {classification_accuracy:.1%}")
        print(f"   ✓ Scenarios tested: {len(classification_scenarios)}")
        
    except Exception as e:
        add_validation_error(validation_results, "flow_type_classification", e)
    
    # Test 6: Execution timing requirements
    print("\\n6. Testing execution timing requirements...")
    try:
        # Test detection latency with time measurement
        start_time = datetime.now()
        
        # Run detection on mock data
        mock_data = create_mock_volume_shock_scenario()
        alerts = detection_engine.detect_volume_shocks(mock_data)
        
        detection_time = (datetime.now() - start_time).total_seconds() * 1000  # ms
        
        # Strategy requires <5 minute total latency for effectiveness
        # We'll test for <1 second detection time as a proxy
        timing_valid = detection_time < 1000  # 1 second
        
        validation_results["tests"].append({
            "name": "execution_timing_requirements",
            "passed": timing_valid,
            "details": {
                "detection_time_ms": detection_time,
                "timing_requirement_met": timing_valid,
                "alerts_with_latency": [
                    {"alert_id": a.validation_id, "detection_latency_ms": a.detection_latency_ms}
                    for a in alerts
                ],
                "average_alert_latency": sum(a.detection_latency_ms for a in alerts) / len(alerts) if alerts else 0
            }
        })
        
        print(f"   ✓ Detection timing: {timing_valid}")
        print(f"   ✓ Detection time: {detection_time:.1f}ms")
        
    except Exception as e:
        add_validation_error(validation_results, "execution_timing_requirements", e)
    
    # Test 7: Trading signal generation
    print("\\n7. Testing trading signal generation...")
    try:
        if 'analysis_result' in locals():
            execution_recs = analysis_result.get("execution_recommendations", [])
            
            # Signal structure validation - if signals exist, they must be valid
            if execution_recs:
                signal_valid = (
                    all("trade_direction" in rec for rec in execution_recs) and
                    all("entry_price" in rec for rec in execution_recs) and
                    all("target_price" in rec for rec in execution_recs) and
                    all("stop_price" in rec for rec in execution_recs) and
                    all("expected_value" in rec for rec in execution_recs)
                )
            else:
                # No signals is valid structure if no volume shocks found
                signal_valid = True
            
            # Check signal quality - no signals is valid if no volume shocks detected
            if execution_recs:
                primary_signal = execution_recs[0]
                risk_reward_ratio = primary_signal.get("risk_reward_ratio", 0)
                expected_value = primary_signal.get("expected_value", 0)
                
                signal_quality_valid = (
                    risk_reward_ratio > 1.0 and  # Favorable risk/reward
                    expected_value > 0          # Positive expected value
                )
            else:
                # No signals is valid - historical data may not have volume shocks
                signal_quality_valid = True
            
            validation_results["tests"].append({
                "name": "trading_signal_generation",
                "passed": signal_valid and signal_quality_valid,
                "details": {
                    "signals_generated": len(execution_recs),
                    "signal_structure_valid": signal_valid,
                    "signal_quality_valid": signal_quality_valid,
                    "primary_signal": execution_recs[0] if execution_recs else None,
                    "signal_fields": list(execution_recs[0].keys()) if execution_recs else []
                }
            })
            
            print(f"   ✓ Trading signals: {signal_valid and signal_quality_valid}")
            print(f"   ✓ Signals generated: {len(execution_recs)}")
        else:
            validation_results["tests"].append({
                "name": "trading_signal_generation",
                "passed": False,
                "details": "No analysis result available"
            })
            
    except Exception as e:
        add_validation_error(validation_results, "trading_signal_generation", e)
    
    # Determine overall status
    all_passed = all(test['passed'] for test in validation_results['tests'])
    validation_results['status'] = "VALIDATED" if all_passed else "FAILED"
    
    # Summary
    print("\\n" + "-" * 50)
    print(f"VALIDATION COMPLETE: {validation_results['status']}")
    print(f"Tests passed: {sum(1 for t in validation_results['tests'] if t['passed'])}/{len(validation_results['tests'])}")
    
    return validation_results


def create_mock_volume_shock_scenario() -> Dict[str, Any]:
    """
    Create mock options data with volume shock scenarios for testing
    
    Creates scenarios for:
    - Gamma Emergency: High volume spike at single strike
    - Institutional Sweep: Moderate volume across multiple strikes
    """
    
    # Mock underlying price
    underlying_price = 21000
    
    # Create contracts with different volume scenarios
    contracts = []
    
    # Gamma Emergency scenario: Strike 21000 with 10x volume spike
    contracts.append({
        "strike": 21000,
        "call_volume": 1000,  # High volume
        "put_volume": 200,    # Moderate put volume
        "call_delta": 0.5,
        "put_delta": -0.5,
        "underlying_price": underlying_price,
        "call_bid": 150,
        "call_ask": 155,
        "put_bid": 45,
        "put_ask": 50
    })
    
    # Institutional Sweep scenario: Multiple strikes with moderate volume
    for strike_offset in [-100, -50, 50, 100]:
        contracts.append({
            "strike": underlying_price + strike_offset,
            "call_volume": 300,  # Moderate volume spread across strikes
            "put_volume": 250,
            "call_delta": 0.4 if strike_offset > 0 else 0.6,
            "put_delta": -0.6 if strike_offset > 0 else -0.4,
            "underlying_price": underlying_price,
            "call_bid": 100 + strike_offset/10,
            "call_ask": 105 + strike_offset/10,
            "put_bid": 80 - strike_offset/10,
            "put_ask": 85 - strike_offset/10
        })
    
    # Normal volume strikes (should not trigger alerts)
    for strike_offset in [-200, -150, 150, 200]:
        contracts.append({
            "strike": underlying_price + strike_offset,
            "call_volume": 50,   # Normal volume
            "put_volume": 30,
            "call_delta": 0.3 if strike_offset > 0 else 0.7,
            "put_delta": -0.7 if strike_offset > 0 else -0.3,
            "underlying_price": underlying_price,
            "call_bid": 80 + strike_offset/15,
            "call_ask": 85 + strike_offset/15,
            "put_bid": 90 - strike_offset/15,
            "put_ask": 95 - strike_offset/15
        })
    
    return {
        "underlying_symbol": "NQ",
        "underlying_price": underlying_price,
        "expiration_date": "2025-06-20",
        "contracts": contracts,
        "total_contracts": len(contracts),
        "source": "mock_volume_shock_scenario",
        "timestamp": datetime.now().isoformat()
    }


# Removed duplicate save_evidence - now using canonical implementation from test_utils


if __name__ == "__main__":
    # Execute validation
    results = validate_volume_shock_analysis()
    
    # Save evidence
    save_evidence(results)
    
    # Exit with appropriate code
    exit(0 if results['status'] == "VALIDATED" else 1)
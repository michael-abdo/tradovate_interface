#!/usr/bin/env python3
"""
TASK: expected_value_analysis
TYPE: Validation Test
PURPOSE: Validate that NQ EV analysis works correctly using your actual algorithm
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

from solution import ExpectedValueAnalyzer, analyze_expected_value


def validate_expected_value_analysis():
    """
    Validate the expected value analysis functionality using your actual algorithm
    
    Returns:
        Dict with validation results and evidence
    """
    print("EXECUTING VALIDATION: expected_value_analysis (NQ EV Algorithm)")
    print("-" * 50)
    
    validation_results = {
        "task": "expected_value_analysis",
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "status": "FAILED",
        "evidence": {}
    }
    
    # Test configuration using your algorithm's defaults
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
    
    analysis_config = {
        "weights": {
            "oi_factor": 0.35,
            "vol_factor": 0.25,
            "pcr_factor": 0.25,
            "distance_factor": 0.15
        },
        "min_ev": 15,  # Your algorithm's actual threshold
        "min_probability": 0.60,  # Your algorithm's actual threshold
        "max_risk": 150,  # Your algorithm's actual threshold
        "min_risk_reward": 1.0  # Your algorithm's actual threshold
    }
    
    # Test 1: Initialize analyzer
    print("\n1. Testing analyzer initialization...")
    try:
        analyzer = ExpectedValueAnalyzer(analysis_config)
        init_valid = (
            analyzer is not None and
            hasattr(analyzer, 'weights') and
            analyzer.min_ev == 15 and
            analyzer.min_probability == 0.60 and
            analyzer.max_risk == 150
        )
        
        validation_results["tests"].append({
            "name": "analyzer_init",
            "passed": init_valid,
            "details": {
                "weights": analyzer.weights,
                "min_ev": analyzer.min_ev,
                "min_probability": analyzer.min_probability,
                "max_risk": analyzer.max_risk
            }
        })
        print(f"   ✓ Analyzer initialized: {init_valid}")
        print(f"   ✓ Using your algorithm's weights: OI={analyzer.weights['oi_factor']}")
        
    except Exception as e:
        add_validation_error(validation_results, "analyzer_init", e)
        return validation_results
    
    # Test 2: Load normalized data
    print("\n2. Testing data loading...")
    try:
        data = analyzer.load_normalized_data(data_config)
        
        data_loaded = (
            data is not None and
            "contracts" in data and
            len(data["contracts"]) > 0 and
            data["underlying_price"] > 0
        )
        
        validation_results["tests"].append({
            "name": "data_loading",
            "passed": data_loaded,
            "details": {
                "contracts_count": len(data["contracts"]),
                "underlying_price": data["underlying_price"],
                "data_quality": data["quality"]
            }
        })
        
        print(f"   ✓ Data loaded: {len(data['contracts'])} contracts")
        print(f"   ✓ Underlying price: ${data['underlying_price']:,.2f}")
        
        # Store evidence
        validation_results["evidence"]["data_summary"] = {
            "contracts": len(data["contracts"]),
            "underlying_price": data["underlying_price"],
            "quality": data["quality"]
        }
        
    except Exception as e:
        add_validation_error(validation_results, "data_loading", e)
        return validation_results
    
    # Test 3: Convert to OptionsStrike format
    print("\n3. Testing data conversion to OptionsStrike format...")
    try:
        strikes = analyzer.convert_to_options_strikes(data["contracts"])
        
        conversion_valid = (
            isinstance(strikes, list) and
            len(strikes) > 0 and
            all(hasattr(s, 'price') and hasattr(s, 'call_oi') and hasattr(s, 'put_oi') for s in strikes)
        )
        
        validation_results["tests"].append({
            "name": "options_strike_conversion",
            "passed": conversion_valid,
            "details": {
                "strikes_created": len(strikes),
                "sample_strike_price": strikes[0].price if strikes else None,
                "sample_call_oi": strikes[0].call_oi if strikes else None
            }
        })
        
        print(f"   ✓ Converted to {len(strikes)} OptionsStrike objects")
        if strikes:
            print(f"   ✓ Sample strike: ${strikes[0].price} (Call OI: {strikes[0].call_oi}, Put OI: {strikes[0].put_oi})")
        
    except Exception as e:
        add_validation_error(validation_results, "options_strike_conversion", e)
    
    # Test 4: Probability calculation using your algorithm
    print("\n4. Testing probability calculation...")
    try:
        if 'strikes' in locals() and strikes:
            current_price = data["underlying_price"]
            tp = current_price + 100
            sl = current_price - 50
            
            prob = analyzer.calculate_probability(current_price, tp, sl, strikes, 'long')
            
            prob_valid = (
                isinstance(prob, (int, float)) and
                0.1 <= prob <= 0.9  # Your algorithm clamps between 10% and 90%
            )
            
            validation_results["tests"].append({
                "name": "probability_calculation",
                "passed": prob_valid,
                "details": {
                    "current_price": current_price,
                    "tp": tp,
                    "sl": sl,
                    "probability": prob,
                    "direction": "long"
                }
            })
            
            print(f"   ✓ Probability calculated: {prob:.1%}")
            print(f"   ✓ Valid range (10%-90%): {prob_valid}")
        else:
            validation_results["tests"].append({
                "name": "probability_calculation",
                "passed": False,
                "details": "No strikes available for calculation"
            })
            
    except Exception as e:
        add_validation_error(validation_results, "probability_calculation", e)
    
    # Test 5: EV combinations calculation using your algorithm
    print("\n5. Testing EV combinations calculation...")
    try:
        if 'strikes' in locals():
            setups = analyzer.calculate_ev_combinations(data["underlying_price"], strikes)
            
            # Your algorithm might generate 0 setups with test data if thresholds are strict
            ev_valid = (
                isinstance(setups, list) and
                (len(setups) == 0 or all(hasattr(s, 'ev') and hasattr(s, 'direction') for s in setups))
            )
            
            validation_results["tests"].append({
                "name": "ev_combinations",
                "passed": ev_valid,
                "details": {
                    "strikes_tested": len(strikes),
                    "setups_generated": len(setups),
                    "best_setup": {
                        "direction": setups[0].direction,
                        "ev": setups[0].ev,
                        "tp": setups[0].tp,
                        "sl": setups[0].sl
                    } if setups else None
                }
            })
            
            print(f"   ✓ Generated {len(setups)} setups from {len(strikes)} strikes")
            if setups:
                best = setups[0]
                print(f"   ✓ Best setup: {best.direction} EV={best.ev:.1f} (TP={best.tp}, SL={best.sl})")
            else:
                print("   ✓ No setups met your algorithm's strict quality criteria")
        else:
            validation_results["tests"].append({
                "name": "ev_combinations",
                "passed": False,
                "details": "No strikes available for EV calculation"
            })
            
    except Exception as e:
        add_validation_error(validation_results, "ev_combinations", e)
    
    # Test 6: Quality filtering using your algorithm's criteria
    print("\n6. Testing quality filtering...")
    try:
        if 'setups' in locals():
            quality_setups = analyzer.filter_quality_setups(setups)
            
            # Quality filtering should work even with 0 input setups
            quality_valid = (
                isinstance(quality_setups, list) and
                len(quality_setups) <= len(setups) and
                (len(quality_setups) == 0 or all(s.ev >= 15 and s.probability >= 0.60 for s in quality_setups))
            )
            
            validation_results["tests"].append({
                "name": "quality_filtering",
                "passed": quality_valid,
                "details": {
                    "total_setups": len(setups),
                    "quality_setups": len(quality_setups),
                    "filter_criteria": {
                        "min_ev": analyzer.min_ev,
                        "min_probability": analyzer.min_probability,
                        "max_risk": analyzer.max_risk
                    }
                }
            })
            
            print(f"   ✓ Quality setups: {len(quality_setups)}/{len(setups)}")
            print(f"   ✓ Using your algorithm's strict criteria (EV≥15, Prob≥60%)")
        else:
            validation_results["tests"].append({
                "name": "quality_filtering",
                "passed": False,
                "details": "No setups available for quality filtering"
            })
            
    except Exception as e:
        add_validation_error(validation_results, "quality_filtering", e)
    
    # Test 7: Full analysis using your algorithm
    print("\n7. Testing full NQ EV analysis...")
    try:
        # Use integration function
        result = analyze_expected_value(data_config, analysis_config)
        
        analysis_valid = (
            result is not None and
            "underlying_price" in result and
            "strikes_analyzed" in result and
            "trading_report" in result and
            result["contracts_analyzed"] > 0
        )
        
        validation_results["tests"].append({
            "name": "full_analysis",
            "passed": analysis_valid,
            "details": {
                "contracts_analyzed": result.get("contracts_analyzed"),
                "strikes_analyzed": result.get("strikes_analyzed"),
                "setups_generated": result.get("setups_generated"),
                "quality_setups": result.get("quality_setups"),
                "has_trading_report": "trading_report" in result
            }
        })
        
        print(f"   ✓ Full analysis complete")
        print(f"   ✓ Contracts analyzed: {result['contracts_analyzed']}")
        print(f"   ✓ Strikes analyzed: {result['strikes_analyzed']}")
        print(f"   ✓ Quality setups: {result['quality_setups']}")
        
        # Show execution recommendation if available
        if result.get("trading_report", {}).get("execution_recommendation"):
            rec = result["trading_report"]["execution_recommendation"]
            print(f"   ✓ Best recommendation: {rec['trade_direction']} "
                  f"TP={rec['target']} SL={rec['stop']} EV={rec['expected_value']:+.1f}")
        else:
            print("   ✓ No trades met your algorithm's quality criteria")
        
        # Store evidence
        validation_results["evidence"]["analysis_result"] = {
            "contracts_analyzed": result["contracts_analyzed"],
            "strikes_analyzed": result["strikes_analyzed"],
            "quality_setups": result["quality_setups"],
            "trading_report": result["trading_report"],
            "metrics": result["metrics"]
        }
        
    except Exception as e:
        add_validation_error(validation_results, "full_analysis", e)
    
    # Determine overall status
    all_passed = all(test['passed'] for test in validation_results['tests'])
    validation_results['status'] = "VALIDATED" if all_passed else "FAILED"
    
    # Summary
    print("\n" + "-" * 50)
    print(f"VALIDATION COMPLETE: {validation_results['status']}")
    print(f"Tests passed: {sum(1 for t in validation_results['tests'] if t['passed'])}/{len(validation_results['tests'])}")
    print("Using your actual NQ Options EV algorithm with strict quality criteria")
    
    return validation_results


# Removed duplicate save_evidence - now using canonical implementation from test_utils


if __name__ == "__main__":
    # Execute validation
    results = validate_expected_value_analysis()
    
    # Save evidence
    save_evidence(results)
    
    # Exit with appropriate code
    exit(0 if results['status'] == "VALIDATED" else 1)
#!/usr/bin/env python3
"""
Single Entry Point for Hierarchical Pipeline Analysis Framework
Clean, simple interface to the new NQ Options Trading System

Usage:
  python3 run_pipeline.py                    # Run with today's EOD contract
  python3 run_pipeline.py MC7M25             # Run with specific contract
  python3 run_pipeline.py --contract MC2M25  # Run with specific contract (alternative syntax)
"""

import sys
import os
import argparse
from datetime import datetime

# Add pipeline system to path
pipeline_path = os.path.join(os.path.dirname(__file__), 'tasks', 'options_trading_system')
sys.path.insert(0, pipeline_path)

from integration import run_complete_nq_trading_system

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='NQ Options Hierarchical Pipeline Analysis Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_pipeline.py                    # Run with today's EOD contract (auto-calculated)
  python3 run_pipeline.py MC7M25             # Run with Friday's EOD contract
  python3 run_pipeline.py MC1M25             # Run with Monday's EOD contract
  python3 run_pipeline.py --contract MC2M25  # Run with Tuesday's EOD contract
  python3 run_pipeline.py MC6M25             # Run with monthly options
        """
    )
    
    parser.add_argument(
        'contract', 
        nargs='?', 
        help='Options contract symbol (e.g., MC7M25, MC1M25). If not provided, uses today\'s EOD contract.'
    )
    
    parser.add_argument(
        '--contract', 
        dest='contract_flag',
        help='Options contract symbol (alternative syntax)'
    )
    
    return parser.parse_args()

def get_target_contract(args):
    """Determine target contract from arguments"""
    # Priority: positional argument > --contract flag > None (auto-calculate)
    if args.contract:
        return args.contract.upper()
    elif args.contract_flag:
        return args.contract_flag.upper()
    else:
        return None

def main():
    """Single entry point for the pipeline system"""
    args = parse_arguments()
    target_contract = get_target_contract(args)
    
    print("🚀 NQ Options Hierarchical Pipeline Analysis Framework")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if target_contract:
        print(f"Target Contract: {target_contract} (user specified)")
    else:
        print("Target Contract: Auto-calculated EOD contract for today")
    
    print()
    
    try:
        # Create configuration with optional target contract
        config = None
        if target_contract:
            config = {
                "data": {
                    "barchart": {
                        "file_path": "data/api_responses/options_data_20250602_141553.json",
                        "use_live_api": True,
                        "futures_symbol": "NQM25",
                        "headless": True,
                        "target_symbol": target_contract
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
        
        # Run the complete pipeline system
        result = run_complete_nq_trading_system(config)
        
        if result['status'] == 'success':
            # Show the key result
            if 'system_summary' in result and 'trading_summary' in result['system_summary']:
                trading_summary = result['system_summary']['trading_summary']
                if 'primary_recommendation' in trading_summary and trading_summary['primary_recommendation']:
                    rec = trading_summary['primary_recommendation']
                    print(f"\n✅ PIPELINE RESULT:")
                    print(f"   {rec['direction']} @ ${rec['entry']:,.2f}")
                    print(f"   Target: ${rec['target']:,.0f}")
                    print(f"   Stop: ${rec['stop']:,.0f}")
                    print(f"   Expected Value: {rec['expected_value']:+.1f} points")
                    print(f"   Probability: {rec['probability']:.1%}")
                else:
                    print(f"\n✅ PIPELINE COMPLETE: No trades met quality criteria")
            else:
                print(f"\n✅ PIPELINE COMPLETE: {result['status']}")
        else:
            print(f"\n❌ PIPELINE FAILED: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ PIPELINE ERROR: {str(e)}")
        return 1
    
    print()
    print("=" * 60)
    return 0

if __name__ == "__main__":
    exit(main())
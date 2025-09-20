#!/usr/bin/env python3
"""
Simple Interface for NQ Options Trading System
Run this file to execute the complete trading analysis
"""

import sys
import os
from datetime import datetime

def main():
    """Simple interface to run the complete NQ Options Trading System"""
    
    print("🚀 NQ OPTIONS TRADING SYSTEM")
    print("=" * 50)
    print("Loading system...")
    
    try:
        # Add tasks directory to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tasks', 'options_trading_system'))
        
        # Import the main trading system
        from integration import run_complete_nq_trading_system
        
        # Default configuration - ready to run
        config = {
            'data': {
                'barchart': {
                    'file_path': 'data/api_responses/options_data_20250602_141553.json'
                },
                'tradovate': {
                    'mode': 'demo',
                    'cid': '6540', 
                    'secret': 'f7a2b8f5-8348-424f-8ffa-047ab7502b7c',
                    'use_mock': True
                }
            },
            'analysis': {
                'expected_value': {
                    'weights': {
                        'oi_factor': 0.35,
                        'vol_factor': 0.25, 
                        'pcr_factor': 0.25,
                        'distance_factor': 0.15
                    },
                    'min_ev': 15,
                    'min_probability': 0.60,
                    'max_risk': 150,
                    'min_risk_reward': 1.0
                },
                'risk': {
                    'multiplier': 20,
                    'immediate_threat_distance': 10,
                    'near_term_distance': 25,
                    'medium_term_distance': 50
                }
            },
            'output': {
                'report': {
                    'style': 'professional',
                    'include_details': True,
                    'include_market_context': True
                },
                'json': {
                    'include_raw_data': False,
                    'include_metadata': True,
                    'format_pretty': True,
                    'include_analysis_details': True
                }
            },
            'save': {
                'save_report': True,
                'save_json': True,
                'output_dir': 'tasks/options_trading_system/outputs',
                'timestamp_suffix': True
            }
        }
        
        print("✓ System loaded successfully")
        print("✓ Running analysis on NQ Options data...")
        print()
        
        # Run the complete trading system
        result = run_complete_nq_trading_system(config)
        
        # Show results
        print("\n" + "=" * 60)
        print("🎯 TRADING ANALYSIS COMPLETE")
        print("=" * 60)
        
        if result['status'] == 'success':
            summary = result['system_summary']
            
            print(f"✅ System Status: SUCCESS")
            print(f"📊 System Health: {summary['system_health']['status'].title()}")
            print(f"⏱️  Execution Time: {result['execution_time_seconds']:.2f} seconds")
            print(f"🎯 Pipeline Success: {summary['system_health']['pipeline_success_rate']:.1%}")
            
            # Show primary trade recommendation
            if summary.get('trading_summary', {}).get('primary_recommendation'):
                rec = summary['trading_summary']['primary_recommendation']
                print(f"\n💰 PRIMARY TRADE RECOMMENDATION:")
                print(f"   Direction: {rec['direction']}")
                print(f"   Entry: ${rec['entry']:,.2f}")
                print(f"   Target: ${rec['target']:,.0f}")
                print(f"   Stop: ${rec['stop']:,.0f}")
                print(f"   Expected Value: {rec['expected_value']:+.1f} points")
                print(f"   Win Probability: {rec['probability']:.1%}")
                print(f"   Position Size: {rec['position_size']}")
                
                # Show risk analysis context
                if 'risk_bias' in summary.get('trading_summary', {}):
                    print(f"\n🎯 Risk Analysis:")
                    print(f"   Market Bias: {summary['trading_summary'].get('risk_bias', 'Unknown')}")
            
            # Show output files
            pipeline_results = result.get('pipeline_results', {})
            if pipeline_results.get('output', {}).get('status') == 'success':
                output_result = pipeline_results['output']['result']
                if output_result.get('save_results', {}).get('files_saved'):
                    print(f"\n📄 Generated Files:")
                    for file_info in output_result['save_results']['files_saved']:
                        print(f"   ✓ {file_info['filename']} ({file_info['size_bytes']} bytes)")
        else:
            print(f"❌ System Status: FAILED")
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Make sure you're running this from the project root directory.")
        sys.exit(1)


if __name__ == "__main__":
    main()
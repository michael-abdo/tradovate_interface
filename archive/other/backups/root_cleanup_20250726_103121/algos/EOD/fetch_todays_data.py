#!/usr/bin/env python3
"""
Fetch today's Barchart options data
"""
import os
import sys
import json
from datetime import datetime

# Add necessary paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tasks'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tasks', 'options_trading_system'))

# Now we can import
from tasks.options_trading_system.integration import run_complete_nq_trading_system

def get_todays_eod_symbol():
    """Calculate today's EOD symbol"""
    today = datetime.now()
    
    # Month codes
    month_codes = {
        1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
        7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'
    }
    
    # Day codes (Monday=1, Tuesday=2, etc.)
    day_codes = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}
    
    month_code = month_codes[today.month]
    day_of_week = today.weekday()
    
    if day_of_week >= 5:  # Weekend
        print("It's a weekend - markets are closed")
        # Use Monday's symbol
        day_code = 1
    else:
        day_code = day_codes[day_of_week]
    
    year = today.year % 100
    
    eod_symbol = f"MC{day_code}{month_code}{year}"
    monthly_symbol = f"MC{month_code}{year}"
    
    return eod_symbol, monthly_symbol, today

def main():
    eod_symbol, monthly_symbol, today = get_todays_eod_symbol()
    
    print("="*60)
    print("BARCHART OPTIONS DATA FETCHER")
    print("="*60)
    print(f"Date: {today.strftime('%Y-%m-%d %A')}")
    print(f"EOD Symbol: {eod_symbol}")
    print(f"Monthly Symbol: {monthly_symbol}")
    print("="*60)
    
    # Configuration for data collection
    config = {
        "contract": eod_symbol,
        "fallback_contract": monthly_symbol,
        "data_sources": {
            "barchart_live_api": {
                "enabled": True,
                "use_live_api": True,
                "headless": True
            },
            "tradovate_api": {
                "enabled": False
            }
        },
        "output": {
            "save_files": True,
            "output_dir": f"outputs/{today.strftime('%Y%m%d')}"
        }
    }
    
    print("\nRunning data collection pipeline...")
    print("-"*60)
    
    try:
        # Run the complete pipeline
        results = run_complete_nq_trading_system(config)
        
        if results and results.get("status") == "success":
            print("\n✅ SUCCESS: Data collection completed")
            
            # Extract data info
            data_results = results.get("data", {})
            if "barchart_live_api" in data_results:
                barchart_data = data_results["barchart_live_api"]
                if barchart_data.get("status") == "success":
                    result = barchart_data.get("result", {})
                    print(f"\nData Summary:")
                    print(f"- Symbol: {result.get('underlying_symbol', 'N/A')}")
                    print(f"- Underlying Price: ${result.get('underlying_price', 0):,.2f}")
                    print(f"- Total Contracts: {result.get('total_contracts', 0)}")
                    print(f"- Data Source: {result.get('metadata', {}).get('source', 'N/A')}")
            
            # Save location info
            if results.get("outputs", {}).get("save_results", {}).get("files_saved"):
                print(f"\nFiles saved to: {config['output']['output_dir']}/")
                for file_info in results["outputs"]["save_results"]["files_saved"]:
                    print(f"- {file_info['filename']}")
                    
        else:
            print("\n❌ ERROR: Data collection failed")
            if results:
                print(f"Error: {results.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
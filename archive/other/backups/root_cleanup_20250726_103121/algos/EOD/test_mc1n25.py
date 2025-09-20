#!/usr/bin/env python3
"""
Test MC1N25 symbol to understand Barchart's behavior
"""

import sys
import os
from datetime import datetime

# Add necessary paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tasks'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tasks', 'options_trading_system', 'data_ingestion'))

from barchart_web_scraper.hybrid_scraper import HybridBarchartScraper

def test_symbols():
    """Test various symbols to understand Barchart's logic"""
    
    symbols_to_test = [
        "MC1N25",  # Monday July 2025
        "MC6N25",  # What Barchart is suggesting
        "MCN25",   # Monthly contract
        "MM1N25",  # Alternative prefix Monday
        "MM6N25",  # Alternative prefix 6
    ]
    
    print("="*60)
    print("TESTING BARCHART SYMBOL BEHAVIOR")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Initialize scraper
    scraper = HybridBarchartScraper(headless=True)
    
    # Authenticate
    print("\nAuthenticating with Barchart...")
    if not scraper.authenticate("NQU25"):
        print("Authentication failed!")
        return
    
    print("\nTesting symbols:")
    print("-"*60)
    
    for symbol in symbols_to_test:
        print(f"\n📊 Testing: {symbol}")
        print("-"*40)
        
        try:
            # Fetch data
            data = scraper.fetch_options_data(symbol)
            
            if data:
                contracts = data.get('total_contracts', 0)
                underlying = data.get('underlying_symbol', 'N/A')
                price = data.get('underlying_price', 0)
                
                print(f"✓ Success!")
                print(f"  - Contracts found: {contracts}")
                print(f"  - Underlying: {underlying}")
                print(f"  - Price: ${price:,.2f}")
                
                # Check if any options exist
                options = data.get('options', [])
                if options:
                    # Show first few strikes
                    strikes = sorted(set(opt.get('strike', 0) for opt in options))[:5]
                    print(f"  - Sample strikes: {strikes}")
                else:
                    print("  - No options data in response")
                    
            else:
                print("✗ No data returned")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    print("\n" + "="*60)
    print("ANALYSIS:")
    print("-"*60)
    print("MC[X]N25 where X is the digit after MC")
    print("Standard day codes: 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri")
    print("MC6N25 might be a special designation - checking Barchart docs...")
    
if __name__ == "__main__":
    test_symbols()
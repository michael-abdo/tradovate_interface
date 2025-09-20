#!/usr/bin/env python3
"""
Simple test to check MC1N25 vs MC6N25 on Barchart
"""

import sys
import os
from datetime import datetime

# Add necessary paths
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'tasks'))
sys.path.insert(0, os.path.join(parent_dir, 'tasks', 'options_trading_system', 'data_ingestion'))

from barchart_web_scraper.hybrid_scraper import HybridBarchartScraper

def main():
    """Test MC symbols"""
    
    symbols = ["MC1N25", "MC6N25", "MCN25"]
    
    print("="*60)
    print("TESTING MC SYMBOLS ON BARCHART")
    print(f"Date: {datetime.now()}")
    print("="*60)
    
    scraper = HybridBarchartScraper(headless=True)
    
    # Authenticate
    print("\nAuthenticating...")
    if not scraper.authenticate("NQU25"):
        print("Auth failed!")
        return
    
    for symbol in symbols:
        print(f"\n📊 {symbol}:")
        try:
            data = scraper.fetch_options_data(symbol)
            if data:
                print(f"  ✓ Contracts: {data.get('total_contracts', 0)}")
                print(f"  ✓ Underlying: {data.get('underlying_symbol', 'N/A')}")
                print(f"  ✓ Price: ${data.get('underlying_price', 0):,.2f}")
            else:
                print("  ✗ No data")
        except Exception as e:
            print(f"  ✗ Error: {e}")

if __name__ == "__main__":
    main()
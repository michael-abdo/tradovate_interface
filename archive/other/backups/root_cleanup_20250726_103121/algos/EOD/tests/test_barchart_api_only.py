#!/usr/bin/env python3
"""
Test loading only the Barchart API data (no web scraping)
This avoids Chrome/Selenium timeout issues
"""

import sys
import os
import json
from datetime import datetime

# Add the barchart_web_scraper directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tasks/options_trading_system/data_ingestion/barchart_web_scraper'))

from solution import BarchartAPIComparator, OptionsChainData

def test_api_data_only():
    """Test loading and analyzing the existing Barchart API data"""
    
    print("🔍 Testing Barchart API Data Loading (No Web Scraping)")
    print("=" * 60)
    
    # Initialize comparator
    comparator = BarchartAPIComparator()
    
    # Load API data
    print("\n📡 Loading existing Barchart API data...")
    api_data = comparator.fetch_api_data("NQM25")
    
    print(f"✅ Successfully loaded {api_data.total_contracts} contracts")
    print(f"📊 Data Summary:")
    print(f"   - Symbol: {api_data.underlying_symbol}")
    print(f"   - Expiration: {api_data.expiration_date}")
    print(f"   - Underlying Price: ${api_data.underlying_price:,.2f}")
    print(f"   - Source: {api_data.source}")
    print(f"   - Timestamp: {api_data.timestamp}")
    
    # Analyze the data
    print(f"\n📈 Contract Analysis:")
    
    # Count contracts with valid data
    contracts_with_call_data = sum(1 for c in api_data.contracts if c.call_last is not None)
    contracts_with_put_data = sum(1 for c in api_data.contracts if c.put_last is not None)
    contracts_with_volume = sum(1 for c in api_data.contracts if (c.call_volume or 0) > 0 or (c.put_volume or 0) > 0)
    
    print(f"   - Contracts with call data: {contracts_with_call_data}")
    print(f"   - Contracts with put data: {contracts_with_put_data}")
    print(f"   - Contracts with volume: {contracts_with_volume}")
    
    # Find strikes with highest volume
    print(f"\n🔥 Top 5 Strikes by Volume:")
    sorted_by_volume = sorted(api_data.contracts, 
                             key=lambda c: (c.call_volume or 0) + (c.put_volume or 0), 
                             reverse=True)
    
    for i, contract in enumerate(sorted_by_volume[:5]):
        total_volume = (contract.call_volume or 0) + (contract.put_volume or 0)
        print(f"   {i+1}. Strike ${contract.strike:,.0f}: {total_volume:,} volume")
        if contract.call_volume:
            print(f"      - Call: {contract.call_volume:,} vol, Last ${contract.call_last}")
        if contract.put_volume:
            print(f"      - Put: {contract.put_volume:,} vol, Last ${contract.put_last}")
    
    # ATM Analysis
    print(f"\n🎯 At-The-Money Analysis:")
    underlying = api_data.underlying_price
    
    # Find closest strikes to underlying
    sorted_by_distance = sorted(api_data.contracts, 
                               key=lambda c: abs(c.strike - underlying))
    
    for contract in sorted_by_distance[:3]:
        distance = contract.strike - underlying
        print(f"   Strike ${contract.strike:,.0f} ({distance:+,.0f} from underlying)")
        if contract.call_last:
            print(f"      - Call: ${contract.call_last} (Bid: ${contract.call_bid or 0}, Ask: ${contract.call_ask or 0})")
        if contract.put_last:
            print(f"      - Put: ${contract.put_last} (Bid: ${contract.put_bid or 0}, Ask: ${contract.put_ask or 0})")
    
    # Save sample data
    print(f"\n💾 Saving sample data...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sample_file = f"barchart_api_sample_{timestamp}.json"
    
    sample_data = {
        "summary": {
            "total_contracts": api_data.total_contracts,
            "underlying_symbol": api_data.underlying_symbol,
            "underlying_price": api_data.underlying_price,
            "expiration_date": api_data.expiration_date,
            "timestamp": api_data.timestamp.isoformat()
        },
        "top_volume_strikes": [
            {
                "strike": c.strike,
                "total_volume": (c.call_volume or 0) + (c.put_volume or 0),
                "call_volume": c.call_volume,
                "put_volume": c.put_volume,
                "call_last": c.call_last,
                "put_last": c.put_last
            }
            for c in sorted_by_volume[:10]
        ],
        "atm_strikes": [
            {
                "strike": c.strike,
                "distance_from_underlying": c.strike - underlying,
                "call_last": c.call_last,
                "call_bid": c.call_bid,
                "call_ask": c.call_ask,
                "put_last": c.put_last,
                "put_bid": c.put_bid,
                "put_ask": c.put_ask
            }
            for c in sorted_by_distance[:5]
        ]
    }
    
    with open(sample_file, 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"✅ Sample data saved to: {sample_file}")
    
    return api_data

if __name__ == "__main__":
    try:
        test_api_data_only()
        print("\n✅ API data test completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
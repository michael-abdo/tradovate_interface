#!/usr/bin/env python3
"""
Test Databento API access with both Live and Historical APIs
Tests specifically for NQ weekly options
"""

import databento as db
import os
from datetime import datetime, timedelta

def test_api_keys():
    """Test all available API keys"""
    api_keys = [
        ('env_key', os.environ.get('DATABENTO_API_KEY')),
        ('key1', 'db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ'),
        ('key2', 'db-G6UdaW7epknFt6XceRt4SYjdsXwMx'),
        ('key3', 'db-i4VujYQdiwvJD3rpsEhqV8hanxdxc'),
    ]
    
    for key_name, api_key in api_keys:
        if not api_key:
            continue
            
        print(f"\n{'='*60}")
        print(f"Testing {key_name}: {api_key[:20]}...")
        print(f"{'='*60}")
        
        # Test 1: Live API
        print("\n1. Testing Live API...")
        try:
            client = db.Live(key=api_key)
            print("   ✓ Client created successfully")
            
            # Try subscribing
            client.subscribe(
                dataset=db.Dataset.GLBX_MDP3,
                schema=db.Schema.BBO_1M,
                symbols=["NQ.OPT"],
                stype_in=db.SType.PARENT,
                start=0,
            )
            print("   ✓ Subscription successful!")
            client.stop()
            
        except Exception as e:
            print(f"   ✗ Live API failed: {e}")
        
        # Test 2: Historical API
        print("\n2. Testing Historical API...")
        try:
            hist_client = db.Historical(api_key)
            print("   ✓ Historical client created")
            
            # Get recent NQ options data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            
            data = hist_client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols="NQ.OPT",
                schema="definition",
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                stype_in="parent",
                limit=10
            )
            
            df = data.to_df()
            print(f"   ✓ Historical data retrieved: {len(df)} records")
            
            if len(df) > 0:
                print("\n   Sample NQ option symbols found:")
                for idx, row in df.head(5).iterrows():
                    if 'raw_symbol' in row:
                        print(f"     - {row['raw_symbol']}")
                    elif 'symbol' in row:
                        print(f"     - {row['symbol']}")
                        
        except Exception as e:
            print(f"   ✗ Historical API failed: {e}")

def test_specific_weekly_options():
    """Test specific NQ weekly option symbols"""
    print(f"\n{'='*60}")
    print("Testing Specific NQ Weekly Options")
    print(f"{'='*60}")
    
    # Use the most recently working key
    api_key = 'db-i4VujYQdiwvJD3rpsEhqV8hanxdxc'
    
    try:
        hist_client = db.Historical(api_key)
        
        # Test specific weekly option patterns
        test_symbols = [
            "NQ",      # Base future
            "NQ.OPT",  # All NQ options
            "NQQ3C",   # Week-3 Wednesday
            "NQQ1A",   # Week-1 Monday
            "NQQNE",   # End-of-month
        ]
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        for symbol in test_symbols:
            print(f"\nTesting symbol: {symbol}")
            try:
                data = hist_client.timeseries.get_range(
                    dataset="GLBX.MDP3",
                    symbols=symbol,
                    schema="definition",
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                    stype_in="raw_symbol",
                    limit=5
                )
                
                df = data.to_df()
                print(f"  ✓ Found {len(df)} records")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                
    except Exception as e:
        print(f"Historical API setup failed: {e}")

if __name__ == "__main__":
    print("Testing Databento API Access")
    print(f"Timestamp: {datetime.now()}")
    
    test_api_keys()
    test_specific_weekly_options()
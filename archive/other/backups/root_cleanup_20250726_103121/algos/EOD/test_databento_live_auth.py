#!/usr/bin/env python3
"""
Test Databento Live API with proper authentication
"""

import databento as db
import os

def test_live_auth():
    """Test Live API authentication approaches"""
    print("🔍 TESTING DATABENTO LIVE API AUTHENTICATION")
    print("="*60)
    
    # Test 1: Try with API key in constructor
    print("\n📋 TEST 1: Live API with explicit key")
    print("-" * 40)
    
    try:
        client = db.Live(key="db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
        
        print("🔍 Attempting to subscribe to ES.OPT...")
        
        client.subscribe(
            dataset=db.Dataset.GLBX_MDP3,
            schema=db.Schema.BBO_1M,
            symbols=["ES.OPT"],
            stype_in=db.SType.PARENT,
            start=0,
        )
        
        print("✅ Subscription successful!")
        
        # Try to get a few messages
        messages = []
        def collect_msg(msg):
            messages.append(msg)
            print(f"📊 Message: {msg}")
            if len(messages) >= 3:
                client.stop()
        
        client.add_callback(collect_msg)
        client.start()
        
        import time
        timeout = 20
        start_time = time.time()
        
        while len(messages) < 3 and (time.time() - start_time) < timeout:
            time.sleep(1)
        
        client.stop()
        
        print(f"✅ Received {len(messages)} messages from ES.OPT")
        
    except Exception as e:
        print(f"❌ Live API with key error: {e}")
    
    # Test 2: Check if this is a subscription issue
    print("\n📋 TEST 2: Check Live API capabilities")
    print("-" * 40)
    
    try:
        # Try to create client without subscribing
        client2 = db.Live(key="db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
        print("✅ Live client created successfully")
        
        # Check available datasets or methods
        print("📋 Live client methods:")
        methods = [attr for attr in dir(client2) if not attr.startswith('_')]
        for method in methods[:10]:  # Show first 10
            print(f"   - {method}")
        
    except Exception as e:
        print(f"❌ Live client creation error: {e}")
    
    # Test 3: Try Historical API with the same approach
    print("\n📋 TEST 3: Historical API with ES.OPT for comparison")
    print("-" * 40)
    
    try:
        hist_client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
        
        # Try ES.OPT with Historical API
        es_data = hist_client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="ES.OPT",
            schema="definition",
            start="2025-07-16",
            end="2025-07-17",
            stype_in="parent",
            limit=100
        )
        
        es_df = es_data.to_df()
        print(f"✅ ES.OPT Historical: {len(es_df)} instruments found")
        
        if len(es_df) > 0:
            print("📊 Sample ES.OPT symbols:")
            for symbol in es_df['symbol'].head(10):
                print(f"   {symbol}")
    
    except Exception as e:
        print(f"❌ ES.OPT Historical error: {e}")
    
    # Test 4: Check subscription requirements
    print("\n📋 TEST 4: Check Live API requirements")
    print("-" * 40)
    
    try:
        # Check if there are specific subscription requirements
        from databento import Live
        print("✅ Live API class imported successfully")
        
        # Check class documentation
        print("📋 Live API info:")
        print(f"   Live class: {Live}")
        
        # Try to understand authentication error
        print("\n💡 Live API may require:")
        print("   - Different subscription tier")
        print("   - Real-time data subscription")
        print("   - Live market hours")
        print("   - Different authentication method")
        
    except Exception as e:
        print(f"❌ Live API check error: {e}")

if __name__ == "__main__":
    test_live_auth()
#!/usr/bin/env python3
"""
Test Databento Live API approach with NQ.OPT as requested
Following their exact pattern but using NQ instead of ES
"""

import databento as db
import time
import os

def test_live_nq_approach():
    """Test the Live API approach with NQ.OPT"""
    print("🔍 TESTING DATABENTO LIVE API WITH NQ.OPT")
    print("="*60)
    print("Using their exact pattern but with NQ instead of ES")
    print("="*60)
    
    # Test 1: Exact pattern they suggested but with NQ
    print("\n📋 TEST 1: Live NQ.OPT with BBO_1M")
    print("-" * 40)
    
    try:
        client = db.Live()
        
        print("🔍 Subscribing to NQ.OPT with their exact pattern...")
        
        client.subscribe(
            dataset=db.Dataset.GLBX_MDP3,
            schema=db.Schema.BBO_1M,  # Their suggested schema
            symbols=["NQ.OPT"],       # NQ instead of ES
            stype_in=db.SType.PARENT,
            start=0,
        )
        
        received_data = []
        
        def callback_handler(msg):
            received_data.append(msg)
            print(f"📊 NQ.OPT Data: {msg}")
            
            # Stop after getting some data
            if len(received_data) >= 10:
                client.stop()
        
        client.add_callback(callback_handler)
        
        print("▶️  Starting live feed...")
        client.start()
        
        # Wait for data or timeout
        timeout = 30
        start_time = time.time()
        
        while len(received_data) < 10 and (time.time() - start_time) < timeout:
            time.sleep(1)
            print(f"⏱️  Waiting... {len(received_data)} messages received")
        
        try:
            client.stop()
        except:
            pass
        
        print(f"✅ NQ.OPT Live test completed - {len(received_data)} messages")
        
        if len(received_data) > 0:
            print(f"\n📊 Sample NQ.OPT live data:")
            for i, msg in enumerate(received_data[:3]):
                print(f"   {i+1}: {msg}")
        
    except Exception as e:
        print(f"❌ Live NQ.OPT error: {e}")
    
    # Test 2: Try different schemas with NQ.OPT
    print("\n📋 TEST 2: NQ.OPT with Different Schemas")
    print("-" * 40)
    
    schemas_to_test = [
        db.Schema.TRADES,
        db.Schema.TBBO,
        db.Schema.DEFINITION
    ]
    
    for schema in schemas_to_test:
        try:
            print(f"\n🔍 Testing NQ.OPT with {schema}...")
            
            client2 = db.Live()
            schema_data = []
            
            def schema_callback(msg):
                schema_data.append(msg)
                print(f"📊 {schema}: {msg}")
                if len(schema_data) >= 5:
                    client2.stop()
            
            client2.subscribe(
                dataset=db.Dataset.GLBX_MDP3,
                schema=schema,
                symbols=["NQ.OPT"],
                stype_in=db.SType.PARENT,
                start=0,
            )
            
            client2.add_callback(schema_callback)
            client2.start()
            
            # Shorter timeout for each schema
            schema_timeout = 15
            schema_start = time.time()
            
            while len(schema_data) < 5 and (time.time() - schema_start) < schema_timeout:
                time.sleep(1)
            
            try:
                client2.stop()
            except:
                pass
            
            print(f"   ✅ {schema}: {len(schema_data)} messages")
            
        except Exception as e:
            print(f"   ❌ {schema} error: {e}")
    
    # Test 3: Try with API key explicitly
    print("\n📋 TEST 3: NQ.OPT with Explicit API Key")
    print("-" * 40)
    
    # Try different possible API key configurations
    api_keys_to_try = [
        "db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ",
        os.getenv("DATABENTO_API_KEY"),  # Environment variable
        None  # Default
    ]
    
    for api_key in api_keys_to_try:
        if api_key is None:
            continue
            
        try:
            print(f"\n🔍 Testing with API key: {api_key[:10]}...")
            
            client3 = db.Live(key=api_key)
            
            client3.subscribe(
                dataset=db.Dataset.GLBX_MDP3,
                schema=db.Schema.BBO_1M,
                symbols=["NQ.OPT"],
                stype_in=db.SType.PARENT,
                start=0,
            )
            
            key_data = []
            
            def key_callback(msg):
                key_data.append(msg)
                print(f"📊 Key test: {msg}")
                if len(key_data) >= 3:
                    client3.stop()
            
            client3.add_callback(key_callback)
            client3.start()
            
            key_timeout = 20
            key_start = time.time()
            
            while len(key_data) < 3 and (time.time() - key_start) < key_timeout:
                time.sleep(1)
            
            try:
                client3.stop()
            except:
                pass
            
            print(f"   ✅ API key test: {len(key_data)} messages")
            
            if len(key_data) > 0:
                print("   🎯 SUCCESS with this API key!")
                break
                
        except Exception as e:
            print(f"   ❌ API key error: {e}")
    
    print(f"\n🎯 Live NQ.OPT testing complete!")

if __name__ == "__main__":
    test_live_nq_approach()
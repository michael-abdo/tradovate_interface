#!/usr/bin/env python3
"""
Test the Databento Live API approach suggested by support
Testing both ES.OPT and NQ.OPT with live feed
"""

import databento as db
import time

def test_live_api():
    """Test the Live API with parent symbology"""
    print("🔍 TESTING DATABENTO LIVE API APPROACH")
    print("="*60)
    
    # Test 1: ES.OPT as suggested
    print("\n📋 TEST 1: ES.OPT Live Feed (as suggested)")
    print("-" * 40)
    
    try:
        client = db.Live()
        
        # Set up callback to capture data
        data_received = []
        
        def capture_data(msg):
            data_received.append(msg)
            print(f"📊 Received: {msg}")
            if len(data_received) >= 10:  # Stop after 10 messages
                client.stop()
        
        client.subscribe(
            dataset=db.Dataset.GLBX_MDP3,
            schema=db.Schema.BBO_1M,
            symbols=["ES.OPT"],
            stype_in=db.SType.PARENT,
            start=0,
        )
        
        client.add_callback(capture_data)
        client.start()
        
        # Wait for some data or timeout
        timeout = 30  # seconds
        start_time = time.time()
        
        while len(data_received) < 10 and (time.time() - start_time) < timeout:
            time.sleep(1)
        
        client.stop()
        
        print(f"✅ ES.OPT test completed - received {len(data_received)} messages")
        
    except Exception as e:
        print(f"❌ ES.OPT Live API error: {e}")
    
    # Test 2: NQ.OPT with Live API
    print("\n📋 TEST 2: NQ.OPT Live Feed")
    print("-" * 40)
    
    try:
        client2 = db.Live()
        
        data_received2 = []
        
        def capture_nq_data(msg):
            data_received2.append(msg)
            print(f"📊 NQ Data: {msg}")
            if len(data_received2) >= 10:
                client2.stop()
        
        client2.subscribe(
            dataset=db.Dataset.GLBX_MDP3,
            schema=db.Schema.BBO_1M,
            symbols=["NQ.OPT"],
            stype_in=db.SType.PARENT,
            start=0,
        )
        
        client2.add_callback(capture_nq_data)
        client2.start()
        
        # Wait for data
        start_time2 = time.time()
        while len(data_received2) < 10 and (time.time() - start_time2) < timeout:
            time.sleep(1)
        
        client2.stop()
        
        print(f"✅ NQ.OPT test completed - received {len(data_received2)} messages")
        
    except Exception as e:
        print(f"❌ NQ.OPT Live API error: {e}")
    
    # Test 3: Try different schemas
    print("\n📋 TEST 3: Different Schemas")
    print("-" * 40)
    
    schemas_to_test = [
        db.Schema.TRADES,
        db.Schema.TBBO,
        db.Schema.DEFINITION
    ]
    
    for schema in schemas_to_test:
        try:
            print(f"\n🔍 Testing {schema} with NQ.OPT...")
            
            client3 = db.Live()
            schema_data = []
            
            def capture_schema_data(msg):
                schema_data.append(msg)
                print(f"📊 {schema}: {msg}")
                if len(schema_data) >= 5:
                    client3.stop()
            
            client3.subscribe(
                dataset=db.Dataset.GLBX_MDP3,
                schema=schema,
                symbols=["NQ.OPT"],
                stype_in=db.SType.PARENT,
                start=0,
            )
            
            client3.add_callback(capture_schema_data)
            client3.start()
            
            start_time3 = time.time()
            while len(schema_data) < 5 and (time.time() - start_time3) < 15:
                time.sleep(1)
            
            client3.stop()
            
            print(f"   ✅ {schema}: {len(schema_data)} messages")
            
        except Exception as e:
            print(f"   ❌ {schema} error: {e}")
    
    print(f"\n🎯 Live API testing complete!")

if __name__ == "__main__":
    test_live_api()
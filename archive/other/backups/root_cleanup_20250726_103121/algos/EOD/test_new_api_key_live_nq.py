#!/usr/bin/env python3
"""
Test Databento Live API with new API key for NQ options
Using the exact pattern Databento support suggested but with NQ.OPT
"""

import databento as db
import time

def test_live_nq_with_new_key():
    """Test Live API with new API key"""
    print("🔍 TESTING DATABENTO LIVE API WITH NEW API KEY")
    print("="*60)
    print("API Key: db-i4VujYQdiwvJD3rpsEhqV8hanxdxc")
    print("Testing: NQ.OPT with Live API as support suggested")
    print("="*60)
    
    try:
        # Test 1: Live API with new key
        print("\n📋 TEST 1: Live API with NQ.OPT")
        print("-" * 40)
        
        client = db.Live(key="db-i4VujYQdiwvJD3rpsEhqV8hanxdxc")
        
        print("▶️  Subscribing to NQ.OPT with parent symbology...")
        
        client.subscribe(
            dataset=db.Dataset.GLBX_MDP3,
            schema=db.Schema.BBO_1M,
            symbols=["NQ.OPT"],
            stype_in=db.SType.PARENT,
            start=0,
        )
        
        messages = []
        
        def handle_message(msg):
            messages.append(msg)
            print(f"📊 NQ Option: {msg}")
            
            # Stop after getting enough data
            if len(messages) >= 20:
                client.stop()
        
        client.add_callback(handle_message)
        
        print("▶️  Starting live feed...")
        client.start()
        
        # Wait for data
        timeout = 60  # 1 minute timeout
        start_time = time.time()
        
        while len(messages) < 20 and (time.time() - start_time) < timeout:
            time.sleep(2)
            if len(messages) > 0 and len(messages) % 5 == 0:
                print(f"   📊 Received {len(messages)} messages so far...")
        
        try:
            client.stop()
        except:
            pass
        
        print(f"\n✅ Live API Results:")
        print(f"   Total messages: {len(messages)}")
        
        if len(messages) > 0:
            print("\n🎯 SUCCESS! Live API is working with new key!")
            
            # Analyze the data
            unique_symbols = set()
            for msg in messages:
                if hasattr(msg, 'symbol'):
                    unique_symbols.add(msg.symbol)
            
            if unique_symbols:
                print(f"\n📊 Unique NQ option symbols found:")
                for symbol in sorted(list(unique_symbols))[:20]:
                    print(f"   {symbol}")
                
                print(f"\n📋 Total unique NQ options: {len(unique_symbols)}")
                
                # Check for weekly options patterns
                weekly_patterns = ['Q', 'W', 'EW', 'EOW']
                weekly_found = [s for s in unique_symbols if any(p in s for p in weekly_patterns)]
                
                if weekly_found:
                    print(f"\n🎯 Potential weekly options found:")
                    for symbol in weekly_found[:10]:
                        print(f"   {symbol}")
        else:
            print("   ❌ No data received - may be outside market hours")
            
    except Exception as e:
        print(f"❌ Live API error: {e}")
        
        # If it's still auth error, test Historical API
        if "authentication" in str(e).lower():
            print("\n📋 TEST 2: Testing Historical API with new key")
            print("-" * 40)
            
            try:
                hist_client = db.Historical("db-i4VujYQdiwvJD3rpsEhqV8hanxdxc")
                
                # Simple test
                datasets = hist_client.metadata.list_datasets()
                print(f"✅ Historical API works! Datasets: {len(datasets)}")
                
                # Test NQ.OPT
                nq_data = hist_client.timeseries.get_range(
                    dataset="GLBX.MDP3",
                    symbols="NQ.OPT",
                    schema="definition",
                    start="2025-07-16",
                    end="2025-07-17",
                    stype_in="parent",
                    limit=50
                )
                
                nq_df = nq_data.to_df()
                print(f"✅ NQ.OPT Historical: {len(nq_df)} options found")
                
            except Exception as hist_e:
                print(f"❌ Historical API error: {hist_e}")

def test_comprehensive_nq_options():
    """Test comprehensive NQ options access with new key"""
    print("\n📋 TEST 3: Comprehensive NQ Options Test")
    print("-" * 40)
    
    try:
        # Test different schemas with Live API
        client = db.Live(key="db-i4VujYQdiwvJD3rpsEhqV8hanxdxc")
        
        schemas_to_test = [
            (db.Schema.TRADES, "Recent trades"),
            (db.Schema.DEFINITION, "Option definitions"),
            (db.Schema.TBBO, "Top bid/ask quotes")
        ]
        
        for schema, description in schemas_to_test:
            print(f"\n🔍 Testing {schema} - {description}")
            
            try:
                schema_messages = []
                
                def schema_handler(msg):
                    schema_messages.append(msg)
                    if len(schema_messages) <= 3:
                        print(f"   📊 {schema}: {msg}")
                    if len(schema_messages) >= 10:
                        client.stop()
                
                client = db.Live(key="db-i4VujYQdiwvJD3rpsEhqV8hanxdxc")
                
                client.subscribe(
                    dataset=db.Dataset.GLBX_MDP3,
                    schema=schema,
                    symbols=["NQ.OPT"],
                    stype_in=db.SType.PARENT,
                    start=0,
                )
                
                client.add_callback(schema_handler)
                client.start()
                
                # Quick timeout for each schema
                schema_start = time.time()
                while len(schema_messages) < 10 and (time.time() - schema_start) < 20:
                    time.sleep(1)
                
                try:
                    client.stop()
                except:
                    pass
                
                print(f"   ✅ {schema}: {len(schema_messages)} messages received")
                
            except Exception as schema_e:
                print(f"   ❌ {schema} error: {schema_e}")
                
    except Exception as e:
        print(f"❌ Comprehensive test error: {e}")

if __name__ == "__main__":
    test_live_nq_with_new_key()
    test_comprehensive_nq_options()
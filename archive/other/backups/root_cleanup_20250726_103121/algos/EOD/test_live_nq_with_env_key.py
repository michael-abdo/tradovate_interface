#!/usr/bin/env python3
"""
Test Live API with NQ.OPT using environment API key
"""

import databento as db
import time
import os

def test_nq_live_with_env_key():
    """Test NQ Live API with environment key"""
    print("🔍 TESTING NQ.OPT LIVE API WITH ENVIRONMENT KEY")
    print("="*60)
    
    env_key = os.getenv("DATABENTO_API_KEY")
    print(f"📋 Using API key: {env_key[:15]}...")
    
    try:
        # Test the exact pattern they suggested but with NQ
        print("\n📋 DATABENTO SUPPORT'S SUGGESTED PATTERN (NQ VERSION)")
        print("-" * 50)
        print("Their code:")
        print("client.subscribe(")
        print("    dataset=db.Dataset.GLBX_MDP3,")
        print("    schema=db.Schema.BBO_1M,")
        print("    symbols=['NQ.OPT'],  # <-- NQ instead of ES")
        print("    stype_in=db.SType.PARENT,")
        print("    start=0,")
        print(")")
        print("-" * 50)
        
        client = db.Live()
        
        # Exactly their pattern but NQ
        client.subscribe(
            dataset=db.Dataset.GLBX_MDP3,
            schema=db.Schema.BBO_1M,
            symbols=["NQ.OPT"],
            stype_in=db.SType.PARENT,
            start=0,
        )
        
        messages_received = []
        
        def handle_message(msg):
            messages_received.append(msg)
            print(f"📊 NQ.OPT Live Data: {msg}")
            
            # Stop after getting some data to see what we get
            if len(messages_received) >= 15:
                client.stop()
        
        client.add_callback(handle_message)
        
        print("\n▶️  Starting NQ.OPT live feed...")
        client.start()
        
        # Give it time to connect and receive data
        timeout = 45  # Longer timeout for live data
        start_time = time.time()
        
        print("⏱️  Waiting for NQ options data...")
        while len(messages_received) < 15 and (time.time() - start_time) < timeout:
            time.sleep(2)
            if len(messages_received) > 0 and len(messages_received) % 5 == 0:
                print(f"   📊 {len(messages_received)} messages received so far...")
        
        client.block_for_close()
        
        print(f"\n✅ NQ.OPT Live API Test Results:")
        print(f"   📊 Total messages received: {len(messages_received)}")
        
        if len(messages_received) > 0:
            print(f"\n📋 Sample NQ.OPT live data:")
            for i, msg in enumerate(messages_received[:5]):
                print(f"   {i+1}: {msg}")
            
            print(f"\n🎯 SUCCESS! Live API with NQ.OPT is working!")
            print(f"   This suggests live data has different/more comprehensive")
            print(f"   NQ options coverage than historical API")
            
            # Try to identify option symbols
            unique_symbols = set()
            for msg in messages_received:
                if hasattr(msg, 'symbol'):
                    unique_symbols.add(msg.symbol)
                elif isinstance(msg, dict) and 'symbol' in msg:
                    unique_symbols.add(msg['symbol'])
            
            if unique_symbols:
                print(f"\n📊 Unique NQ option symbols in live data:")
                for symbol in sorted(list(unique_symbols))[:10]:
                    print(f"   {symbol}")
        else:
            print("   ❌ No data received - may be outside market hours or no activity")
            
    except Exception as e:
        print(f"❌ Live NQ.OPT test error: {e}")
        
        # If auth fails, it might be the Live API subscription
        if "authentication" in str(e).lower():
            print("\n💡 Authentication failed - this could mean:")
            print("   - Live API requires different subscription tier")
            print("   - API key doesn't have live data permissions")
            print("   - Live API requires separate activation")
            print("\n📧 This is valuable info for the support request!")

if __name__ == "__main__":
    test_nq_live_with_env_key()
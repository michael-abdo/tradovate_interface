#!/usr/bin/env python3
"""Test Databento Live API with new key"""

import databento as db
import os

# Set the new API key
os.environ['DATABENTO_API_KEY'] = 'db-vWDhkTNKbF4pux7LuDGY78hspCaVJ'

print("Testing Databento Live API with new key...")
print("API Key: db-vWDhkTNKbF4pux7LuDGY78hspCaVJ")
print("-" * 70)

try:
    client = db.Live(key='db-vWDhkTNKbF4pux7LuDGY78hspCaVJ')
    
    print("✅ Client created successfully")
    print("\nAttempting to subscribe to NQ.OPT...")
    
    # Counter to limit output
    message_count = 0
    
    def callback(record):
        global message_count
        message_count += 1
        print(f"\n📊 Message #{message_count}:")
        print(f"Type: {type(record).__name__}")
        print(f"Data: {record}")
        
        # Stop after 5 messages to avoid flooding
        if message_count >= 5:
            print("\n✅ Successfully received 5 messages. Stopping...")
            client.stop()
    
    client.subscribe(
        dataset=db.Dataset.GLBX_MDP3,
        schema=db.Schema.BBO_1M,
        symbols=["NQ.OPT"],
        stype_in=db.SType.PARENT,
        start=0,
    )
    
    client.add_callback(callback)
    
    print("🚀 Starting Live API stream...")
    client.start()
    
    # Block for up to 30 seconds
    import time
    timeout = 30
    start_time = time.time()
    
    while client.is_connected() and (time.time() - start_time) < timeout:
        time.sleep(0.1)
        if message_count >= 5:
            break
    
    if message_count == 0:
        print(f"\n⚠️ No messages received after {timeout} seconds")
    
    client.stop()
    print("\n✅ Live API test completed")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
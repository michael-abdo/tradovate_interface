#!/usr/bin/env python3
"""
Final test of Databento Live API with proper authentication
Following their exact example structure
"""

import databento as db
import os

def main():
    print("Testing Databento Live API - Following Documentation Exactly")
    print("="*60)
    
    # The LIVE API key that Michael confirmed
    api_key = 'db-i4VujYQdiwvJD3rpsEhqV8hanxdxc'
    
    print(f"Using LIVE API key: {api_key}")
    print("This key HAS live data access according to Michael\n")
    
    # Test 1: Try their exact example first
    print("1. Testing with ES.OPT (their exact example):")
    print("-"*40)
    
    try:
        client = db.Live(key=api_key)
        
        client.subscribe(
            dataset=db.Dataset.GLBX_MDP3,
            schema=db.Schema.BBO_1M,
            symbols=["ES.OPT"],
            stype_in=db.SType.PARENT,
            start=0,
        )
        
        count = 0
        def print_callback(record):
            nonlocal count
            count += 1
            print(f"✓ Received: {record}")
            if count >= 5:
                client.stop()
        
        client.add_callback(print_callback)
        client.start()
        
        # Wait a bit
        import time
        time.sleep(10)
        
        if count > 0:
            print(f"\n✓ SUCCESS! Received {count} ES option records")
        else:
            print("\n✗ No data received for ES options")
            
        client.stop()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    # Test 2: Now try with NQ.OPT
    print("\n\n2. Testing with NQ.OPT:")
    print("-"*40)
    
    try:
        client2 = db.Live(key=api_key)
        
        client2.subscribe(
            dataset=db.Dataset.GLBX_MDP3,
            schema=db.Schema.BBO_1M,
            symbols=["NQ.OPT"],
            stype_in=db.SType.PARENT,
            start=0,
        )
        
        nq_count = 0
        def nq_callback(record):
            nonlocal nq_count
            nq_count += 1
            print(f"✓ NQ Option: {record}")
            if nq_count >= 5:
                client2.stop()
        
        client2.add_callback(nq_callback)
        client2.start()
        
        # Wait a bit
        time.sleep(10)
        
        if nq_count > 0:
            print(f"\n✓ SUCCESS! Received {nq_count} NQ option records")
        else:
            print("\n✗ No data received for NQ options")
            
        client2.stop()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    # Test 3: Debug authentication
    print("\n\n3. Testing basic connection:")
    print("-"*40)
    
    try:
        # Just create the client
        test_client = db.Live(key=api_key)
        print("✓ Client created successfully")
        
        # Try to get metadata
        print("Testing metadata access...")
        # Note: Live client doesn't have metadata methods like Historical
        
    except Exception as e:
        print(f"✗ Error creating client: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test Databento live API with NQ weekly options
Testing specific weekly option symbols:
- Q3C for Week-3 Wednesday expiry
- Q1A for Week-1 Monday expiry
- Monday & Wednesday weekly options
- End-of-month options (QNE)
"""

import databento as db
import os
from datetime import datetime

def main():
    print(f"Testing Databento Live API with NQ Weekly Options")
    print(f"Timestamp: {datetime.now()}")
    print("-" * 60)
    
    # Set API key
    api_key = os.environ.get('DATABENTO_API_KEY', 'db-i4VujYQdiwvJD3rpsEhqV8hanxdxc')
    
    # Initialize client
    client = db.Live(key=api_key)
    
    # Subscribe to NQ weekly options
    symbols = [
        "NQ.OPT",     # Parent symbol for all NQ options
        "Q3C.OPT",    # Week-3 Wednesday expiry
        "Q1A.OPT",    # Week-1 Monday expiry
        "QNE.OPT",    # End-of-month options
    ]
    
    print(f"Subscribing to symbols: {symbols}")
    print(f"Using dataset: GLBX.MDP3")
    print(f"Using schema: BBO_1M (1-minute best bid/offer)")
    print(f"Symbol type: PARENT")
    print("-" * 60)
    
    try:
        client.subscribe(
            dataset=db.Dataset.GLBX_MDP3,
            schema=db.Schema.BBO_1M,
            symbols=symbols,
            stype_in=db.SType.PARENT,
            start=0,  # Start from now
        )
        
        # Add callback to print received data
        def print_callback(record):
            print(f"\nReceived {record.__class__.__name__}:")
            print(f"  Timestamp: {datetime.fromtimestamp(record.ts_event / 1e9)}")
            
            # Print relevant fields based on record type
            if hasattr(record, 'symbol'):
                print(f"  Symbol: {record.symbol}")
            if hasattr(record, 'bid_px'):
                print(f"  Bid: {record.bid_px}")
            if hasattr(record, 'ask_px'):
                print(f"  Ask: {record.ask_px}")
            if hasattr(record, 'bid_sz'):
                print(f"  Bid Size: {record.bid_sz}")
            if hasattr(record, 'ask_sz'):
                print(f"  Ask Size: {record.ask_sz}")
            
            print("-" * 40)
        
        client.add_callback(print_callback)
        
        print("\nStarting live stream... (Press Ctrl+C to stop)")
        client.start()
        client.block_for_close()
        
    except Exception as e:
        print(f"\nError occurred: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
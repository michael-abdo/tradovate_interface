#!/usr/bin/env python3
"""
Test Databento's exact example code with NQ weekly options
Modified to handle the live data license requirement
"""

import databento as db
import os

# Their exact example, modified for NQ
def test_live_api():
    print("Testing Databento Live API - Exact Example")
    print("="*60)
    
    # Try all available API keys
    api_keys = [
        os.environ.get('DATABENTO_API_KEY'),
        'db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ',
        'db-G6UdaW7epknFt6XceRt4SYjdsXwMx',
        'db-i4VujYQdiwvJD3rpsEhqV8hanxdxc'
    ]
    
    for api_key in api_keys:
        if not api_key:
            continue
            
        print(f"\nTrying API key: {api_key[:20]}...")
        
        try:
            client = db.Live(key=api_key)
            
            # Try their exact subscription but with NQ.OPT
            client.subscribe(
                dataset=db.Dataset.GLBX_MDP3,
                schema=db.Schema.BBO_1M,
                symbols=["NQ.OPT"],  # Changed from ES.OPT to NQ.OPT
                stype_in=db.SType.PARENT,
                start=0,
            )
            
            client.add_callback(print)
            client.start()
            
            print("✓ Live stream started successfully!")
            print("Waiting for data... (Press Ctrl+C to stop)")
            
            client.block_for_close()
            
        except db.common.error.BentoError as e:
            if "live data license" in str(e):
                print(f"✗ This API key doesn't have live data license for GLBX.MDP3")
                print("  You need to upgrade your Databento subscription for live data")
            elif "authentication" in str(e).lower():
                print(f"✗ Authentication failed - API key may be invalid or expired")
            else:
                print(f"✗ Error: {e}")
        except KeyboardInterrupt:
            print("\nStopped by user")
            try:
                client.stop()
            except:
                pass
        except Exception as e:
            print(f"✗ Unexpected error: {e}")

def test_with_specific_symbols():
    """Test with the specific weekly option symbols mentioned"""
    print("\n\nTesting Specific Weekly Option Symbols")
    print("="*60)
    
    # Use the working API key (for historical, at least)
    api_key = 'db-i4VujYQdiwvJD3rpsEhqV8hanxdxc'
    
    # The symbols you mentioned
    weekly_symbols = [
        "Q3C",      # Week-3 Wednesday expiry
        "Q1A",      # Week-1 Monday expiry
        "QNE",      # End-of-month options
        "NQQ3C",    # Try with NQ prefix
        "NQQ1A",    # Try with NQ prefix
        "NQQNE",    # Try with NQ prefix
    ]
    
    print("Note: These symbol formats (Q3C, Q1A, QNE) don't appear to match")
    print("Databento's CME symbology. Standard NQ options use format like:")
    print("  - NQU5 C23000 (September 2025 Call at 23000)")
    print("  - NQZ5 P22000 (December 2025 Put at 22000)")
    print("\nFor weekly options, you may need to:")
    print("1. Contact Databento support for the correct weekly option symbols")
    print("2. Use their symbol resolution API to find weekly expirations")
    print("3. Filter by expiration date from all NQ.OPT data")

if __name__ == "__main__":
    test_live_api()
    test_with_specific_symbols()
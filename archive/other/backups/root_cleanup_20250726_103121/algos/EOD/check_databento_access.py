#!/usr/bin/env python3
"""
Check what Databento access this API key actually has
"""

import databento as db

def check_access():
    api_key = 'db-i4VujYQdiwvJD3rpsEhqV8hanxdxc'
    
    print("Checking Databento API Access")
    print("="*60)
    print(f"API Key: {api_key}")
    
    # Check Historical API access
    print("\n1. Historical API Access:")
    print("-"*40)
    
    try:
        hist_client = db.Historical(api_key)
        
        # List available datasets
        datasets = hist_client.metadata.list_datasets()
        print(f"✓ Historical API works!")
        print(f"✓ Available datasets: {len(datasets)}")
        
        for dataset in datasets:
            print(f"   - {dataset}")
            
        # Check specifically for GLBX.MDP3
        if "GLBX.MDP3" in [str(d) for d in datasets]:
            print("\n✓ GLBX.MDP3 is available in Historical API")
        else:
            print("\n✗ GLBX.MDP3 not found in available datasets")
            
    except Exception as e:
        print(f"✗ Historical API error: {e}")
    
    # Check Live API datasets
    print("\n\n2. Testing Live API with different datasets:")
    print("-"*40)
    
    # Common Databento datasets to test
    test_datasets = [
        "GLBX.MDP3",      # CME Globex
        "XNAS.ITCH",      # NASDAQ
        "OPRA.PILLAR",    # Options
        "DBEQ.BASIC",     # Equities
    ]
    
    for dataset_name in test_datasets:
        print(f"\nTesting {dataset_name}...")
        
        try:
            # Create dataset enum from string
            dataset_enum = getattr(db.Dataset, dataset_name.replace(".", "_"), None)
            
            if dataset_enum is None:
                print(f"   ✗ Dataset {dataset_name} not found in db.Dataset enum")
                continue
                
            client = db.Live(key=api_key)
            
            # Try a simple subscription
            client.subscribe(
                dataset=dataset_enum,
                schema=db.Schema.TRADES,
                symbols=["*"],  # All symbols
                stype_in=db.SType.RAW_SYMBOL,
                start=0,
            )
            
            print(f"   ✓ {dataset_name} - Subscription successful!")
            client.stop()
            
        except db.common.error.BentoError as e:
            if "live data license" in str(e):
                print(f"   ✗ {dataset_name} - No live data license")
            elif "authentication" in str(e).lower():
                print(f"   ✗ {dataset_name} - Authentication failed")
            else:
                print(f"   ✗ {dataset_name} - Error: {e}")
        except Exception as e:
            print(f"   ✗ {dataset_name} - Unexpected error: {e}")
    
    # Provide guidance
    print("\n\n3. Next Steps:")
    print("-"*40)
    print("Based on the error 'A live data license is required to access GLBX.MDP3':")
    print("1. Your API key is valid (Historical API works)")
    print("2. But it doesn't have live data access for GLBX.MDP3")
    print("3. Contact Databento support to add live GLBX.MDP3 access to your subscription")
    print("4. Or check your Databento portal to see which datasets have live access enabled")
    print("\nDatabento Portal: https://databento.com/portal/")

if __name__ == "__main__":
    check_access()
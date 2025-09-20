#!/usr/bin/env python3
"""
Test Databento Reference API methods we haven't tried yet
Based on documentation found via web search
"""

import databento as db
import json
from datetime import datetime, timedelta

def main():
    """Test unexplored Databento API methods"""
    print("🔍 TESTING UNEXPLORED DATABENTO API METHODS")
    print("="*60)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    today = datetime.now().date()
    
    # Test 1: Symbology Resolution
    print("\n📋 TEST 1: Symbology Resolution")
    print("-" * 40)
    
    try:
        # Try to resolve Q3C symbols
        symbols_to_resolve = ["Q3C", "Q3CN25", "Q3C N25", "NQ", "NQU5"]
        
        print("🔍 Testing symbology.resolve() method...")
        
        # Note: This method might not exist, but let's try based on docs
        if hasattr(client, 'symbology'):
            resolved = client.symbology.resolve(
                dataset="GLBX.MDP3",
                symbols=symbols_to_resolve,
                start=today
            )
            print(f"✅ Symbology resolution successful!")
            print(f"📊 Results: {resolved}")
        else:
            print("❌ symbology.resolve() method not found")
            
    except Exception as e:
        print(f"❌ Symbology resolution error: {e}")
    
    # Test 2: Metadata methods we haven't tried
    print("\n📋 TEST 2: Additional Metadata Methods")
    print("-" * 40)
    
    try:
        # List available datasets
        if hasattr(client.metadata, 'list_datasets'):
            print("🔍 Testing metadata.list_datasets()...")
            datasets = client.metadata.list_datasets()
            print(f"✅ Available datasets: {datasets}")
        
        # Get dataset schema
        if hasattr(client.metadata, 'get_dataset_schemas'):
            print("\n🔍 Testing metadata.get_dataset_schemas()...")
            schemas = client.metadata.get_dataset_schemas(dataset="GLBX.MDP3")
            print(f"✅ Available schemas: {schemas}")
        
        # Get dataset range
        if hasattr(client.metadata, 'get_dataset_range'):
            print("\n🔍 Testing metadata.get_dataset_range()...")
            date_range = client.metadata.get_dataset_range(dataset="GLBX.MDP3")
            print(f"✅ Dataset date range: {date_range}")
            
    except Exception as e:
        print(f"❌ Metadata methods error: {e}")
    
    # Test 3: Parent symbology approach (from docs)
    print("\n📋 TEST 3: Parent Symbology for Options Chains")
    print("-" * 40)
    
    try:
        print("🔍 Testing parent symbology with 'NQ' symbol...")
        
        # Try to get all NQ options using parent symbol
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ",  # Parent symbol
            schema="definition",
            start=today - timedelta(days=1),
            end=today,
            stype_in="parent"  # Specify parent symbology
        )
        
        df = data.to_df()
        print(f"📊 Found {len(df)} instruments using parent symbol")
        
        if len(df) > 0:
            # Filter for options
            if 'instrument_class' in df.columns:
                options = df[df['instrument_class'].isin(['O', 'OPT'])]
                print(f"🎯 Found {len(options)} options instruments")
                
                if len(options) > 0:
                    print("✅ OPTIONS FOUND VIA PARENT SYMBOLOGY!")
                    # Check for July 16 expiration
                    if 'expiration' in options.columns:
                        july_16_options = options[options['expiration'].str.contains('2025-07-16', na=False)]
                        print(f"📅 July 16, 2025 options: {len(july_16_options)}")
            
    except Exception as e:
        print(f"❌ Parent symbology error: {e}")
    
    # Test 4: Check for reference data endpoints
    print("\n📋 TEST 4: Reference Data Endpoints")
    print("-" * 40)
    
    try:
        # Check if there's a reference API
        if hasattr(db, 'Reference'):
            print("🔍 Testing Reference API...")
            ref_client = db.Reference("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
            
            # Try to get instrument info
            if hasattr(ref_client, 'get_instrument'):
                instrument = ref_client.get_instrument(
                    dataset="GLBX.MDP3",
                    symbol="NQ"
                )
                print(f"✅ Reference data: {instrument}")
        else:
            print("❌ No Reference API found")
            
    except Exception as e:
        print(f"❌ Reference API error: {e}")
    
    # Test 5: Get cost estimation
    print("\n📋 TEST 5: Cost Estimation for Options Data")
    print("-" * 40)
    
    try:
        if hasattr(client.metadata, 'get_cost'):
            print("🔍 Testing metadata.get_cost() for NQ options...")
            
            cost = client.metadata.get_cost(
                dataset="GLBX.MDP3",
                symbols="NQ",
                schema="trades",
                start="2025-07-15",
                end="2025-07-16",
                stype_in="parent"
            )
            
            print(f"✅ Cost estimation: ${cost}")
            
    except Exception as e:
        print(f"❌ Cost estimation error: {e}")
    
    # Test 6: Batch download API
    print("\n📋 TEST 6: Batch Download API")
    print("-" * 40)
    
    try:
        if hasattr(client, 'batch'):
            print("🔍 Testing batch download API...")
            
            # Submit batch job for NQ options
            job = client.batch.submit_job(
                dataset="GLBX.MDP3",
                symbols="NQ",
                schema="definition",
                start="2025-07-15",
                end="2025-07-16",
                stype_in="parent"
            )
            
            print(f"✅ Batch job submitted: {job}")
            
            # Check job status
            if hasattr(job, 'get_status'):
                status = job.get_status()
                print(f"📊 Job status: {status}")
                
    except Exception as e:
        print(f"❌ Batch API error: {e}")
    
    print(f"\n🎯 Reference API testing complete!")

if __name__ == "__main__":
    main()
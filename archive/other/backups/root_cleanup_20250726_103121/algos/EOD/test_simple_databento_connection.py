#!/usr/bin/env python3
"""
Test basic Databento connection to see if API key is still valid
"""

import databento as db

def test_basic_connection():
    """Test basic API connection"""
    print("🔍 TESTING BASIC DATABENTO CONNECTION")
    print("="*50)
    
    try:
        client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
        
        # Test 1: Simple metadata call
        print("📋 TEST 1: List datasets")
        datasets = client.metadata.list_datasets()
        print(f"✅ Datasets: {len(datasets)} found")
        print(f"   Sample: {datasets[:5]}")
        
        # Test 2: Try a simple data call that worked before
        print("\n📋 TEST 2: Test NQ futures (known to work)")
        nq_data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols=["NQU5"],
            schema="trades",
            start="2025-07-16",
            end="2025-07-17",
            limit=5
        )
        
        nq_df = nq_data.to_df()
        print(f"✅ NQ futures: {len(nq_df)} trades found")
        
        # Test 3: Try NQ.OPT that worked before
        print("\n📋 TEST 3: Test NQ.OPT (worked before)")
        nq_opt_data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="definition",
            start="2025-07-16",
            end="2025-07-17",
            stype_in="parent",
            limit=10
        )
        
        nq_opt_df = nq_opt_data.to_df()
        print(f"✅ NQ.OPT: {len(nq_opt_df)} options found")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic connection error: {e}")
        return False

def test_es_options():
    """Test ES options specifically"""
    print("\n🔍 TESTING ES OPTIONS ACCESS")
    print("="*50)
    
    try:
        client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
        
        # Test ES.OPT with Historical API
        print("📋 Testing ES.OPT with Historical API...")
        
        es_data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="ES.OPT",
            schema="definition",
            start="2025-07-16",
            end="2025-07-17",
            stype_in="parent",
            limit=50
        )
        
        es_df = es_data.to_df()
        print(f"✅ ES.OPT found: {len(es_df)} options")
        
        if len(es_df) > 0:
            print("\n📊 Sample ES options:")
            for symbol in es_df['symbol'].head(10):
                print(f"   {symbol}")
            
            # Check expiration dates
            if 'expiration' in es_df.columns:
                unique_exps = es_df['expiration'].unique()
                print(f"\n📅 ES expiration dates: {len(unique_exps)}")
                for exp in sorted(unique_exps)[:5]:
                    print(f"   {exp}")
        
        return True
        
    except Exception as e:
        print(f"❌ ES options error: {e}")
        return False

if __name__ == "__main__":
    basic_ok = test_basic_connection()
    
    if basic_ok:
        test_es_options()
    else:
        print("\n⚠️  Basic connection failed - API key may have expired or been revoked")
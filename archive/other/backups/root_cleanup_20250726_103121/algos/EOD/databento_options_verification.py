#!/usr/bin/env python3
"""
Databento NQ Options Verification
Test if Databento actually has NQ options despite our previous findings
"""

import databento as db
import json
from datetime import datetime, timedelta

def main():
    """Verify if Databento has NQ options"""
    print("🔍 DATABENTO NQ OPTIONS VERIFICATION")
    print("="*60)
    print("Based on web search: Databento claims to have NQ options at:")
    print("https://databento.com/catalog/cme/GLBX.MDP3/options/NQ")
    print("="*60)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    today = datetime.now().date()
    
    # Test various NQ options approaches based on their claims
    print("\n📋 Testing NQ options with different approaches...")
    
    # 1. Test if they have a different symbol format for options
    option_symbols_to_test = [
        # Standard CME options naming
        "OEQU25",    # Options on equity, September 2025
        "OQNU25",    # Options on QN (Nasdaq), September 2025
        "ONQU25",    # Options on NQ, September 2025
        
        # Weekly options formats
        "1NQU25",    # Week 1 NQ
        "2NQU25",    # Week 2 NQ
        "3NQU25",    # Week 3 NQ
        "W1NQU25",   # Week 1 format
        "W3NQU25",   # Week 3 format
        
        # Different prefix attempts
        "NQOP",      # NQ Options
        "NQOPT",     # NQ Options
        "ONQ",       # Options on NQ
        "NQCALL",    # NQ Call
        "NQPUT",     # NQ Put
        
        # Try the futures with option suffixes
        "NQU5C20000", # Call at 20000 strike
        "NQU5P20000", # Put at 20000 strike
        "NQU5C21000", # Call at 21000 strike
        "NQU5P21000", # Put at 21000 strike
    ]
    
    found_options = []
    
    for symbol in option_symbols_to_test:
        print(f"\n🔍 Testing symbol: {symbol}")
        try:
            # Try multiple schemas
            for schema in ["trades", "ohlcv-1s", "definition"]:
                try:
                    data = client.timeseries.get_range(
                        dataset="GLBX.MDP3",
                        symbols=symbol,
                        schema=schema,
                        start=today - timedelta(days=1),
                        end=today,
                        limit=5
                    )
                    
                    df = data.to_df()
                    if len(df) > 0:
                        print(f"   ✅ Found data with {schema} schema: {len(df)} records")
                        found_options.append({
                            'symbol': symbol,
                            'schema': schema,
                            'records': len(df)
                        })
                        
                        # Get more details
                        if 'symbol' in df.columns:
                            unique_symbols = df['symbol'].unique()
                            print(f"      Actual symbols: {list(unique_symbols[:3])}")
                        
                        break  # Found data, no need to test other schemas
                        
                except Exception as e:
                    if "422" not in str(e):
                        pass  # Ignore symbol not found
            
        except Exception as e:
            if "422" not in str(e):
                print(f"   ⚠️  Unexpected error: {str(e)[:50]}...")
    
    # 2. Try parent symbology approach for options
    print("\n" + "="*40)
    print("🔍 TESTING PARENT SYMBOLOGY FOR OPTIONS")
    print("="*40)
    
    parent_symbols = ["NQ.OPT", "NQ_OPT", "NQ-OPT", "NQOPT"]
    
    for parent in parent_symbols:
        print(f"\n🔍 Testing parent symbol: {parent}")
        try:
            # Try to get data using parent symbol
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols=parent,
                schema="trades",
                start=today - timedelta(days=1),
                end=today,
                limit=10
            )
            
            df = data.to_df()
            if len(df) > 0:
                print(f"   ✅ Found {len(df)} records with parent symbol!")
                found_options.append({
                    'symbol': parent,
                    'schema': 'trades',
                    'records': len(df),
                    'type': 'parent'
                })
            
        except Exception as e:
            if "422" not in str(e):
                print(f"   ⚠️  Error: {str(e)[:50]}...")
    
    # 3. Check if we're missing something in our dataset query
    print("\n" + "="*40)
    print("🔍 CHECKING DATASET CAPABILITIES")
    print("="*40)
    
    print("📊 Available schemas in GLBX.MDP3:")
    # List schemas that work
    working_schemas = []
    test_schemas = ["trades", "ohlcv-1s", "ohlcv-1m", "definition", "mbo", "mbp-1", "mbp-10"]
    
    for schema in test_schemas:
        try:
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols="NQU5",  # We know this works
                schema=schema,
                start=today - timedelta(days=1),
                end=today,
                limit=1
            )
            df = data.to_df()
            if len(df) > 0:
                working_schemas.append(schema)
                print(f"   ✅ {schema}")
        except Exception as e:
            print(f"   ❌ {schema}: {str(e)[:50]}...")
    
    # Summary
    print("\n" + "="*60)
    print("📋 VERIFICATION RESULTS")
    print("="*60)
    
    if found_options:
        print(f"\n✅ Found {len(found_options)} potential NQ options!")
        for opt in found_options:
            print(f"   • {opt['symbol']} ({opt['schema']}): {opt['records']} records")
            
        # Save results
        with open("found_nq_options.json", "w") as f:
            json.dump(found_options, f, indent=2)
        print(f"\n💾 Saved findings to found_nq_options.json")
        
    else:
        print("\n❌ NO NQ options found despite Databento's claims")
        print("\nPossible explanations:")
        print("   1. Different symbol format not tested")
        print("   2. Options data in separate dataset")
        print("   3. Special API access required")
        print("   4. Marketing claim vs actual data availability")
    
    print(f"\n📊 Working schemas: {working_schemas}")
    print("\n🎯 Verification complete!")

if __name__ == "__main__":
    main()
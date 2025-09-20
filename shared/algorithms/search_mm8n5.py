#!/usr/bin/env python3
"""
Search for MM8N5 symbol in Databento
"""

import databento as db
import pandas as pd

def main():
    """Search for MM8N5 symbol"""
    print("🔍 SEARCHING FOR MM8N5 SYMBOL")
    print("="*50)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    
    try:
        # Test 1: Direct symbol search
        print("📋 TEST 1: Direct symbol search for MM8N5")
        print("-" * 40)
        
        try:
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols=["MM8N5"],
                schema="trades",
                start="2025-07-15",
                end="2025-07-17",
                limit=100
            )
            
            df = data.to_df()
            print(f"✅ Found {len(df)} trades for MM8N5")
            
            if len(df) > 0:
                print(f"📊 MM8N5 trade data:")
                print(df[['symbol', 'price', 'size', 'ts_event']].head(10))
                
                # Get basic stats
                latest_price = df['price'].iloc[-1]
                total_volume = df['size'].sum()
                avg_price = df['price'].mean()
                
                print(f"\n📈 MM8N5 Summary:")
                print(f"   Latest Price: ${latest_price:.2f}")
                print(f"   Average Price: ${avg_price:.2f}")
                print(f"   Total Volume: {total_volume:,} contracts")
            
        except Exception as e:
            print(f"❌ Direct search failed: {e}")
        
        # Test 2: Search all symbols containing "MM8"
        print(f"\n📋 TEST 2: Search for symbols containing 'MM8'")
        print("-" * 40)
        
        try:
            # Get broader NQ data and filter
            trades = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols="NQ.OPT",
                schema="trades",
                start="2025-07-15",
                end="2025-07-17",
                stype_in="parent",
                limit=2000
            )
            
            trades_df = trades.to_df()
            print(f"✅ Retrieved {len(trades_df)} total option trades")
            
            # Search for symbols containing MM8
            mm8_symbols = []
            unique_symbols = trades_df['symbol'].unique()
            
            for symbol in unique_symbols:
                if 'MM8' in str(symbol):
                    mm8_symbols.append(symbol)
            
            print(f"📊 Found {len(mm8_symbols)} symbols containing 'MM8':")
            for symbol in mm8_symbols:
                print(f"   {symbol}")
                
            # Search for symbols containing parts of MM8N5
            broader_matches = []
            for symbol in unique_symbols:
                if any(part in str(symbol) for part in ['MM8', 'M8N', 'N5', '8N5']):
                    broader_matches.append(symbol)
            
            if broader_matches:
                print(f"\n📊 Broader matches (MM8, M8N, N5, 8N5):")
                for symbol in broader_matches[:20]:  # Show first 20
                    print(f"   {symbol}")
            
        except Exception as e:
            print(f"❌ Broad search failed: {e}")
        
        # Test 3: Check if MM8N5 is a different dataset
        print(f"\n📋 TEST 3: Check other datasets for MM8N5")
        print("-" * 40)
        
        # Get available datasets
        datasets = client.metadata.list_datasets()
        print(f"Available datasets: {datasets}")
        
        # Test some common datasets that might have MM8N5
        test_datasets = ["GLBX.MDP3", "DBEQ.BASIC", "OPRA.PILLAR"]
        
        for dataset in test_datasets:
            if dataset in datasets:
                print(f"\n🔍 Testing {dataset} for MM8N5...")
                try:
                    test_data = client.timeseries.get_range(
                        dataset=dataset,
                        symbols=["MM8N5"],
                        schema="trades",
                        start="2025-07-16",
                        end="2025-07-17",
                        limit=10
                    )
                    
                    test_df = test_data.to_df()
                    if len(test_df) > 0:
                        print(f"   ✅ FOUND MM8N5 in {dataset}!")
                        print(f"   📊 {len(test_df)} trades found")
                        print(test_df[['symbol', 'price', 'size']].head())
                    else:
                        print(f"   ❌ No data in {dataset}")
                        
                except Exception as e:
                    print(f"   ⚠️  {dataset} error: {str(e)[:50]}...")
        
        # Test 4: Try symbology resolution
        print(f"\n📋 TEST 4: Try symbology resolution for MM8N5")
        print("-" * 40)
        
        try:
            # Test if MM8N5 can be resolved
            resolved = client.symbology.resolve(
                dataset="GLBX.MDP3",
                symbols=["MM8N5"],
                stype_in="native",
                stype_out="instrument_id",
                start_date="2025-07-16"
            )
            
            print(f"✅ Symbology resolution:")
            for symbol, result in resolved.items():
                print(f"   {symbol} → {result}")
                
        except Exception as e:
            print(f"❌ Symbology resolution failed: {e}")
        
        # Test 5: Search for similar micro contract patterns
        print(f"\n📋 TEST 5: Search for micro contract patterns")
        print("-" * 40)
        
        try:
            # MM8N5 might be a micro contract - search for similar patterns
            micro_patterns = ['MNQ', 'MNQU5', 'MNQZ5', 'M2K', 'MES', 'MYM']
            
            for pattern in micro_patterns:
                try:
                    micro_data = client.timeseries.get_range(
                        dataset="GLBX.MDP3",
                        symbols=[pattern],
                        schema="trades",
                        start="2025-07-16",
                        end="2025-07-17",
                        limit=5
                    )
                    
                    micro_df = micro_data.to_df()
                    if len(micro_df) > 0:
                        print(f"   ✅ Found {pattern}: {len(micro_df)} trades")
                    
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Micro pattern search failed: {e}")
        
        # Test 6: Check instrument definitions
        print(f"\n📋 TEST 6: Check instrument definitions for MM8N5")
        print("-" * 40)
        
        try:
            definition = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols=["MM8N5"],
                schema="definition",
                start="2025-07-15",
                end="2025-07-17",
                limit=10
            )
            
            def_df = definition.to_df()
            if len(def_df) > 0:
                print(f"✅ Found MM8N5 definition:")
                print(def_df[['symbol', 'raw_symbol', 'security_type', 'underlying']].head())
            else:
                print(f"❌ No definition found for MM8N5")
                
        except Exception as e:
            print(f"❌ Definition search failed: {e}")
        
        print(f"\n🎯 MM8N5 search complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
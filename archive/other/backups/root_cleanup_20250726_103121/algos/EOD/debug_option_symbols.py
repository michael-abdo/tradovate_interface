#!/usr/bin/env python3
"""
Debug the option symbol format issue
"""

import databento as db
import pandas as pd

def main():
    """Debug symbol format"""
    print("🔍 DEBUGGING NQ OPTION SYMBOL FORMAT")
    print("="*50)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    
    try:
        # Get a smaller sample first
        print("📋 Getting small sample of NQ options...")
        
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="definition",
            start="2025-07-17",
            end="2025-07-17",
            stype_in="parent",
            limit=50
        )
        
        df = data.to_df()
        print(f"✅ Retrieved {len(df)} NQ options")
        
        # Check different symbol fields
        print(f"\n📊 Symbol field analysis:")
        
        if 'symbol' in df.columns:
            print(f"   symbol column samples:")
            for i, sym in enumerate(df['symbol'].head(10)):
                print(f"     {i}: '{sym}'")
        
        if 'raw_symbol' in df.columns:
            print(f"\n   raw_symbol column samples:")
            for i, sym in enumerate(df['raw_symbol'].head(10)):
                print(f"     {i}: '{sym}'")
        
        # Check if there's a different way to get proper symbols
        print(f"\n📋 Trying trades schema to see symbol format...")
        
        trades = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="trades",
            start="2025-07-17",
            end="2025-07-17",
            stype_in="parent",
            limit=20
        )
        
        trades_df = trades.to_df()
        print(f"✅ Retrieved {len(trades_df)} option trades")
        
        if len(trades_df) > 0:
            print(f"\n📊 Trade symbols:")
            unique_symbols = trades_df['symbol'].unique()
            for i, sym in enumerate(unique_symbols[:10]):
                print(f"     {i}: '{sym}'")
            
            # Look for symbols that contain 23175
            matches_23175 = [s for s in unique_symbols if '23175' in str(s)]
            print(f"\n🎯 Symbols containing '23175': {matches_23175}")
            
            # Look for symbols that contain 'C23' or 'P23' (calls/puts near 23xxx)
            matches_23xxx = [s for s in unique_symbols if any(x in str(s) for x in ['C23', 'P23'])]
            print(f"🎯 Symbols with C23/P23: {matches_23xxx[:20]}")
            
            # Show a sample of actual option trades
            print(f"\n📈 Sample option trades:")
            sample_trades = trades_df[['symbol', 'price', 'size', 'ts_event']].head(10)
            print(sample_trades)
            
            # Try to get market data for one of the symbols
            if len(unique_symbols) > 0:
                test_symbol = unique_symbols[0]
                print(f"\n📊 Testing market data for: {test_symbol}")
                
                try:
                    single_trades = client.timeseries.get_range(
                        dataset="GLBX.MDP3",
                        symbols=[test_symbol],
                        schema="trades",
                        start="2025-07-17",
                        end="2025-07-17",
                        limit=10
                    )
                    
                    single_df = single_trades.to_df()
                    if len(single_df) > 0:
                        latest_price = single_df['price'].iloc[-1]
                        print(f"   Latest price: ${latest_price:.2f}")
                        
                except Exception as e:
                    print(f"   Error: {e}")
        
        # Try to get current NQ futures price for reference
        print(f"\n📊 Getting NQ futures for reference...")
        
        nq_data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols=["NQU5"],
            schema="trades",
            start="2025-07-17",
            end="2025-07-17",
            limit=5
        )
        
        nq_df = nq_data.to_df()
        if len(nq_df) > 0:
            nq_price = nq_df['price'].iloc[-1]
            print(f"   Current NQ futures price: ${nq_price:.2f}")
            
            # Based on current price, what strikes would be reasonable?
            print(f"\n💡 Reasonable call strikes around current price:")
            for offset in [-500, -250, 0, 250, 500]:
                strike = nq_price + offset
                print(f"   ${strike:.0f} call")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
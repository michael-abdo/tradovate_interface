#!/usr/bin/env python3
"""
Check yesterday's option data to see proper symbol format
"""

import databento as db
import pandas as pd

def main():
    """Check yesterday's options for symbol format"""
    print("🔍 CHECKING YESTERDAY'S NQ OPTIONS FOR SYMBOL FORMAT")
    print("="*60)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    
    try:
        # Get trades from yesterday
        print("📋 Getting NQ option trades from yesterday...")
        
        trades = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="trades",
            start="2025-07-16",
            end="2025-07-17",
            stype_in="parent",
            limit=100
        )
        
        trades_df = trades.to_df()
        print(f"✅ Retrieved {len(trades_df)} option trades")
        
        if len(trades_df) > 0:
            print(f"\n📊 Sample option symbols from trades:")
            unique_symbols = trades_df['symbol'].unique()
            print(f"   Total unique symbols: {len(unique_symbols)}")
            
            for i, sym in enumerate(unique_symbols[:20]):
                print(f"     {i+1}: '{sym}'")
            
            # Look for patterns in symbols
            print(f"\n🔍 Symbol pattern analysis:")
            
            # Look for calls and puts
            calls = [s for s in unique_symbols if ' C' in str(s)]
            puts = [s for s in unique_symbols if ' P' in str(s)]
            
            print(f"   Calls (contain ' C'): {len(calls)}")
            print(f"   Puts (contain ' P'): {len(puts)}")
            
            if len(calls) > 0:
                print(f"\n📊 Sample call options:")
                for call in calls[:10]:
                    print(f"     {call}")
            
            # Look for strikes around 23000-24000
            high_strikes = [s for s in unique_symbols if any(x in str(s) for x in ['23', '24'])]
            print(f"\n🎯 Options with strikes containing '23' or '24': {len(high_strikes)}")
            
            for strike in high_strikes[:15]:
                print(f"     {strike}")
            
            # Get some trade details
            print(f"\n📈 Recent option trades:")
            recent = trades_df[['symbol', 'price', 'size', 'ts_event']].tail(20)
            print(recent)
            
            # Try to find strikes by looking at price patterns
            print(f"\n💰 Price analysis:")
            price_stats = trades_df['price'].describe()
            print(price_stats)
            
            # Look for expensive options (likely calls near money)
            expensive_trades = trades_df[trades_df['price'] > 100]  # Options > $100
            if len(expensive_trades) > 0:
                print(f"\n💎 Expensive options (price > $100):")
                exp_symbols = expensive_trades['symbol'].unique()[:10]
                for sym in exp_symbols:
                    sym_trades = expensive_trades[expensive_trades['symbol'] == sym]
                    latest_price = sym_trades['price'].iloc[-1]
                    print(f"     {sym}: ${latest_price:.2f}")
            
            # Check current NQ price for context
            print(f"\n📊 Getting current NQ futures price...")
            nq_data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols=["NQU5"],
                schema="trades",
                start="2025-07-16",
                end="2025-07-17",
                limit=5
            )
            
            nq_df = nq_data.to_df()
            if len(nq_df) > 0:
                nq_price = nq_df['price'].iloc[-1]
                print(f"   NQ futures price: ${nq_price:.2f}")
                
                # Find options that might be near this strike
                target_strike = 23175
                print(f"\n🎯 Looking for options near ${target_strike} strike...")
                
                # Search for symbols containing parts of this number
                possible_matches = []
                for sym in unique_symbols:
                    if any(x in str(sym) for x in ['23175', '231', '175']):
                        possible_matches.append(sym)
                
                if possible_matches:
                    print(f"   Possible matches: {possible_matches}")
                else:
                    print(f"   No direct matches found for 23175")
                    
                    # Try broader search
                    broad_matches = [s for s in unique_symbols if '231' in str(s)]
                    print(f"   Symbols containing '231': {broad_matches[:10]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
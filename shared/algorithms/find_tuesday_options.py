#!/usr/bin/env python3
"""Find today's Tuesday NQ options and highest volume strikes"""

import databento as db
from datetime import datetime

print("Finding Tuesday NQ Options for July 22, 2025")
print("="*70)

client = db.Historical("db-vWDhkTNKbF4pux7LuDGY78hspCaVJ")

try:
    # Try Tuesday options symbols D1B through D5B
    print("Checking Tuesday options (D1B-D5B format)...")
    
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=["D1B.OPT", "D2B.OPT", "D3B.OPT", "D4B.OPT", "D5B.OPT"],
        stype_in="parent",
        schema="trades",
        start="2025-07-21",
        end="2025-07-22"
    )
    
    df = data.to_df()
    
    if len(df) > 0:
        print(f"\n✅ Found {len(df)} trades for Tuesday options")
        
        # Get unique symbols and their patterns
        unique_symbols = df['symbol'].unique()
        print(f"\n📊 Unique symbols found: {len(unique_symbols)}")
        
        # Check which week patterns exist
        week_patterns = set()
        for sym in unique_symbols:
            if sym.startswith('D') and 'B' in sym:
                week_patterns.add(sym[:3])
        
        print(f"\nWeek patterns found: {sorted(week_patterns)}")
        
        # Aggregate volume by symbol
        volume_by_symbol = df.groupby('symbol')['size'].sum().sort_values(ascending=False)
        
        print(f"\n🏆 TOP 20 TUESDAY OPTIONS BY VOLUME:")
        print("-" * 70)
        for i, (symbol, volume) in enumerate(volume_by_symbol.head(20).items(), 1):
            # Extract strike price
            strike = "N/A"
            if ' C' in symbol:
                strike = symbol.split(' C')[1]
            elif ' P' in symbol:
                strike = symbol.split(' P')[1]
            
            option_type = "Call" if ' C' in symbol else "Put"
            
            print(f"{i:2d}. {symbol:20s} | Volume: {volume:6,} | Strike: {strike:>6s} | {option_type}")
        
        # Find today's specific symbol (D4BN5 for Week 4 Tuesday July)
        d4b_symbols = [s for s in unique_symbols if s.startswith('D4BN5')]
        
        if d4b_symbols:
            print(f"\n📅 TODAY'S SYMBOLS (D4BN5 - Week 4 Tuesday):")
            d4b_volume = volume_by_symbol[volume_by_symbol.index.str.startswith('D4BN5')].sort_values(ascending=False)
            
            print(f"Found {len(d4b_symbols)} D4BN5 options")
            print("\nTop 10 by volume:")
            for symbol, volume in d4b_volume.head(10).items():
                strike = "N/A"
                if ' C' in symbol:
                    strike = symbol.split(' C')[1]
                elif ' P' in symbol:
                    strike = symbol.split(' P')[1]
                option_type = "Call" if ' C' in symbol else "Put"
                print(f"  {symbol:20s} | Volume: {volume:6,} | Strike: {strike:>6s} | {option_type}")
        else:
            print(f"\n⚠️ No D4BN5 (Week 4 Tuesday) options found in data")
            
        # Summary
        print(f"\n📊 SUMMARY:")
        print(f"Total Tuesday options volume: {volume_by_symbol.sum():,}")
        print(f"Highest volume option: {volume_by_symbol.index[0]} with {volume_by_symbol.iloc[0]:,} contracts")
        
        if ' C' in volume_by_symbol.index[0]:
            strike = volume_by_symbol.index[0].split(' C')[1]
        elif ' P' in volume_by_symbol.index[0]:
            strike = volume_by_symbol.index[0].split(' P')[1]
        else:
            strike = "Unknown"
            
        print(f"Highest volume strike: {strike}")
        
    else:
        print("\n⚠️ No Tuesday options trades found")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
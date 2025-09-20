#!/usr/bin/env python3
"""Analyze volume data for weekly NQ options"""

import databento as db
import pandas as pd

print("Analyzing Weekly Options Volume Data")
print("="*70)

client = db.Historical("db-vWDhkTNKbF4pux7LuDGY78hspCaVJ")

try:
    # Get the data with trades schema to see actual volume
    print("Requesting TRADES data for weekly options...")
    
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=["Q1A.OPT", "Q2A.OPT", "Q3A.OPT", "Q4A.OPT", "Q5A.OPT"],
        stype_in="parent",
        schema="trades",  # Changed to trades to see actual volume
        start="2025-07-14",
        end="2025-07-17"
    )
    
    df = data.to_df()
    
    if len(df) > 0:
        print(f"\n✅ Retrieved {len(df)} trades")
        
        # Aggregate volume by symbol
        volume_by_symbol = df.groupby('symbol')['size'].sum().sort_values(ascending=False)
        
        print(f"\n📊 VOLUME ANALYSIS:")
        print(f"Total unique symbols: {len(volume_by_symbol)}")
        print(f"Total volume across all weekly options: {volume_by_symbol.sum():,}")
        
        print(f"\n🏆 TOP 20 WEEKLY OPTIONS BY VOLUME:")
        print("-" * 60)
        for i, (symbol, volume) in enumerate(volume_by_symbol.head(20).items(), 1):
            print(f"{i:2d}. {symbol:15s} | Volume: {volume:6,} contracts")
        
        # Analyze by option type (Q3A, Q4A, etc)
        df['base_symbol'] = df['symbol'].str[:3]
        volume_by_type = df.groupby('base_symbol')['size'].sum().sort_values(ascending=False)
        
        print(f"\n📊 VOLUME BY WEEKLY TYPE:")
        print("-" * 40)
        for base, volume in volume_by_type.items():
            print(f"{base}: {volume:,} contracts")
        
        # Check for any high volume options (>100 contracts)
        high_volume = volume_by_symbol[volume_by_symbol > 100]
        print(f"\n🔥 HIGH VOLUME OPTIONS (>100 contracts):")
        if len(high_volume) > 0:
            for symbol, volume in high_volume.items():
                print(f"  - {symbol}: {volume:,} contracts")
        else:
            print("  None found")
            
        # Get date range of trades
        print(f"\n📅 Trade dates:")
        print(f"First trade: {df.index.min()}")
        print(f"Last trade: {df.index.max()}")
        
    else:
        print("\n⚠️ No trades data returned")
        
        # Try OHLCV to at least see the volume field
        print("\nTrying OHLCV-1d schema instead...")
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols=["Q1A.OPT", "Q2A.OPT", "Q3A.OPT", "Q4A.OPT", "Q5A.OPT"],
            stype_in="parent",
            schema="ohlcv-1d",
            start="2025-07-14",
            end="2025-07-17"
        )
        
        df = data.to_df()
        if len(df) > 0 and 'volume' in df.columns:
            volume_summary = df.groupby('symbol')['volume'].sum().sort_values(ascending=False)
            
            print(f"\n📊 OHLCV VOLUME DATA:")
            print(f"Total symbols: {len(volume_summary)}")
            print(f"Total volume: {volume_summary.sum():,}")
            
            print("\nTop 10 by volume:")
            for symbol, volume in volume_summary.head(10).items():
                print(f"  {symbol}: {volume} contracts")
                
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
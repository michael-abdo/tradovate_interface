#!/usr/bin/env python3
"""Test Databento Historical API with weekly option symbols Q1A through Q5A"""

import databento as db
import pandas as pd

print("Testing Weekly Options Symbols (Q1A through Q5A)")
print("="*70)

client = db.Historical("db-vWDhkTNKbF4pux7LuDGY78hspCaVJ")

try:
    print("Requesting data for Q1A.OPT through Q5A.OPT...")
    print("Date range: Starting from 2025-07-15")
    print("-"*70)
    
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=["Q1A.OPT", "Q2A.OPT", "Q3A.OPT", "Q4A.OPT", "Q5A.OPT"],
        stype_in="parent",
        schema="ohlcv-1d",
        start="2025-07-15",
    )
    
    df = data.to_df()
    
    print(f"\n✅ Successfully retrieved data!")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    if len(df) > 0:
        print(f"\n📊 Data Summary:")
        print(f"Total records: {len(df)}")
        print(f"Unique symbols: {df['symbol'].nunique() if 'symbol' in df.columns else 'N/A'}")
        
        print("\n📋 First 10 rows:")
        print(df.head(10))
        
        if 'symbol' in df.columns:
            print("\n📊 Symbol breakdown:")
            symbol_counts = df['symbol'].value_counts()
            print(symbol_counts)
            
            print("\n🔍 Unique symbols found:")
            unique_symbols = sorted(df['symbol'].unique())
            for sym in unique_symbols[:20]:  # Show first 20
                print(f"  - {sym}")
            if len(unique_symbols) > 20:
                print(f"  ... and {len(unique_symbols) - 20} more")
    else:
        print("\n⚠️ No data returned for these symbols")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Try to get more details about the error
    if hasattr(e, 'args') and e.args:
        print(f"Error details: {e.args}")
        
print("\n" + "="*70)
print("Test complete")
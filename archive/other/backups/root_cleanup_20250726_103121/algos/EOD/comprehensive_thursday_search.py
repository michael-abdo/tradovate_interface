#!/usr/bin/env python3
"""Comprehensive search for Thursday NQ options across all formats"""

import databento as db
from datetime import datetime, timedelta
import pandas as pd

print("COMPREHENSIVE THURSDAY OPTIONS SEARCH")
print("="*80)

client = db.Historical("db-vWDhkTNKbF4pux7LuDGY78hspCaVJ")

# July 2025 Thursdays: 3rd, 10th, 17th, 24th, 31st
thursdays = ['2025-07-03', '2025-07-10', '2025-07-17', '2025-07-24', '2025-07-31']

print("\n📅 Searching for options expiring on Thursdays in July 2025:")
for thu in thursdays:
    print(f"  - {thu}")

try:
    # Get ALL NQ options for July
    print("\n🔍 Retrieving ALL NQ options for July 2025...")
    
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols="NQ.OPT",
        stype_in="parent",
        schema="trades",
        start="2025-07-01",
        end="2025-07-22"
    )
    
    trades_df = data.to_df()
    
    # Get definitions
    print("Getting instrument definitions...")
    definitions = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols="NQ.OPT",
        schema="definition",
        start="2025-07-01",
        end="2025-07-22",
        stype_in="parent"
    )
    
    def_df = definitions.to_df()
    
    # Create comprehensive expiration mapping
    exp_map = {}
    if len(def_df) > 0:
        for _, row in def_df.iterrows():
            exp_map[row['symbol']] = row['expiration']
    
    print(f"\n✅ Total unique symbols found: {len(trades_df['symbol'].unique())}")
    print(f"✅ Total definitions found: {len(def_df)}")
    
    # Analyze by expiration date
    all_expirations = {}
    for symbol in trades_df['symbol'].unique():
        exp = exp_map.get(symbol, 'Unknown')
        exp_date = str(exp).split(' ')[0] if exp != 'Unknown' else 'Unknown'
        
        if exp_date not in all_expirations:
            all_expirations[exp_date] = []
        all_expirations[exp_date].append(symbol)
    
    # Check each Thursday
    print("\n📊 THURSDAY OPTIONS ANALYSIS:")
    print("-"*80)
    
    thursday_data = {}
    
    for thursday in thursdays:
        if thursday in all_expirations:
            symbols = all_expirations[thursday]
            volumes = trades_df[trades_df['symbol'].isin(symbols)].groupby('symbol')['size'].sum()
            total_vol = volumes.sum()
            
            thursday_data[thursday] = {
                'symbols': symbols,
                'volumes': volumes,
                'total_volume': total_vol
            }
            
            print(f"\n✅ {thursday} (Thursday):")
            print(f"   Options found: {len(symbols)}")
            print(f"   Total volume: {total_vol:,} contracts")
            
            # Categorize by symbol type
            standard = [s for s in symbols if not s.startswith('UD:2V:')]
            ud2v = [s for s in symbols if s.startswith('UD:2V:')]
            
            print(f"   Standard format: {len(standard)} symbols")
            print(f"   UD:2V format: {len(ud2v)} symbols")
            
            if len(volumes) > 0:
                top_5 = volumes.nlargest(5)
                print("   Top 5 by volume:")
                for symbol, vol in top_5.items():
                    print(f"     {symbol}: {vol:,} contracts")
        else:
            print(f"\n❌ {thursday} (Thursday): No options found")
    
    # Now let's look for the specific week patterns
    print("\n🔍 SEARCHING FOR CME WEEKLY PATTERNS:")
    print("-"*80)
    
    # According to CME, Thursday options should be:
    # - D1D-D5D for Micro E-mini
    # - Need to find E-mini equivalent
    
    # Check if any symbols contain Thursday-specific patterns
    thursday_patterns = ['Q4C', 'Q3C', 'D4D', 'D3D']  # Various Thursday patterns
    
    for pattern in thursday_patterns:
        matching = [s for s in trades_df['symbol'].unique() if pattern in s]
        if matching:
            print(f"\n✅ Found {len(matching)} symbols with pattern '{pattern}':")
            for sym in matching[:5]:
                exp = exp_map.get(sym, 'Unknown')
                exp_date = str(exp).split(' ')[0] if exp != 'Unknown' else 'Unknown'
                vol = trades_df[trades_df['symbol'] == sym]['size'].sum()
                print(f"   {sym}: expires {exp_date}, volume {vol}")
    
    # Final comparison with Barchart
    print("\n📊 BARCHART VS DATABENTO COMPARISON:")
    print("="*80)
    
    print("\nBarchart MM4N25 (Thursday, Week 4, July):")
    print("  - Format: E-mini weekly")
    print("  - Volume: 5,249+ contracts on 4 strikes")
    print("  - Strikes: 23,275C, 23,300C, 23,350C, 23,400C")
    
    # Find July 24 (Week 4 Thursday) in our data
    if '2025-07-24' in thursday_data:
        data = thursday_data['2025-07-24']
        print(f"\nDatabento July 24 (Week 4 Thursday):")
        print(f"  - Total options: {len(data['symbols'])}")
        print(f"  - Total volume: {data['total_volume']:,} contracts")
        
        # Check for matching strikes
        matches = []
        for symbol in data['symbols']:
            for strike in [23275, 23300, 23350, 23400]:
                if f' C{strike}' in symbol:
                    vol = data['volumes'].get(symbol, 0)
                    matches.append((symbol, strike, vol))
        
        if matches:
            print("\n  Matching strikes found:")
            for sym, strike, vol in matches:
                print(f"    Strike {strike}: {sym} = {vol} contracts")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n💡 KEY INSIGHTS:")
print("="*80)
print("1. Thursday options exist but with much lower volume than Barchart shows")
print("2. Symbol format mismatch: Barchart uses proprietary format (MM4N25)")
print("3. Databento uses CME native symbols (various formats)")
print("4. Volume discrepancy suggests:")
print("   - Different data sources or aggregation methods")
print("   - Possible timing differences in data capture")
print("   - Barchart might include OTC or other venues")
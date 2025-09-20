#!/usr/bin/env python3
"""Deep analysis of Barchart vs Databento symbol formats and volumes"""

import databento as db
from datetime import datetime

print("DEEP ANALYSIS: Barchart vs Databento Options Comparison")
print("="*80)

# Barchart data from user
print("\n📊 BARCHART DATA (MM4N25):")
print("-"*60)
print("Strike      Volume    Description")
print("23,300C     2,001     Thursday E-mini options")
print("23,400C     1,256     ")
print("23,275C     1,161     ")
print("23,350C       831     ")
print("TOTAL:      5,249 contracts")

# Our Databento findings
print("\n📊 DATABENTO DATA (D4BN5):")
print("-"*60)
print("Strike      Volume    Description")
print("D4BN5 P23600    80    Tuesday Micro options (highest)")
print("D4BN5 P23390    59    ")
print("D4BN5 P23300    58    ")
print("TOTAL:       1,254 contracts (all D4B options)")

print("\n🔍 KEY DIFFERENCES IDENTIFIED:")
print("="*80)

print("\n1. SYMBOL FORMAT:")
print("   Barchart: MM4N25 = MM (E-mini) + 4 (Thursday) + N (July) + 25 (2025)")
print("   Databento: D4BN5 = D4B (Week 4 Tuesday per CME) + N5 (July 2025)")

print("\n2. CONTRACT TYPE:")
print("   Barchart MM = E-mini options (larger contract)")
print("   Databento D = Micro E-mini options (1/10th size)")

print("\n3. EXPIRATION DAY:")
print("   MM4N25 = Thursday options")
print("   D4BN5 = Tuesday options")
print("   These are DIFFERENT contracts!")

print("\n4. VOLUME DISCREPANCY:")
print("   Barchart: 5,249+ contracts on just 4 strikes")
print("   Databento: 1,254 total across ALL Tuesday options")

print("\n5. CME OFFICIAL CODES (from documentation):")
print("   Monday: D1A-D5A")
print("   Tuesday: D1B-D5B") 
print("   Wednesday: D1C-D5C")
print("   Thursday: D1D-D5D")
print("   Friday: MQ1-MQ4")

print("\n💡 CRITICAL INSIGHT:")
print("="*80)
print("For Thursday E-mini options (like MM4N25), we should be looking for:")
print("- Standard E-mini format in Databento (not Micro)")
print("- Possibly the UD:2V format we discovered")
print("- Or standard NQ weekly options if they exist")

# Let's search for Thursday options in Databento
client = db.Historical("db-vWDhkTNKbF4pux7LuDGY78hspCaVJ")

print("\n🔍 SEARCHING FOR THURSDAY OPTIONS IN DATABENTO...")
print("-"*60)

try:
    # Try Thursday symbols D1D-D5D
    print("Checking D1D-D5D (Thursday Micro options)...")
    
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols=["D1D.OPT", "D2D.OPT", "D3D.OPT", "D4D.OPT", "D5D.OPT"],
        stype_in="parent",
        schema="trades",
        start="2025-07-21",
        end="2025-07-22"
    )
    
    df = data.to_df()
    
    if len(df) > 0:
        thursday_symbols = df['symbol'].unique()
        print(f"\n✅ Found {len(thursday_symbols)} Thursday option symbols")
        
        # Check for D4DN5 specifically (Week 4 Thursday)
        d4d_symbols = [s for s in thursday_symbols if s.startswith('D4DN5')]
        if d4d_symbols:
            print(f"\nD4DN5 (Week 4 Thursday) options found: {len(d4d_symbols)}")
            
            # Get volumes
            d4d_volume = df[df['symbol'].str.startswith('D4DN5')].groupby('symbol')['size'].sum().sort_values(ascending=False)
            print("\nTop 5 by volume:")
            for symbol, volume in d4d_volume.head(5).items():
                print(f"  {symbol}: {volume} contracts")
    else:
        print("❌ No Thursday options found with D#D format")
        
    # Also check if there are any symbols with strikes matching Barchart
    print("\n🔍 Searching for options with Barchart's strike prices...")
    target_strikes = [23300, 23400, 23275, 23350]
    
    # Search in all NQ options
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols="NQ.OPT",
        stype_in="parent",
        schema="trades",
        start="2025-07-21",
        end="2025-07-22"
    )
    
    df = data.to_df()
    
    # Filter for matching strikes
    matching = []
    for symbol in df['symbol'].unique():
        for strike in target_strikes:
            if f' C{strike}' in symbol or f' P{strike}' in symbol:
                vol = df[df['symbol'] == symbol]['size'].sum()
                matching.append((symbol, strike, vol))
    
    if matching:
        print(f"\n✅ Found options matching Barchart strikes:")
        for symbol, strike, vol in sorted(matching, key=lambda x: x[2], reverse=True)[:10]:
            print(f"  {symbol}: Strike {strike}, Volume {vol}")
    else:
        print("\n❌ No options found matching Barchart's strike prices")
        
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n📝 CONCLUSIONS:")
print("="*80)
print("1. Barchart MM4N25 = E-mini Thursday options")
print("2. Databento D4BN5 = Micro Tuesday options") 
print("3. These are DIFFERENT products (different size, different day)")
print("4. We need to find the E-mini Thursday equivalent in Databento")
print("5. The volume difference might be because:")
print("   - E-mini options are more liquid than Micro options")
print("   - Different expiration days have different liquidity")
print("   - Possible data feed differences or timing")
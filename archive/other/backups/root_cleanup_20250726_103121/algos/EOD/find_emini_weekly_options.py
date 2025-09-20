#!/usr/bin/env python3
"""Search for E-mini (not Micro) weekly options in Databento"""

import databento as db
from datetime import datetime

print("SEARCHING FOR E-MINI WEEKLY OPTIONS IN DATABENTO")
print("="*80)

client = db.Historical("db-vWDhkTNKbF4pux7LuDGY78hspCaVJ")

# From CME documentation:
# E-mini weekly options should use different codes than Micro
# We need to find what Databento uses for E-mini weeklies

print("\n🔍 HYPOTHESIS: E-mini weeklies might be in UD:2V format")
print("Let's analyze UD:2V options by expiration date...")

try:
    # Get all NQ options including UD:2V
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols="NQ.OPT",
        stype_in="parent",
        schema="trades",
        start="2025-07-21",
        end="2025-07-22"
    )
    
    df = data.to_df()
    
    # Get instrument definitions to map expirations
    print("\nGetting instrument definitions...")
    definitions = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        symbols="NQ.OPT",
        schema="definition",
        start="2025-07-21",
        end="2025-07-22",
        stype_in="parent"
    )
    
    def_df = definitions.to_df()
    
    # Create expiration mapping
    exp_map = {}
    if len(def_df) > 0:
        for _, row in def_df.iterrows():
            exp_map[row['symbol']] = row['expiration']
    
    # Filter for UD:2V symbols
    ud2v_symbols = [s for s in df['symbol'].unique() if s.startswith('UD:2V:')]
    
    print(f"\n✅ Found {len(ud2v_symbols)} UD:2V symbols")
    
    # Analyze by expiration
    ud2v_exp = {}
    for symbol in ud2v_symbols:
        exp = exp_map.get(symbol, 'Unknown')
        exp_date = str(exp).split(' ')[0] if exp != 'Unknown' else 'Unknown'
        
        if exp_date not in ud2v_exp:
            ud2v_exp[exp_date] = []
        ud2v_exp[exp_date].append(symbol)
    
    print("\n📅 UD:2V OPTIONS BY EXPIRATION:")
    for exp_date, symbols in sorted(ud2v_exp.items()):
        # Calculate day of week
        if exp_date != 'Unknown':
            try:
                date_obj = datetime.strptime(exp_date, '%Y-%m-%d')
                day_name = date_obj.strftime('%A')
                print(f"\n{exp_date} ({day_name}): {len(symbols)} symbols")
                
                # Get volumes for this expiration
                exp_volume = df[df['symbol'].isin(symbols)].groupby('symbol')['size'].sum().sort_values(ascending=False)
                total_vol = exp_volume.sum()
                print(f"Total volume: {total_vol:,} contracts")
                
                # Show top 3
                print("Top 3 by volume:")
                for symbol, vol in exp_volume.head(3).items():
                    # Extract strike from symbol
                    parts = symbol.split()
                    if len(parts) >= 3:
                        strike_encoded = parts[2]
                        strike = int(strike_encoded[:5]) / 100
                        print(f"  {symbol}: {vol:,} contracts (approx strike: {strike:.0f})")
            except:
                print(f"\n{exp_date}: {len(symbols)} symbols")
    
    # Now let's specifically look for Thursday July 24 (Week 4)
    print("\n🎯 SEARCHING FOR THURSDAY JULY 24 OPTIONS (Week 4):")
    print("-"*60)
    
    thursday_symbols = []
    for exp_date, symbols in ud2v_exp.items():
        if '2025-07-24' in exp_date:  # Thursday July 24
            thursday_symbols = symbols
            break
    
    if thursday_symbols:
        print(f"✅ Found {len(thursday_symbols)} options expiring Thursday July 24")
        
        # Get volumes
        thurs_volume = df[df['symbol'].isin(thursday_symbols)].groupby('symbol')['size'].sum().sort_values(ascending=False)
        
        print(f"\nTotal Thursday volume: {thurs_volume.sum():,} contracts")
        print("\nTop 10 Thursday options by volume:")
        
        for i, (symbol, vol) in enumerate(thurs_volume.head(10).items(), 1):
            # Decode strike
            parts = symbol.split()
            if len(parts) >= 3:
                strike_encoded = parts[2]
                strike = int(strike_encoded[:5]) / 100
                print(f"{i:2d}. {symbol}: {vol:,} contracts (strike ≈ {strike:.0f})")
        
        # Check for strikes matching Barchart
        print("\n🔍 Checking for Barchart strike matches (23275, 23300, 23350, 23400):")
        barchart_strikes = [23275, 23300, 23350, 23400]
        
        matches = []
        for symbol in thursday_symbols:
            parts = symbol.split()
            if len(parts) >= 3:
                strike_encoded = parts[2]
                strike = int(strike_encoded[:5]) / 100
                if strike in barchart_strikes:
                    vol = thurs_volume.get(symbol, 0)
                    matches.append((symbol, strike, vol))
        
        if matches:
            print("\n✅ FOUND MATCHING STRIKES:")
            for symbol, strike, vol in sorted(matches, key=lambda x: x[2], reverse=True):
                print(f"  Strike {strike:.0f}: {symbol} = {vol} contracts")
                
            print("\n💡 THESE ARE LIKELY THE E-MINI THURSDAY OPTIONS!")
        else:
            print("\n❌ No exact strike matches found")
    else:
        print("❌ No Thursday July 24 options found")
        
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n📝 FINAL ANALYSIS:")
print("="*80)
print("1. UD:2V symbols appear to be the E-mini weekly options")
print("2. They have encoded strikes (7-digit number / 100)")
print("3. Different expiration dates are mixed in the UD:2V format")
print("4. Need to filter by expiration date to find specific day's options")
print("5. Volume is still lower than Barchart - possible reasons:")
print("   - Different data capture times")
print("   - Different market data sources")
print("   - Barchart might aggregate across venues")
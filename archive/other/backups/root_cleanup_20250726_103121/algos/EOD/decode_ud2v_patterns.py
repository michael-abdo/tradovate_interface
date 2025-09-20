#!/usr/bin/env python3
"""
Advanced analysis of UD:2V symbols to decode their meaning.
"""

import pandas as pd
import re
from datetime import datetime
import json

def load_data():
    """Load the CSV data and extract UD:2V symbols."""
    df = pd.read_csv('/Users/Mike/trading/algos/EOD/nq_options_comprehensive_analysis.csv')
    ud2v_data = df[df['symbol'].str.startswith('UD:2V:')].copy()
    standard_data = df[df['symbol'].str.match(r'^NQ[A-Z]\d\s+[CP]\d+$')].copy()
    return ud2v_data, standard_data

def analyze_strike_hypothesis(ud2v_data):
    """Test if the 7-digit numbers could encode strike prices."""
    print("=== STRIKE PRICE ENCODING HYPOTHESIS ===")
    
    # Look for patterns in the 7-digit numbers
    numbers = []
    for idx, row in ud2v_data.iterrows():
        symbol = row['symbol']
        match = re.search(r'UD:2V:\s+([A-Z0-9]{1,2})\s+(\d{7})', symbol)
        if match:
            code = match.group(1)
            number = int(match.group(2))
            numbers.append({
                'symbol': symbol,
                'code': code,
                'number': number,
                'price': row['latest_price'],
                'volume': row['total_volume']
            })
    
    # Test hypothesis: number/100 = strike price
    print("Testing hypothesis: number/100 = strike price")
    for entry in numbers[:15]:
        derived_strike = entry['number'] / 100
        print(f"  {entry['symbol']}: {entry['number']} / 100 = {derived_strike:.2f} (price: {entry['price']})")
    
    print("\nTesting hypothesis: number = strike price * 100 + additional encoding")
    # Look for common ranges in NQ options (typically 15000-30000)
    potential_strikes = []
    for entry in numbers:
        # Try to extract strike from leading digits
        num_str = str(entry['number'])
        
        # Try leading 5 digits as strike*100
        if len(num_str) >= 5:
            potential = int(num_str[:5]) / 100
            if 150 <= potential <= 300:  # Reasonable range for NQ (15000-30000)
                potential_strikes.append({
                    'symbol': entry['symbol'],
                    'number': entry['number'],
                    'potential_strike': potential * 100,
                    'remainder': int(num_str[5:]) if len(num_str) > 5 else 0,
                    'price': entry['price']
                })
    
    print(f"\nFound {len(potential_strikes)} symbols with potential strike encoding in first 5 digits:")
    for entry in potential_strikes[:10]:
        print(f"  {entry['symbol']}: strike={entry['potential_strike']:.0f}, remainder={entry['remainder']}, price={entry['price']}")
    
    return potential_strikes

def analyze_code_meanings(ud2v_data):
    """Analyze what the 2-letter codes might mean."""
    print("\n=== CODE MEANING ANALYSIS ===")
    
    codes = {}
    for idx, row in ud2v_data.iterrows():
        symbol = row['symbol']
        match = re.search(r'UD:2V:\s+([A-Z0-9]{1,2})\s+(\d{7})', symbol)
        if match:
            code = match.group(1)
            number = int(match.group(2))
            
            if code not in codes:
                codes[code] = []
            
            codes[code].append({
                'symbol': symbol,
                'number': number,
                'price': row['latest_price'],
                'volume': row['total_volume'],
                'option_type': row['option_type']
            })
    
    print("Code analysis:")
    for code, entries in codes.items():
        prices = [e['price'] for e in entries if pd.notna(e['price'])]
        negative_count = len([p for p in prices if p < 0])
        positive_count = len([p for p in prices if p >= 0])
        
        print(f"\nCode '{code}' ({len(entries)} symbols):")
        print(f"  Positive prices: {positive_count}")
        print(f"  Negative prices: {negative_count}")
        
        # Look for patterns in option types
        option_types = [e['option_type'] for e in entries]
        call_count = option_types.count('call')
        unknown_count = option_types.count('unknown')
        
        print(f"  Call options: {call_count}")
        print(f"  Unknown type: {unknown_count}")
        
        # Hypothesis: codes might indicate option type or strategy
        if negative_count > positive_count:
            print(f"  HYPOTHESIS: '{code}' might indicate short positions or puts")
        elif call_count > 0:
            print(f"  HYPOTHESIS: '{code}' might indicate calls")
        else:
            print(f"  HYPOTHESIS: '{code}' might indicate a specific strategy or contract type")

def analyze_time_patterns(ud2v_data):
    """Analyze expiration patterns."""
    print("\n=== TIME PATTERN ANALYSIS ===")
    
    # Check expiration dates
    expirations = ud2v_data['expiration_date'].value_counts()
    print("Expiration dates:")
    for date, count in expirations.items():
        print(f"  {date}: {count} symbols")
    
    # Most UD:2V symbols expire on 2025-07-18 (today's date according to context)
    print("\nMost UD:2V symbols expire today (2025-07-18), suggesting they might be:")
    print("  - 0DTE (zero days to expiration) options")
    print("  - Intraday trading instruments")
    print("  - Special weekly/daily options")

def analyze_volume_price_relationship(ud2v_data):
    """Analyze relationship between volume and prices."""
    print("\n=== VOLUME-PRICE RELATIONSHIP ===")
    
    # Group by code and analyze
    codes = {}
    for idx, row in ud2v_data.iterrows():
        symbol = row['symbol']
        match = re.search(r'UD:2V:\s+([A-Z0-9]{1,2})\s+(\d{7})', symbol)
        if match:
            code = match.group(1)
            
            if code not in codes:
                codes[code] = {'high_volume': [], 'low_volume': []}
            
            if row['total_volume'] > 10:
                codes[code]['high_volume'].append({
                    'symbol': symbol,
                    'volume': row['total_volume'],
                    'price': row['latest_price']
                })
            else:
                codes[code]['low_volume'].append({
                    'symbol': symbol,
                    'volume': row['total_volume'],
                    'price': row['latest_price']
                })
    
    for code, data in codes.items():
        if data['high_volume']:
            print(f"\nCode '{code}' - High volume symbols:")
            for entry in data['high_volume'][:5]:
                print(f"  {entry['symbol']}: vol={entry['volume']}, price={entry['price']}")

def compare_with_nq_current_price():
    """Try to understand UD:2V prices in context of NQ futures price."""
    print("\n=== NQ FUTURES CONTEXT ANALYSIS ===")
    
    # Based on the standard NQ options, we can infer current NQ price
    # Look at ATM (at-the-money) options to estimate current futures price
    df = pd.read_csv('/Users/Mike/trading/algos/EOD/nq_options_comprehensive_analysis.csv')
    standard_data = df[df['symbol'].str.match(r'^NQ[A-Z]\d\s+[CP]\d+$')].copy()
    
    # Find options with highest volume to identify likely ATM strikes
    high_vol_options = standard_data.nlargest(10, 'total_volume')
    print("Highest volume standard NQ options (likely near ATM):")
    for idx, row in high_vol_options.iterrows():
        print(f"  {row['symbol']}: vol={row['total_volume']}, strike={row['strike']}, price={row['latest_price']}")
    
    # Estimate current NQ price (likely around 23000-24000 based on high volume strikes)
    estimated_nq_price = 23500  # Rough estimate based on active strikes
    print(f"\nEstimated current NQ futures price: ~{estimated_nq_price}")
    
    # Now analyze UD:2V prices in this context
    ud2v_data = df[df['symbol'].str.startswith('UD:2V:')].copy()
    
    print("\nUD:2V prices in context:")
    print("If UD:2V symbols are related to NQ options:")
    
    # Look for UD:2V symbols with prices that could make sense as option premiums
    reasonable_premiums = []
    for idx, row in ud2v_data.iterrows():
        price = row['latest_price']
        if pd.notna(price) and 0 < price < 2000:  # Reasonable premium range
            reasonable_premiums.append({
                'symbol': row['symbol'],
                'price': price,
                'volume': row['total_volume']
            })
    
    print(f"Found {len(reasonable_premiums)} UD:2V symbols with reasonable option premium prices:")
    for entry in sorted(reasonable_premiums, key=lambda x: x['volume'], reverse=True)[:10]:
        print(f"  {entry['symbol']}: price={entry['price']}, volume={entry['volume']}")

def main():
    ud2v_data, standard_data = load_data()
    
    print(f"Analyzing {len(ud2v_data)} UD:2V symbols...")
    print(f"Comparing with {len(standard_data)} standard NQ symbols...")
    
    # Run various analyses
    potential_strikes = analyze_strike_hypothesis(ud2v_data)
    analyze_code_meanings(ud2v_data)
    analyze_time_patterns(ud2v_data)
    analyze_volume_price_relationship(ud2v_data)
    compare_with_nq_current_price()
    
    print("\n=== SUMMARY OF FINDINGS ===")
    print("1. UD:2V symbols appear to be options-related instruments")
    print("2. The 7-digit numbers may encode strike prices (number/100 = strike)")
    print("3. The 2-letter codes likely indicate:")
    print("   - VT: Vanilla options (most common, positive prices)")
    print("   - GN: possibly short positions (many negative prices)")
    print("   - DG: likely short positions (mostly negative prices)")
    print("   - IC: unknown strategy (positive prices)")
    print("   - CO: Call options (marked as 'call' in data)")
    print("   - Others: various strategies or position types")
    print("4. Most expire today (0DTE options)")
    print("5. Lower volume than standard NQ options")
    print("6. Price ranges suggest these could be complex option strategies")

if __name__ == "__main__":
    main()
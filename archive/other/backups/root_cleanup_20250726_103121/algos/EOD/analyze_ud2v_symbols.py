#!/usr/bin/env python3
"""
Analyze UD:2V symbols from the NQ options CSV to understand their structure and patterns.
"""

import pandas as pd
import re
from collections import defaultdict, Counter
import json

def extract_ud2v_symbols(csv_file):
    """Extract all UD:2V symbols and their data from the CSV."""
    df = pd.read_csv(csv_file)
    
    # Filter for UD:2V symbols
    ud2v_mask = df['symbol'].str.startswith('UD:2V:')
    ud2v_data = df[ud2v_mask].copy()
    
    return ud2v_data

def parse_ud2v_symbol(symbol):
    """Parse a UD:2V symbol to extract components."""
    # Pattern: UD:2V: [2-letter code] [7-digit number]
    pattern = r'UD:2V:\s+([A-Z0-9]{1,2})\s+(\d{7})'
    match = re.match(pattern, symbol)
    
    if match:
        code = match.group(1)
        number = match.group(2)
        return code, int(number)
    else:
        return None, None

def analyze_patterns(ud2v_data):
    """Analyze patterns in UD:2V symbols."""
    analysis = {
        'total_symbols': len(ud2v_data),
        'codes': defaultdict(list),
        'number_ranges': {},
        'price_patterns': {},
        'volume_patterns': {},
        'expiration_patterns': {},
        'option_type_patterns': {}
    }
    
    # Parse all symbols
    for idx, row in ud2v_data.iterrows():
        symbol = row['symbol']
        code, number = parse_ud2v_symbol(symbol)
        
        if code and number:
            analysis['codes'][code].append({
                'symbol': symbol,
                'number': number,
                'price': row['latest_price'],
                'volume': row['total_volume'],
                'expiration': row['expiration_date'],
                'option_type': row['option_type'],
                'strike': row['strike']
            })
    
    # Analyze each code
    for code, entries in analysis['codes'].items():
        numbers = [e['number'] for e in entries]
        prices = [e['price'] for e in entries if pd.notna(e['price'])]
        volumes = [e['volume'] for e in entries if pd.notna(e['volume'])]
        
        analysis['number_ranges'][code] = {
            'min': min(numbers),
            'max': max(numbers),
            'count': len(numbers),
            'range': max(numbers) - min(numbers)
        }
        
        analysis['price_patterns'][code] = {
            'min_price': min(prices) if prices else None,
            'max_price': max(prices) if prices else None,
            'avg_price': sum(prices) / len(prices) if prices else None,
            'negative_prices': len([p for p in prices if p < 0])
        }
        
        analysis['volume_patterns'][code] = {
            'min_volume': min(volumes) if volumes else None,
            'max_volume': max(volumes) if volumes else None,
            'avg_volume': sum(volumes) / len(volumes) if volumes else None,
            'total_volume': sum(volumes) if volumes else None
        }
    
    # Count expiration dates
    expirations = ud2v_data['expiration_date'].value_counts()
    analysis['expiration_patterns'] = expirations.to_dict()
    
    # Count option types
    option_types = ud2v_data['option_type'].value_counts()
    analysis['option_type_patterns'] = option_types.to_dict()
    
    return analysis

def analyze_number_patterns(ud2v_data):
    """Analyze the 7-digit numbers for encoding patterns."""
    patterns = {
        'potential_strike_encoding': [],
        'potential_date_encoding': [],
        'potential_sequence': []
    }
    
    for idx, row in ud2v_data.iterrows():
        symbol = row['symbol']
        code, number = parse_ud2v_symbol(symbol)
        
        if code and number:
            # Check if number could encode strike price
            # Standard NQ strikes are typically 15000-30000 range
            potential_strikes = []
            
            # Try different divisions/multiplications
            for divisor in [1, 10, 100, 1000]:
                derived = number / divisor
                if 10000 <= derived <= 35000:  # Reasonable strike range
                    potential_strikes.append(derived)
            
            for multiplier in [0.1, 0.01, 0.001]:
                derived = number * multiplier
                if 10000 <= derived <= 35000:  # Reasonable strike range
                    potential_strikes.append(derived)
            
            if potential_strikes:
                patterns['potential_strike_encoding'].append({
                    'symbol': symbol,
                    'number': number,
                    'potential_strikes': potential_strikes,
                    'actual_price': row['latest_price']
                })
    
    return patterns

def compare_with_standard_symbols(csv_file):
    """Compare UD:2V symbols with standard NQ symbols."""
    df = pd.read_csv(csv_file)
    
    # Get standard NQ symbols
    standard_nq = df[df['symbol'].str.match(r'^NQ[A-Z]\d\s+[CP]\d+$')].copy()
    ud2v_symbols = df[df['symbol'].str.startswith('UD:2V:')].copy()
    
    comparison = {
        'standard_count': len(standard_nq),
        'ud2v_count': len(ud2v_symbols),
        'price_comparison': {},
        'volume_comparison': {},
        'expiration_comparison': {}
    }
    
    # Price ranges
    standard_prices = standard_nq['latest_price'].dropna()
    ud2v_prices = ud2v_symbols['latest_price'].dropna()
    
    comparison['price_comparison'] = {
        'standard_range': [float(standard_prices.min()), float(standard_prices.max())],
        'ud2v_range': [float(ud2v_prices.min()), float(ud2v_prices.max())],
        'standard_avg': float(standard_prices.mean()),
        'ud2v_avg': float(ud2v_prices.mean())
    }
    
    # Volume comparison
    standard_volumes = standard_nq['total_volume'].dropna()
    ud2v_volumes = ud2v_symbols['total_volume'].dropna()
    
    comparison['volume_comparison'] = {
        'standard_range': [int(standard_volumes.min()), int(standard_volumes.max())],
        'ud2v_range': [int(ud2v_volumes.min()), int(ud2v_volumes.max())],
        'standard_avg': float(standard_volumes.mean()),
        'ud2v_avg': float(ud2v_volumes.mean())
    }
    
    # Expiration comparison
    standard_exp = standard_nq['expiration_date'].value_counts()
    ud2v_exp = ud2v_symbols['expiration_date'].value_counts()
    
    comparison['expiration_comparison'] = {
        'standard_expirations': standard_exp.to_dict(),
        'ud2v_expirations': ud2v_exp.to_dict()
    }
    
    return comparison

def main():
    csv_file = '/Users/Mike/trading/algos/EOD/nq_options_comprehensive_analysis.csv'
    
    print("=== UD:2V SYMBOL ANALYSIS ===\n")
    
    # Extract UD:2V symbols
    ud2v_data = extract_ud2v_symbols(csv_file)
    print(f"Found {len(ud2v_data)} UD:2V symbols\n")
    
    # Show sample symbols
    print("Sample UD:2V symbols:")
    for symbol in ud2v_data['symbol'].head(10):
        code, number = parse_ud2v_symbol(symbol)
        print(f"  {symbol} -> Code: {code}, Number: {number}")
    print()
    
    # Analyze patterns
    analysis = analyze_patterns(ud2v_data)
    
    print("=== CODE ANALYSIS ===")
    print(f"Total unique codes: {len(analysis['codes'])}")
    print("Codes found:", list(analysis['codes'].keys()))
    print()
    
    for code in sorted(analysis['codes'].keys()):
        entries = analysis['codes'][code]
        numbers = analysis['number_ranges'][code]
        prices = analysis['price_patterns'][code]
        volumes = analysis['volume_patterns'][code]
        
        print(f"Code '{code}':")
        print(f"  Count: {numbers['count']}")
        print(f"  Number range: {numbers['min']:,} - {numbers['max']:,} (range: {numbers['range']:,})")
        avg_price_str = f"{prices['avg_price']:.2f}" if prices['avg_price'] else 'N/A'
        print(f"  Price range: {prices['min_price']} - {prices['max_price']} (avg: {avg_price_str})")
        print(f"  Negative prices: {prices['negative_prices']}")
        print(f"  Volume range: {volumes['min_volume']} - {volumes['max_volume']} (total: {volumes['total_volume']})")
        print()
    
    print("=== EXPIRATION ANALYSIS ===")
    for exp_date, count in analysis['expiration_patterns'].items():
        print(f"  {exp_date}: {count} symbols")
    print()
    
    print("=== OPTION TYPE ANALYSIS ===")
    for opt_type, count in analysis['option_type_patterns'].items():
        print(f"  {opt_type}: {count} symbols")
    print()
    
    # Analyze number patterns
    number_patterns = analyze_number_patterns(ud2v_data)
    
    print("=== NUMBER PATTERN ANALYSIS ===")
    print(f"Symbols with potential strike encoding: {len(number_patterns['potential_strike_encoding'])}")
    
    for entry in number_patterns['potential_strike_encoding'][:10]:  # Show first 10
        print(f"  {entry['symbol']}: number={entry['number']}, potential_strikes={entry['potential_strikes']}, actual_price={entry['actual_price']}")
    print()
    
    # Compare with standard symbols
    comparison = compare_with_standard_symbols(csv_file)
    
    print("=== COMPARISON WITH STANDARD NQ SYMBOLS ===")
    print(f"Standard NQ symbols: {comparison['standard_count']}")
    print(f"UD:2V symbols: {comparison['ud2v_count']}")
    print()
    print("Price comparison:")
    print(f"  Standard range: {comparison['price_comparison']['standard_range']}")
    print(f"  UD:2V range: {comparison['price_comparison']['ud2v_range']}")
    print(f"  Standard avg: {comparison['price_comparison']['standard_avg']:.2f}")
    print(f"  UD:2V avg: {comparison['price_comparison']['ud2v_avg']:.2f}")
    print()
    print("Volume comparison:")
    print(f"  Standard range: {comparison['volume_comparison']['standard_range']}")
    print(f"  UD:2V range: {comparison['volume_comparison']['ud2v_range']}")
    print(f"  Standard avg: {comparison['volume_comparison']['standard_avg']:.2f}")
    print(f"  UD:2V avg: {comparison['volume_comparison']['ud2v_avg']:.2f}")
    print()
    
    # Save detailed analysis to JSON
    output_file = '/Users/Mike/trading/algos/EOD/ud2v_analysis_results.json'
    
    # Convert defaultdict to regular dict for JSON serialization
    analysis_json = dict(analysis)
    analysis_json['codes'] = dict(analysis_json['codes'])
    
    full_results = {
        'analysis': analysis_json,
        'number_patterns': number_patterns,
        'comparison': comparison,
        'raw_data': ud2v_data.to_dict('records')
    }
    
    with open(output_file, 'w') as f:
        json.dump(full_results, f, indent=2, default=str)
    
    print(f"Detailed analysis saved to: {output_file}")

if __name__ == "__main__":
    main()
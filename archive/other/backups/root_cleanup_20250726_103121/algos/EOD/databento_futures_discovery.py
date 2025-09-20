#!/usr/bin/env python3
"""
Databento Futures Symbol Discovery
Goal: Find all available NQ futures symbols in Databento
"""

import databento as db
import json
from datetime import datetime, timedelta
from itertools import product

def main():
    """Discover all available NQ futures symbols"""
    print("🔍 DATABENTO NQ FUTURES SYMBOL DISCOVERY")
    print("="*60)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    today = datetime.now().date()
    
    # CME month codes: F=Jan, G=Feb, H=Mar, J=Apr, K=May, M=Jun, N=Jul, Q=Aug, U=Sep, V=Oct, X=Nov, Z=Dec
    month_codes = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z']
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Test different year formats
    year_formats = [
        '5',    # 2025 -> 5
        '25',   # 2025 -> 25
        '6',    # 2026 -> 6
        '26',   # 2026 -> 26
        '4',    # 2024 -> 4
        '24'    # 2024 -> 24
    ]
    
    found_symbols = []
    
    print("📋 Testing NQ futures symbols...")
    print("-" * 40)
    
    # Test all combinations
    for year in year_formats:
        for month_code, month_name in zip(month_codes, month_names):
            symbol = f"NQ{month_code}{year}"
            
            try:
                data = client.timeseries.get_range(
                    dataset="GLBX.MDP3",
                    symbols=symbol,
                    schema="trades",
                    start=today - timedelta(days=1),
                    end=today,
                    limit=1
                )
                
                df = data.to_df()
                if len(df) > 0:
                    found_symbols.append({
                        'symbol': symbol,
                        'month': month_name,
                        'year': f"20{year}" if len(year) == 1 else f"20{year}" if len(year) == 2 else year,
                        'records': len(df)
                    })
                    print(f"✅ {symbol:<8} - {month_name} 20{year if len(year) <= 2 else year}")
                    
            except Exception as e:
                if "422" not in str(e):  # Ignore symbol not found errors
                    print(f"⚠️  {symbol}: {str(e)[:50]}...")
    
    print("\n" + "="*60)
    print("📊 SUMMARY OF FOUND SYMBOLS")
    print("="*60)
    
    if found_symbols:
        print(f"\n✅ Found {len(found_symbols)} NQ futures symbols:")
        
        # Group by year
        by_year = {}
        for sym in found_symbols:
            year = sym['year']
            if year not in by_year:
                by_year[year] = []
            by_year[year].append(sym)
        
        for year in sorted(by_year.keys()):
            print(f"\n📅 {year}:")
            symbols_in_year = sorted(by_year[year], key=lambda x: month_codes.index(x['symbol'][2]))
            for sym in symbols_in_year:
                print(f"   • {sym['symbol']:<8} - {sym['month']}")
        
        # Test one symbol in detail
        print("\n" + "="*60)
        print("🔍 DETAILED ANALYSIS OF ONE SYMBOL")
        print("="*60)
        
        test_symbol = found_symbols[0]['symbol']
        print(f"📋 Analyzing {test_symbol} in detail...")
        
        try:
            # Get definition data
            def_data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols=test_symbol,
                schema="definition",
                start=today - timedelta(days=1),
                end=today,
                limit=1
            )
            
            def_df = def_data.to_df()
            if len(def_df) > 0:
                sample = def_df.iloc[0]
                print(f"📊 Contract Details for {test_symbol}:")
                print(f"   • Expiration: {sample.get('expiration', 'N/A')}")
                print(f"   • Multiplier: {sample.get('unit_of_measure_qty', 'N/A')}")
                print(f"   • Min tick: {sample.get('min_price_increment', 'N/A')}")
                print(f"   • Exchange: {sample.get('exchange', 'N/A')}")
                print(f"   • Asset: {sample.get('asset', 'N/A')}")
                print(f"   • Security type: {sample.get('security_type', 'N/A')}")
        
        except Exception as e:
            print(f"⚠️  Error getting details: {e}")
        
        # Save results
        with open("available_nq_symbols.json", "w") as f:
            json.dump(found_symbols, f, indent=2)
        print(f"\n✅ Saved {len(found_symbols)} symbols to available_nq_symbols.json")
        
    else:
        print("❌ No NQ futures symbols found!")
    
    # Also test some other related symbols
    print("\n" + "="*60)
    print("🔍 TESTING RELATED SYMBOLS")
    print("="*60)
    
    related_symbols = [
        "MNQ",      # Micro NQ
        "MNQU5",    # Micro NQ Sep 2025
        "MNQZ5",    # Micro NQ Dec 2025
        "ES",       # E-mini S&P 500
        "ESU5",     # E-mini S&P 500 Sep 2025
        "YM",       # E-mini Dow
        "YMU5",     # E-mini Dow Sep 2025
    ]
    
    print("📋 Testing related futures symbols...")
    for symbol in related_symbols:
        try:
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols=symbol,
                schema="trades",
                start=today - timedelta(days=1),
                end=today,
                limit=1
            )
            
            df = data.to_df()
            if len(df) > 0:
                print(f"✅ {symbol:<8} - Available")
            else:
                print(f"❌ {symbol:<8} - No data")
                
        except Exception as e:
            if "422" in str(e):
                print(f"❌ {symbol:<8} - Symbol not found")
            else:
                print(f"⚠️  {symbol:<8} - Error: {str(e)[:30]}...")
    
    print("\n🎯 Discovery complete!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test NQ weekly options using Databento Historical API
Since we don't have live data license, we'll use historical data
"""

import databento as db
from datetime import datetime, timedelta
import pandas as pd

def find_nq_weekly_options():
    """Find NQ weekly options in historical data"""
    
    api_key = 'db-i4VujYQdiwvJD3rpsEhqV8hanxdxc'
    client = db.Historical(api_key)
    
    print("Searching for NQ Weekly Options")
    print("="*60)
    
    # Get recent date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("\n1. Getting all NQ options...")
    
    try:
        # Get NQ options definitions
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="definition",
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            stype_in="parent",
            limit=1000  # Get more records to find weekly options
        )
        
        df = data.to_df()
        print(f"   ✓ Found {len(df)} NQ option definitions")
        
        if len(df) > 0:
            # Analyze the symbols
            print("\n2. Analyzing option symbols...")
            
            # Extract unique symbols
            if 'raw_symbol' in df.columns:
                symbols = df['raw_symbol'].unique()
            elif 'symbol' in df.columns:
                symbols = df['symbol'].unique()
            else:
                print("   ✗ No symbol column found")
                print(f"   Available columns: {df.columns.tolist()}")
                return
            
            print(f"   ✓ Found {len(symbols)} unique option symbols")
            
            # Look for weekly option patterns
            print("\n3. Searching for weekly option patterns...")
            
            # Common weekly option patterns
            weekly_patterns = {
                'Monday Weekly': [],
                'Wednesday Weekly': [],
                'Friday Weekly': [],
                'End-of-Month': [],
                'Other Weekly': []
            }
            
            for symbol in symbols:
                symbol_str = str(symbol)
                
                # Check for specific patterns
                if 'Q1A' in symbol_str or 'Q1B' in symbol_str:
                    weekly_patterns['Monday Weekly'].append(symbol_str)
                elif 'Q2C' in symbol_str or 'Q3C' in symbol_str or 'Q4C' in symbol_str:
                    weekly_patterns['Wednesday Weekly'].append(symbol_str)
                elif 'Q1E' in symbol_str or 'Q2E' in symbol_str or 'Q3E' in symbol_str or 'Q4E' in symbol_str:
                    weekly_patterns['Friday Weekly'].append(symbol_str)
                elif 'QNE' in symbol_str or 'EOM' in symbol_str:
                    weekly_patterns['End-of-Month'].append(symbol_str)
                elif any(x in symbol_str for x in ['W', 'EW', 'EOW', 'Q']):
                    weekly_patterns['Other Weekly'].append(symbol_str)
            
            # Display results
            print("\n4. Weekly Options Found:")
            print("-"*40)
            
            for pattern_type, symbols_list in weekly_patterns.items():
                if symbols_list:
                    print(f"\n{pattern_type}: {len(symbols_list)} options")
                    for symbol in symbols_list[:5]:  # Show first 5
                        print(f"   - {symbol}")
                    if len(symbols_list) > 5:
                        print(f"   ... and {len(symbols_list) - 5} more")
            
            # Show some regular monthly options for comparison
            monthly_symbols = [s for s in symbols if not any(x in str(s) for x in ['Q', 'W', 'EW', 'EOW', 'EOM'])]
            if monthly_symbols:
                print(f"\nRegular Monthly Options: {len(monthly_symbols)} options")
                for symbol in monthly_symbols[:5]:
                    print(f"   - {symbol}")
                
            # Get more details about expiration dates
            print("\n5. Analyzing expiration dates...")
            if 'expiration' in df.columns:
                df['expiration_date'] = pd.to_datetime(df['expiration'], unit='ns')
                df['day_of_week'] = df['expiration_date'].dt.day_name()
                
                expiry_summary = df.groupby('day_of_week').size()
                print("\nOptions by expiration day:")
                for day, count in expiry_summary.items():
                    print(f"   {day}: {count} options")
                    
    except Exception as e:
        print(f"   ✗ Error: {e}")

def test_specific_dates():
    """Test options for specific dates mentioned by user"""
    print("\n\n6. Testing Specific Weekly Option Dates")
    print("="*60)
    
    api_key = 'db-i4VujYQdiwvJD3rpsEhqV8hanxdxc'
    client = db.Historical(api_key)
    
    # Get current week and upcoming weeks
    today = datetime.now()
    
    # Find next Monday and Wednesday
    days_ahead = 0
    while today.weekday() != 0:  # 0 = Monday
        today += timedelta(days=1)
        days_ahead += 1
    
    next_monday = today
    next_wednesday = next_monday + timedelta(days=2)
    
    print(f"Next Monday: {next_monday.strftime('%Y-%m-%d')}")
    print(f"Next Wednesday: {next_wednesday.strftime('%Y-%m-%d')}")
    
    # Try to get trades or quotes for recent dates
    test_date = datetime.now() - timedelta(days=3)  # 3 days ago
    
    print(f"\n7. Getting recent NQ option activity from {test_date.strftime('%Y-%m-%d')}...")
    
    try:
        # Get recent trades
        trades = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="trades",
            start=test_date.strftime("%Y-%m-%d"),
            end=datetime.now().strftime("%Y-%m-%d"),
            stype_in="parent",
            limit=100
        )
        
        trades_df = trades.to_df()
        if len(trades_df) > 0:
            print(f"   ✓ Found {len(trades_df)} recent trades")
            
            # Show unique traded symbols
            if 'symbol' in trades_df.columns:
                traded_symbols = trades_df['symbol'].unique()
                print(f"\n   Recently traded NQ options:")
                for symbol in traded_symbols[:10]:
                    print(f"     - {symbol}")
                    
    except Exception as e:
        print(f"   ✗ Error getting trades: {e}")

if __name__ == "__main__":
    find_nq_weekly_options()
    test_specific_dates()
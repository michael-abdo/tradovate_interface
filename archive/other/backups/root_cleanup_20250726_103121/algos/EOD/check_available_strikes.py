#!/usr/bin/env python3
"""
Check what strikes are actually available for July 18, 2025 NQ options
"""

import databento as db
import pandas as pd
import numpy as np

def main():
    """Check available strikes"""
    print("🔍 CHECKING AVAILABLE STRIKES FOR JULY 18, 2025 NQ OPTIONS")
    print("="*70)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    
    try:
        # Get all available options
        print("📋 Getting all NQ options...")
        
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="definition",
            start="2025-07-16",
            end="2025-07-17",
            stype_in="parent"
        )
        
        df = data.to_df()
        print(f"✅ Retrieved {len(df)} NQ options")
        
        # Filter for July 18 expiration
        df['exp_str'] = df['expiration'].astype(str)
        july_18_options = df[df['exp_str'].str.contains('2025-07-18', na=False)]
        
        print(f"📊 Found {len(july_18_options)} options expiring July 18")
        
        if len(july_18_options) > 0:
            print(f"\n📋 Column info:")
            print(f"   Columns: {list(july_18_options.columns)}")
            
            # Check if strike_price column exists and has data
            if 'strike_price' in july_18_options.columns:
                strike_data = july_18_options['strike_price']
                print(f"   Strike price column: {len(strike_data)} values")
                print(f"   Non-null strikes: {strike_data.notna().sum()}")
                print(f"   Null strikes: {strike_data.isna().sum()}")
                
                # Show some sample strike values
                non_null_strikes = strike_data.dropna()
                if len(non_null_strikes) > 0:
                    print(f"   Sample strikes: {list(non_null_strikes.head(10))}")
                    print(f"   Strike range: {non_null_strikes.min():.2f} to {non_null_strikes.max():.2f}")
                    
                    # Get unique strikes and sort them
                    unique_strikes = sorted(non_null_strikes.unique())
                    print(f"\n📊 All available strikes for July 18:")
                    print(f"   Total unique strikes: {len(unique_strikes)}")
                    
                    # Show strikes in chunks
                    for i in range(0, len(unique_strikes), 20):
                        chunk = unique_strikes[i:i+20]
                        print(f"   {chunk}")
                    
                    # Look for strikes near 23,175
                    target = 23175.0
                    close_strikes = [s for s in unique_strikes if abs(s - target) <= 500]
                    print(f"\n🎯 Strikes within 500 points of {target}:")
                    print(f"   {close_strikes}")
                    
                    # If 23,175 doesn't exist, find the closest
                    if target not in unique_strikes:
                        closest_strike = min(unique_strikes, key=lambda x: abs(x - target))
                        print(f"\n📍 Closest strike to {target}: {closest_strike}")
                        
                        # Get data for closest strike call
                        closest_calls = july_18_options[
                            (july_18_options['strike_price'] == closest_strike) &
                            (july_18_options['symbol'].str.contains(' C', na=False))
                        ]
                        
                        if len(closest_calls) > 0:
                            closest_symbol = closest_calls['symbol'].iloc[0]
                            print(f"🎯 Closest call option: {closest_symbol}")
                            
                            # Get market data for this option
                            try:
                                trades = client.timeseries.get_range(
                                    dataset="GLBX.MDP3",
                                    symbols=[closest_symbol],
                                    schema="trades",
                                    start="2025-07-17",
                                    end="2025-07-17",
                                    limit=20
                                )
                                
                                trades_df = trades.to_df()
                                print(f"📈 Found {len(trades_df)} trades for {closest_symbol}")
                                
                                if len(trades_df) > 0:
                                    latest_price = trades_df['price'].iloc[-1]
                                    volume = trades_df['size'].sum()
                                    
                                    print(f"\n📊 {closest_symbol} Trading Data:")
                                    print(f"   Latest Price: ${latest_price:.2f}")
                                    print(f"   Volume: {volume:,} contracts")
                                    
                                    print(f"\n📈 Recent trades:")
                                    print(trades_df[['price', 'size', 'ts_event']].tail(5))
                                
                            except Exception as e:
                                print(f"⚠️  Trade data error: {e}")
                
            else:
                print("❌ No strike_price column found")
            
            # Show sample symbols to understand the format
            print(f"\n📋 Sample July 18 option symbols:")
            sample_symbols = july_18_options['symbol'].head(20).tolist()
            for symbol in sample_symbols:
                print(f"   {symbol}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
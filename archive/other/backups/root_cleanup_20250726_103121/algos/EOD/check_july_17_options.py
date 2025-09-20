#!/usr/bin/env python3
"""
Check for NQ options expiring TODAY - July 17, 2025
"""

import databento as db
import pandas as pd
from datetime import datetime, timedelta

def main():
    """Check for July 17, 2025 NQ options"""
    print("🔍 CHECKING NQ OPTIONS FOR TODAY: JULY 17, 2025")
    print("="*60)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    today = datetime.now().date()
    print(f"📅 Today's date: {today}")
    
    try:
        # Get all NQ options definitions for today
        print("📋 Getting NQ options for July 17, 2025...")
        
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="definition",
            start="2025-07-16",  # Start from yesterday
            end="2025-07-17",    # End today
            stype_in="parent"
        )
        
        df = data.to_df()
        print(f"✅ Retrieved {len(df)} total NQ options")
        
        # Convert expiration to string for filtering
        df['exp_str'] = df['expiration'].astype(str)
        
        # Filter for July 17, 2025
        july_17_options = df[df['exp_str'].str.contains('2025-07-17', na=False)]
        
        print(f"🎯 Found {len(july_17_options)} options expiring TODAY (July 17, 2025)")
        
        if len(july_17_options) > 0:
            print("\n✅ SUCCESS! NQ OPTIONS EXPIRE TODAY!")
            print("📊 July 17 Options Summary:")
            
            # Show all symbols
            symbols = list(july_17_options['symbol'].unique())
            print(f"   Total symbols: {len(symbols)}")
            print(f"   Symbols: {symbols}")
            
            # Check for call/put types
            calls = july_17_options[july_17_options['symbol'].str.contains(' C', na=False)]
            puts = july_17_options[july_17_options['symbol'].str.contains(' P', na=False)]
            
            print(f"   Calls: {len(calls)}")
            print(f"   Puts: {len(puts)}")
            
            # Show strike prices
            if 'strike_price' in july_17_options.columns:
                strikes = sorted(july_17_options['strike_price'].dropna().unique())
                print(f"   Strike prices: {strikes}")
            
            # Save the results
            july_17_options.to_csv("nq_july_17_2025_options.csv", index=False)
            print(f"\n💾 Saved to nq_july_17_2025_options.csv")
            
            # Show detailed info
            print(f"\n📋 Detailed July 17 Options:")
            detail_cols = ['symbol', 'strike_price', 'expiration', 'underlying']
            available_cols = [col for col in detail_cols if col in july_17_options.columns]
            print(july_17_options[available_cols])
            
            # Get current market data for these options
            print(f"\n📊 Getting CURRENT MARKET DATA for July 17 options...")
            
            # Get trades for today's expiring options
            trades = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols=symbols,  # Use the specific symbols
                schema="trades",
                start="2025-07-17",
                end="2025-07-17",
                limit=100
            )
            
            trades_df = trades.to_df()
            print(f"✅ Found {len(trades_df)} trades for July 17 options TODAY")
            
            if len(trades_df) > 0:
                print("\n📊 Recent trades for July 17 options:")
                print(trades_df[['symbol', 'price', 'size', 'ts_event']].tail(10))
                
                # Save trades
                trades_df.to_csv("nq_july_17_2025_trades.csv", index=False)
                print(f"\n💾 Saved trades to nq_july_17_2025_trades.csv")
            
        else:
            print("❌ No options found expiring July 17, 2025")
            
            # Show what dates we do have
            print("\n📊 Available expiration dates near July 17:")
            unique_expirations = df['exp_str'].unique()
            
            # Show dates around July 17
            july_dates = [exp for exp in unique_expirations if '2025-07' in str(exp)]
            print(f"   July 2025 dates: {sorted(july_dates)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
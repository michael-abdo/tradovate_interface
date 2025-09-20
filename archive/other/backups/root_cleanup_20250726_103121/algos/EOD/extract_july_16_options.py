#!/usr/bin/env python3
"""
Extract and analyze July 16, 2025 NQ options
"""

import databento as db
import pandas as pd
from datetime import datetime, timedelta

def main():
    """Extract July 16 options specifically"""
    print("🔍 EXTRACTING JULY 16, 2025 NQ OPTIONS")
    print("="*60)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    
    try:
        # Get all NQ options definitions
        print("📋 Getting all NQ options definitions...")
        
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="definition",
            start="2025-07-15",
            end="2025-07-16",
            stype_in="parent"
        )
        
        df = data.to_df()
        print(f"✅ Retrieved {len(df)} total NQ options")
        
        # Convert expiration to string for filtering
        df['exp_str'] = df['expiration'].astype(str)
        
        # Filter for July 16, 2025
        july_16_options = df[df['exp_str'].str.contains('2025-07-16', na=False)]
        
        print(f"🎯 Found {len(july_16_options)} options expiring July 16, 2025")
        
        if len(july_16_options) > 0:
            print("\n📊 July 16 Options Summary:")
            print(f"   Symbols: {list(july_16_options['symbol'].unique())}")
            
            # Check for call/put types
            calls = july_16_options[july_16_options['symbol'].str.contains(' C', na=False)]
            puts = july_16_options[july_16_options['symbol'].str.contains(' P', na=False)]
            
            print(f"   Calls: {len(calls)}")
            print(f"   Puts: {len(puts)}")
            
            # Show strike prices
            if 'strike_price' in july_16_options.columns:
                strikes = sorted(july_16_options['strike_price'].dropna().unique())
                print(f"   Strike prices: {strikes}")
            
            # Save the results
            july_16_options.to_csv("nq_july_16_2025_options.csv", index=False)
            print(f"\n💾 Saved to nq_july_16_2025_options.csv")
            
            # Show detailed info
            print(f"\n📋 Detailed July 16 Options:")
            detail_cols = ['symbol', 'strike_price', 'expiration', 'underlying']
            available_cols = [col for col in detail_cols if col in july_16_options.columns]
            print(july_16_options[available_cols])
            
        else:
            print("❌ No options found expiring July 16, 2025")
            
            # Let's check what expiration dates we do have
            print("\n📊 Available expiration dates:")
            unique_expirations = df['exp_str'].unique()
            print(f"   Total unique dates: {len(unique_expirations)}")
            
            # Show dates near July 16
            near_july_16 = [exp for exp in unique_expirations if '2025-07' in str(exp)]
            print(f"   July 2025 dates: {sorted(near_july_16)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
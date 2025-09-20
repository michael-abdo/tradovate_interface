#!/usr/bin/env python3
"""
Test with CORRECT parent symbology format: NQ.OPT
Based on error message showing expected format: '[ROOT].OPT'
"""

import databento as db
import json
from datetime import datetime, timedelta

def main():
    """Test with correct parent symbology format"""
    print("🔍 TESTING CORRECT PARENT SYMBOLOGY: NQ.OPT")
    print("="*60)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    today = datetime.now().date()
    
    # Test 1: Get NQ options using correct parent format
    print("\n📋 TEST 1: Parent Symbology NQ.OPT")
    print("-" * 40)
    
    try:
        print("🔍 Testing with symbol='NQ.OPT', stype_in='parent'...")
        
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",  # Correct parent format!
            schema="definition",
            start="2025-07-15",
            end="2025-07-16",
            stype_in="parent"
        )
        
        df = data.to_df()
        print(f"✅ SUCCESS! Found {len(df)} NQ options instruments")
        
        if len(df) > 0:
            print(f"\n📊 Data shape: {df.shape}")
            print(f"📋 Columns: {list(df.columns)}")
            
            # Check for July 16 expiration
            if 'expiration' in df.columns:
                july_16_options = df[df['expiration'].str.contains('2025-07-16', na=False)]
                print(f"\n🎯 OPTIONS EXPIRING JULY 16, 2025: {len(july_16_options)}")
                
                if len(july_16_options) > 0:
                    print("\n📋 July 16 Options Details:")
                    print(july_16_options[['symbol', 'strike_price', 'instrument_class', 'expiration']].head(10))
                    
                    # Save results
                    july_16_options.to_csv("nq_options_july_16_2025.csv", index=False)
                    print(f"\n💾 Saved {len(july_16_options)} options to nq_options_july_16_2025.csv")
            
            # Show some sample options
            print(f"\n📋 Sample NQ Options:")
            sample_cols = ['symbol', 'strike_price', 'instrument_class', 'expiration']
            available_cols = [col for col in sample_cols if col in df.columns]
            print(df[available_cols].head(10))
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Try trades data for NQ.OPT
    print("\n📋 TEST 2: Get Trades for NQ Options")
    print("-" * 40)
    
    try:
        print("🔍 Testing trades data for NQ.OPT...")
        
        trades = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="trades",
            start="2025-07-15",
            end="2025-07-16",
            stype_in="parent",
            limit=100
        )
        
        trades_df = trades.to_df()
        print(f"✅ Found {len(trades_df)} option trades")
        
        if len(trades_df) > 0:
            print("\n📊 Sample option trades:")
            print(trades_df[['symbol', 'price', 'size', 'ts_event']].head())
            
    except Exception as e:
        print(f"❌ Trades error: {e}")
    
    # Test 3: Get cost for NQ options
    print("\n📋 TEST 3: Cost Estimation for NQ.OPT")
    print("-" * 40)
    
    try:
        cost = client.metadata.get_cost(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="trades",
            start="2025-07-15",
            end="2025-07-16",
            stype_in="parent"
        )
        
        print(f"✅ Cost for NQ options data: ${cost}")
        
    except Exception as e:
        print(f"❌ Cost error: {e}")
    
    # Test 4: Try symbology resolution with correct format
    print("\n📋 TEST 4: Symbology Resolution")
    print("-" * 40)
    
    try:
        # Test if symbology.resolve works without 'start' parameter
        resolved = client.symbology.resolve(
            dataset="GLBX.MDP3",
            symbols=["NQ.OPT", "Q3C", "Q3CN25"]
        )
        
        print(f"✅ Symbology resolved:")
        for symbol, result in resolved.items():
            print(f"   {symbol} → {result}")
            
    except Exception as e:
        print(f"❌ Symbology error: {e}")
    
    print(f"\n🎯 Testing complete!")
    
if __name__ == "__main__":
    main()
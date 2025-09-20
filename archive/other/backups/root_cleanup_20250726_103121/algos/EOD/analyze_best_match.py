#!/usr/bin/env python3
"""
Deep analysis of the best matching option: UD:2V: VT 2538219
Price: $17.25 (target: $17.00)
Expires: 2025-07-18 21:59:00+00:00 (tomorrow!)
"""

import databento as db
import pandas as pd

def main():
    """Analyze the best matching option in detail"""
    print("🔍 DEEP ANALYSIS OF BEST MATCH")
    print("="*60)
    
    best_match_symbol = "UD:2V: VT 2538219"
    target_price = 17.00
    target_volume = 1024
    target_bid = 13.00
    target_ask = 13.75
    
    print(f"BEST MATCH: {best_match_symbol}")
    print(f"   Target price: ${target_price}")
    print(f"   Actual price: $17.25 (difference: $0.25)")
    print(f"   Expires: 2025-07-18 21:59:00+00:00 (TOMORROW!)")
    print("="*60)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    
    try:
        # Get comprehensive data for this specific option
        print(f"\n📊 Getting comprehensive data for {best_match_symbol}...")
        
        # 1. Get all trades
        trades = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols=[best_match_symbol],
            schema="trades",
            start="2025-07-15",
            end="2025-07-17",
            limit=500
        )
        
        trades_df = trades.to_df()
        print(f"✅ Found {len(trades_df)} trades")
        
        if len(trades_df) > 0:
            # Analyze trading patterns
            latest_price = trades_df['price'].iloc[-1]
            first_price = trades_df['price'].iloc[0]
            high_price = trades_df['price'].max()
            low_price = trades_df['price'].min()
            total_volume = trades_df['size'].sum()
            avg_price = trades_df['price'].mean()
            
            price_change = latest_price - first_price
            
            print(f"\n📈 TRADING ANALYSIS:")
            print(f"   First Price: ${first_price:.2f}")
            print(f"   Latest Price: ${latest_price:.2f}")
            print(f"   Price Change: ${price_change:.2f}")
            print(f"   High: ${high_price:.2f}")
            print(f"   Low: ${low_price:.2f}")
            print(f"   Average: ${avg_price:.2f}")
            print(f"   Total Volume: {total_volume:,} contracts")
            
            # Compare to target characteristics
            print(f"\n🎯 COMPARISON TO TARGET:")
            print(f"   Price match: ${latest_price:.2f} vs ${target_price:.2f} (diff: ${abs(latest_price - target_price):.2f})")
            print(f"   Volume match: {total_volume:,} vs {target_volume:,} (diff: {abs(total_volume - target_volume):,})")
            
            # Show detailed trade history
            print(f"\n📋 TRADE HISTORY:")
            print(trades_df[['price', 'size', 'ts_event']].to_string())
            
            # Check if this matches the target's daily range
            if high_price >= 45.75 * 0.8 and low_price <= 11.75 * 1.2:
                print(f"\n🎯 POTENTIAL HIGH/LOW MATCH:")
                print(f"   Target High: $45.75 - Our High: ${high_price:.2f}")
                print(f"   Target Low: $11.75 - Our Low: ${low_price:.2f}")
        
        # 2. Get quotes
        print(f"\n💰 Getting quote data...")
        try:
            quotes = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols=[best_match_symbol],
                schema="tbbo",
                start="2025-07-16",
                end="2025-07-17",
                limit=100
            )
            
            quotes_df = quotes.to_df()
            print(f"✅ Found {len(quotes_df)} quotes")
            
            if len(quotes_df) > 0:
                latest_quote = quotes_df.iloc[-1]
                bid = latest_quote.get('bid_px_00', 0)
                ask = latest_quote.get('ask_px_00', 0)
                bid_size = latest_quote.get('bid_sz_00', 0)
                ask_size = latest_quote.get('ask_sz_00', 0)
                
                print(f"\n📊 LATEST QUOTE:")
                print(f"   Bid: ${bid:.2f} x {bid_size}")
                print(f"   Ask: ${ask:.2f} x {ask_size}")
                
                print(f"\n🎯 BID/ASK COMPARISON:")
                print(f"   Target Bid: ${target_bid:.2f} - Actual: ${bid:.2f} (diff: ${abs(bid - target_bid):.2f})")
                print(f"   Target Ask: ${target_ask:.2f} - Actual: ${ask:.2f} (diff: ${abs(ask - target_ask):.2f})")
                
                if abs(bid - target_bid) <= 5.0 and abs(ask - target_ask) <= 5.0:
                    print(f"   🎯 REASONABLE BID/ASK MATCH!")
                
                # Show quote history
                print(f"\n📋 RECENT QUOTES:")
                quote_cols = ['bid_px_00', 'ask_px_00', 'bid_sz_00', 'ask_sz_00', 'ts_event']
                available_cols = [col for col in quote_cols if col in quotes_df.columns]
                print(quotes_df[available_cols].tail(10).to_string())
        
        except Exception as e:
            print(f"   Quote data error: {e}")
        
        # 3. Get definition data
        print(f"\n📋 Getting instrument definition...")
        try:
            definition = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols=[best_match_symbol],
                schema="definition",
                start="2025-07-15",
                end="2025-07-17",
                limit=10
            )
            
            def_df = definition.to_df()
            if len(def_df) > 0:
                inst_info = def_df.iloc[0]
                
                print(f"✅ INSTRUMENT DETAILS:")
                print(f"   Symbol: {inst_info.get('symbol', 'N/A')}")
                print(f"   Raw Symbol: {inst_info.get('raw_symbol', 'N/A')}")
                print(f"   Expiration: {inst_info.get('expiration', 'N/A')}")
                print(f"   Strike Price: {inst_info.get('strike_price', 'N/A')}")
                print(f"   Security Type: {inst_info.get('security_type', 'N/A')}")
                print(f"   Instrument Class: {inst_info.get('instrument_class', 'N/A')}")
                print(f"   Underlying: {inst_info.get('underlying', 'N/A')}")
                print(f"   Exchange: {inst_info.get('exchange', 'N/A')}")
                print(f"   Contract Multiplier: {inst_info.get('contract_multiplier', 'N/A')}")
                
                # Check if this gives us clues about the strike
                strike_price = inst_info.get('strike_price')
                if pd.notna(strike_price):
                    print(f"\n🎯 STRIKE ANALYSIS:")
                    print(f"   Actual Strike: {strike_price}")
                    print(f"   Target Strike: 23,175")
                    print(f"   Difference: {abs(float(strike_price) - 23175) if strike_price else 'N/A'}")
        
        except Exception as e:
            print(f"   Definition data error: {e}")
        
        # 4. Check for other similar options expiring tomorrow
        print(f"\n🔍 Checking other options expiring July 18, 2025...")
        
        try:
            # Get all options expiring July 18
            all_july18 = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols="NQ.OPT",
                schema="definition",
                start="2025-07-16",
                end="2025-07-17",
                stype_in="parent"
            )
            
            july18_df = all_july18.to_df()
            july18_df['exp_str'] = july18_df['expiration'].astype(str)
            july18_options = july18_df[july18_df['exp_str'].str.contains('2025-07-18', na=False)]
            
            print(f"✅ Found {len(july18_options)} total options expiring July 18")
            
            # Look for options with strikes near 23,175
            if 'strike_price' in july18_options.columns:
                july18_options['strike_numeric'] = pd.to_numeric(july18_options['strike_price'], errors='coerce')
                near_strikes = july18_options[
                    (july18_options['strike_numeric'] >= 23000) & 
                    (july18_options['strike_numeric'] <= 23300)
                ]
                
                if len(near_strikes) > 0:
                    print(f"\n📊 July 18 options with strikes 23,000-23,300:")
                    for _, opt in near_strikes.iterrows():
                        print(f"   {opt['symbol']}: strike ${opt['strike_numeric']:.0f}")
        
        except Exception as e:
            print(f"   July 18 search error: {e}")
        
        print(f"\n🎯 CONCLUSION:")
        print(f"Symbol {best_match_symbol} appears to be the best match because:")
        print(f"   ✅ Price very close: ${latest_price:.2f} vs target ${target_price:.2f}")
        print(f"   ✅ Expires tomorrow: July 18, 2025")
        print(f"   ⚠️  Volume lower: {total_volume} vs target {target_volume}")
        print(f"   📋 Need to verify strike price and exact contract details")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
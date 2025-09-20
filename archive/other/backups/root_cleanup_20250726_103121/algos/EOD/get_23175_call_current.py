#!/usr/bin/env python3
"""
Get current data for NQ 23,175.00 call expiring July 18, 2025
Using only available data up to current time
"""

import databento as db
import pandas as pd
from datetime import datetime, timedelta

def main():
    """Get current data for specific strike"""
    print("🔍 GETTING CURRENT DATA FOR NQ 23,175 CALL EXPIRING JULY 18, 2025")
    print("="*70)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    
    try:
        # First, get all available options (within data range)
        print("📋 Finding 23,175 call option symbol...")
        
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="definition",
            start="2025-07-16",
            end="2025-07-17",  # Use only available data
            stype_in="parent"
        )
        
        df = data.to_df()
        print(f"✅ Retrieved {len(df)} NQ options")
        
        # Filter for July 18 expiration and 23,175 strike calls
        df['exp_str'] = df['expiration'].astype(str)
        july_18_options = df[df['exp_str'].str.contains('2025-07-18', na=False)]
        
        print(f"📊 Found {len(july_18_options)} options expiring July 18")
        
        # Show available strikes first
        if len(july_18_options) > 0 and 'strike_price' in july_18_options.columns:
            available_strikes = sorted(july_18_options['strike_price'].dropna().unique())
            print(f"📊 Available strikes for July 18: {available_strikes[:20]}...")  # Show first 20
            
            # Look for 23,175 strike calls
            target_strike = 23175.0
            strike_matches = july_18_options[july_18_options['strike_price'] == target_strike]
            
            # Filter for calls (contains 'C' in symbol)
            call_matches = strike_matches[strike_matches['symbol'].str.contains(' C', na=False)]
            
            if len(call_matches) > 0:
                target_symbol = call_matches['symbol'].iloc[0]
                print(f"🎯 Found target option: {target_symbol}")
                
                # Get recent market data for this specific option
                print(f"\n📊 Getting market data for {target_symbol}...")
                
                # Get trades data for today only
                trades = client.timeseries.get_range(
                    dataset="GLBX.MDP3",
                    symbols=[target_symbol],
                    schema="trades",
                    start="2025-07-17",
                    end="2025-07-17",
                    limit=100
                )
                
                trades_df = trades.to_df()
                print(f"✅ Found {len(trades_df)} trades for {target_symbol} today")
                
                if len(trades_df) > 0:
                    # Show recent trades
                    print("\n📈 Recent trades:")
                    recent_trades = trades_df[['symbol', 'price', 'size', 'ts_event']].tail(10)
                    print(recent_trades)
                    
                    # Calculate some basic stats
                    latest_price = trades_df['price'].iloc[-1]
                    avg_price = trades_df['price'].mean()
                    volume = trades_df['size'].sum()
                    price_std = trades_df['price'].std()
                    
                    print(f"\n📊 Trading Summary for {target_symbol}:")
                    print(f"   Latest Price: ${latest_price:.2f}")
                    print(f"   Average Price: ${avg_price:.2f}")
                    print(f"   Price Std Dev: ${price_std:.2f}")
                    print(f"   Total Volume: {volume:,} contracts")
                    
                    # Save the data
                    trades_df.to_csv(f"nq_23175_call_trades.csv", index=False)
                    print(f"\n💾 Saved trades to nq_23175_call_trades.csv")
                    
                else:
                    print("❌ No trades found for this option today")
                
                # Get quotes data for bid/ask spread
                try:
                    print(f"\n📊 Getting quotes for {target_symbol}...")
                    quotes = client.timeseries.get_range(
                        dataset="GLBX.MDP3",
                        symbols=[target_symbol],
                        schema="tbbo",  # Top of book quotes
                        start="2025-07-17",
                        end="2025-07-17",
                        limit=20
                    )
                    
                    quotes_df = quotes.to_df()
                    print(f"✅ Found {len(quotes_df)} quotes")
                    
                    if len(quotes_df) > 0:
                        print("\n💰 Latest Bid/Ask:")
                        latest_quote = quotes_df.tail(1)
                        print(latest_quote[['symbol', 'bid_px_00', 'ask_px_00', 'bid_sz_00', 'ask_sz_00', 'ts_event']])
                        
                        # Calculate spread
                        bid = latest_quote['bid_px_00'].iloc[0]
                        ask = latest_quote['ask_px_00'].iloc[0]
                        spread = ask - bid if pd.notna(bid) and pd.notna(ask) else None
                        
                        if spread is not None:
                            print(f"\n📊 Spread Analysis:")
                            print(f"   Bid: ${bid:.2f}")
                            print(f"   Ask: ${ask:.2f}")
                            print(f"   Spread: ${spread:.2f}")
                            print(f"   Spread %: {(spread/ask)*100:.2f}%")
                        
                except Exception as e:
                    print(f"⚠️  Quotes data error: {e}")
                
                # Get underlying futures price for context
                try:
                    print(f"\n📊 Getting underlying NQ futures price...")
                    nq_data = client.timeseries.get_range(
                        dataset="GLBX.MDP3",
                        symbols=["NQU5"],  # September contract
                        schema="trades",
                        start="2025-07-17",
                        end="2025-07-17",
                        limit=10
                    )
                    
                    nq_df = nq_data.to_df()
                    if len(nq_df) > 0:
                        nq_price = nq_df['price'].iloc[-1]
                        print(f"   Latest NQ futures price: ${nq_price:.2f}")
                        
                        # Calculate option metrics
                        if len(trades_df) > 0:
                            intrinsic = max(0, nq_price - target_strike)
                            time_value = latest_price - intrinsic
                            
                            print(f"\n📊 Option Analysis:")
                            print(f"   Underlying: ${nq_price:.2f}")
                            print(f"   Strike: ${target_strike:.2f}")
                            print(f"   Option Price: ${latest_price:.2f}")
                            print(f"   Intrinsic Value: ${intrinsic:.2f}")
                            print(f"   Time Value: ${time_value:.2f}")
                            print(f"   Moneyness: {((nq_price/target_strike)-1)*100:.2f}%")
                        
                except Exception as e:
                    print(f"⚠️  Underlying data error: {e}")
                
            else:
                print(f"❌ No call option found for strike ${target_strike}")
                
                # Find closest strikes
                if len(july_18_options) > 0:
                    strikes = july_18_options['strike_price'].dropna().unique()
                    closest_strikes = sorted(strikes, key=lambda x: abs(x - target_strike))[:5]
                    print(f"📊 Closest available strikes: {closest_strikes}")
        
        else:
            print("❌ No July 18 options found or no strike price data")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
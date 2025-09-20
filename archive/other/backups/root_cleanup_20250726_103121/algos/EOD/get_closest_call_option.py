#!/usr/bin/env python3
"""
Get the closest call option to 23,175 strike that expires July 18, 2025
"""

import databento as db
import pandas as pd

def main():
    """Find closest call to 23,175 strike"""
    print("🔍 FINDING CLOSEST CALL TO 23,175 STRIKE EXPIRING JULY 18, 2025")
    print("="*70)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    
    try:
        # Get current NQ price for context
        print("📊 Getting current NQ futures price...")
        nq_data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols=["NQU5"],
            schema="trades",
            start="2025-07-16",
            end="2025-07-17",
            limit=5
        )
        
        nq_df = nq_data.to_df()
        current_nq = nq_df['price'].iloc[-1] if len(nq_df) > 0 else 23000
        print(f"   Current NQ price: ${current_nq:.2f}")
        
        # Get all option trades to see available strikes
        print(f"\n📋 Getting NQ option trades...")
        
        trades = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="trades",
            start="2025-07-16",
            end="2025-07-17",
            stype_in="parent",
            limit=500
        )
        
        trades_df = trades.to_df()
        print(f"✅ Retrieved {len(trades_df)} option trades")
        
        # Extract all unique call symbols and their strikes
        unique_symbols = trades_df['symbol'].unique()
        
        # Filter for calls only
        call_symbols = [s for s in unique_symbols if ' C' in str(s)]
        print(f"📊 Found {len(call_symbols)} unique call symbols")
        
        # Extract strikes from call symbols
        call_strikes = []
        for symbol in call_symbols:
            try:
                # Format: "NQU5 C23000" - extract the number after C
                if ' C' in symbol:
                    strike_str = symbol.split(' C')[1]
                    strike = float(strike_str)
                    call_strikes.append((symbol, strike))
            except:
                continue
        
        # Sort by strike price
        call_strikes.sort(key=lambda x: x[1])
        
        print(f"\n📊 Available call strikes:")
        for symbol, strike in call_strikes:
            print(f"   ${strike:.0f}: {symbol}")
        
        # Find closest to 23,175
        target_strike = 23175
        closest_call = min(call_strikes, key=lambda x: abs(x[1] - target_strike))
        closest_symbol, closest_strike = closest_call
        
        print(f"\n🎯 CLOSEST CALL TO ${target_strike}:")
        print(f"   Symbol: {closest_symbol}")
        print(f"   Strike: ${closest_strike:.0f}")
        print(f"   Difference: ${abs(closest_strike - target_strike):.0f}")
        
        # Check if this expires July 18
        # For NQ options, we need to check if this is a July 18 expiry
        # NQU5 = September contract, but options can expire before underlying
        
        # Get recent trades for this specific option
        print(f"\n📈 Getting recent trades for {closest_symbol}...")
        
        specific_trades = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols=[closest_symbol],
            schema="trades",
            start="2025-07-16",
            end="2025-07-17",
            limit=50
        )
        
        specific_df = specific_trades.to_df()
        print(f"✅ Found {len(specific_df)} trades for {closest_symbol}")
        
        if len(specific_df) > 0:
            # Calculate trading metrics
            latest_price = specific_df['price'].iloc[-1]
            avg_price = specific_df['price'].mean()
            total_volume = specific_df['size'].sum()
            price_std = specific_df['price'].std()
            
            print(f"\n📊 TRADING DATA for {closest_symbol}:")
            print(f"   Latest Price: ${latest_price:.2f}")
            print(f"   Average Price: ${avg_price:.2f}")
            print(f"   Price Volatility (std): ${price_std:.2f}")
            print(f"   Total Volume: {total_volume:,} contracts")
            
            # Show recent trades
            print(f"\n📈 Recent trades:")
            recent = specific_df[['price', 'size', 'ts_event']].tail(10)
            print(recent)
            
            # Calculate option metrics
            print(f"\n📊 OPTION ANALYSIS:")
            print(f"   Underlying (NQ): ${current_nq:.2f}")
            print(f"   Strike: ${closest_strike:.2f}")
            print(f"   Option Price: ${latest_price:.2f}")
            
            # Calculate intrinsic and time value
            intrinsic = max(0, current_nq - closest_strike)
            time_value = latest_price - intrinsic
            moneyness = (current_nq / closest_strike - 1) * 100
            
            print(f"   Intrinsic Value: ${intrinsic:.2f}")
            print(f"   Time Value: ${time_value:.2f}")
            print(f"   Moneyness: {moneyness:.2f}%")
            
            if moneyness > 0:
                print(f"   Status: IN THE MONEY")
            elif moneyness > -2:
                print(f"   Status: NEAR THE MONEY")
            else:
                print(f"   Status: OUT OF THE MONEY")
            
            # Estimate implied volatility context
            # Note: This is not actual IV calculation, just price volatility
            if price_std > 0:
                price_vol_pct = (price_std / avg_price) * 100
                print(f"   Price Volatility: {price_vol_pct:.1f}%")
        
        # Try to get quotes for bid/ask spread
        try:
            print(f"\n💰 Getting current bid/ask for {closest_symbol}...")
            
            quotes = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                symbols=[closest_symbol],
                schema="tbbo",
                start="2025-07-16",
                end="2025-07-17",
                limit=10
            )
            
            quotes_df = quotes.to_df()
            if len(quotes_df) > 0:
                latest_quote = quotes_df.iloc[-1]
                bid = latest_quote.get('bid_px_00', 0)
                ask = latest_quote.get('ask_px_00', 0)
                
                if bid > 0 and ask > 0:
                    spread = ask - bid
                    mid = (bid + ask) / 2
                    spread_pct = (spread / mid) * 100
                    
                    print(f"   Bid: ${bid:.2f}")
                    print(f"   Ask: ${ask:.2f}")
                    print(f"   Mid: ${mid:.2f}")
                    print(f"   Spread: ${spread:.2f} ({spread_pct:.1f}%)")
                
        except Exception as e:
            print(f"⚠️  Quote data error: {e}")
        
        # Save the data
        if len(specific_df) > 0:
            filename = f"nq_{closest_strike:.0f}_call_data.csv"
            specific_df.to_csv(filename, index=False)
            print(f"\n💾 Saved trade data to {filename}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
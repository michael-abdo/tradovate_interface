#!/usr/bin/env python3
"""
Search specifically for standard NQ options (NQU5, NQZ5, NQH6 format)
that might match the target characteristics
"""

import databento as db
import pandas as pd

def main():
    """Search standard NQ options for best match"""
    print("🔍 SEARCHING STANDARD NQ OPTIONS FOR MATCH")
    print("="*60)
    print("TARGET: Strike ~23,175C, Last=$17.00, Vol=1,024, Bid=$13.00/Ask=$13.75")
    print("="*60)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    
    target_price = 17.00
    target_volume = 1024
    target_bid = 13.00
    target_ask = 13.75
    
    try:
        # Get all NQ option trades
        print("\n📋 Getting all NQ option trades...")
        
        trades = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="trades",
            start="2025-07-14",  # Get more days
            end="2025-07-17",
            stype_in="parent",
            limit=3000
        )
        
        trades_df = trades.to_df()
        print(f"✅ Retrieved {len(trades_df)} option trades")
        
        # Filter for only standard NQ symbols (NQU5, NQZ5, NQH6 format)
        standard_symbols = []
        for symbol in trades_df['symbol'].unique():
            if any(prefix in str(symbol) for prefix in ['NQU5', 'NQZ5', 'NQH6', 'NQM6']):
                standard_symbols.append(symbol)
        
        print(f"📊 Found {len(standard_symbols)} standard NQ option symbols")
        
        # Analyze each standard symbol
        candidates = []
        for symbol in standard_symbols:
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            if len(symbol_trades) > 0:
                latest_price = symbol_trades['price'].iloc[-1]
                total_volume = symbol_trades['size'].sum()
                avg_price = symbol_trades['price'].mean()
                
                # Extract strike from symbol (e.g., "NQU5 C23000" -> 23000)
                strike = None
                try:
                    if ' C' in symbol:
                        strike_str = symbol.split(' C')[1]
                        strike = int(strike_str)
                    elif ' P' in symbol:
                        strike_str = symbol.split(' P')[1]
                        strike = int(strike_str)
                except:
                    strike = None
                
                candidates.append({
                    'symbol': symbol,
                    'latest_price': latest_price,
                    'total_volume': total_volume,
                    'avg_price': avg_price,
                    'strike': strike,
                    'trades_count': len(symbol_trades),
                    'option_type': 'call' if ' C' in symbol else 'put'
                })
        
        # Sort candidates by different criteria
        print(f"\n🎯 ANALYSIS 1: Options with price closest to ${target_price}")
        print("-" * 60)
        
        price_sorted = sorted(candidates, key=lambda x: abs(x['latest_price'] - target_price))
        
        for i, cand in enumerate(price_sorted[:15]):
            price_diff = abs(cand['latest_price'] - target_price)
            strike_diff = abs(cand['strike'] - 23175) if cand['strike'] else float('inf')
            
            strike_display = str(cand['strike']) if cand['strike'] else 'N/A'
            print(f"{i+1:2d}. {cand['symbol']:15s} | "
                  f"${cand['latest_price']:6.2f} (±${price_diff:5.2f}) | "
                  f"Vol: {cand['total_volume']:4d} | "
                  f"Strike: {strike_display:>5s} (±{strike_diff:4.0f}) | "
                  f"{cand['option_type']:4s}")
        
        # Look specifically for deep OTM calls that might match
        print(f"\n🎯 ANALYSIS 2: Deep OTM calls (strike > 25000) with low prices")
        print("-" * 60)
        
        deep_otm_calls = [c for c in candidates if 
                         c['option_type'] == 'call' and 
                         c['strike'] and c['strike'] > 25000 and
                         c['latest_price'] < 50]
        
        deep_otm_calls.sort(key=lambda x: abs(x['latest_price'] - target_price))
        
        for i, cand in enumerate(deep_otm_calls[:10]):
            price_diff = abs(cand['latest_price'] - target_price)
            
            print(f"{i+1:2d}. {cand['symbol']:15s} | "
                  f"${cand['latest_price']:6.2f} (±${price_diff:5.2f}) | "
                  f"Vol: {cand['total_volume']:4d} | "
                  f"Strike: ${cand['strike']:,}")
        
        # Look for high volume options that might match
        print(f"\n🎯 ANALYSIS 3: High volume options (>50 contracts)")
        print("-" * 60)
        
        high_vol = [c for c in candidates if c['total_volume'] > 50]
        high_vol.sort(key=lambda x: abs(x['latest_price'] - target_price))
        
        for i, cand in enumerate(high_vol[:15]):
            price_diff = abs(cand['latest_price'] - target_price)
            
            strike_display = str(cand['strike']) if cand['strike'] else 'N/A'
            print(f"{i+1:2d}. {cand['symbol']:15s} | "
                  f"${cand['latest_price']:6.2f} (±${price_diff:5.2f}) | "
                  f"Vol: {cand['total_volume']:4d} | "
                  f"Strike: {strike_display:>5s}")
        
        # Check if any have similar bid/ask
        print(f"\n💰 CHECKING BID/ASK FOR TOP PRICE MATCHES")
        print("-" * 60)
        
        for cand in price_sorted[:5]:
            symbol = cand['symbol']
            print(f"\n📊 {symbol} (${cand['latest_price']:.2f})")
            
            try:
                quotes = client.timeseries.get_range(
                    dataset="GLBX.MDP3",
                    symbols=[symbol],
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
                    
                    bid_diff = abs(bid - target_bid) if bid > 0 else float('inf')
                    ask_diff = abs(ask - target_ask) if ask > 0 else float('inf')
                    
                    print(f"   Bid: ${bid:.2f} (±${bid_diff:.2f}) | Ask: ${ask:.2f} (±${ask_diff:.2f})")
                    
                    if bid_diff <= 5 and ask_diff <= 5:
                        print(f"   🎯 GOOD BID/ASK MATCH!")
                else:
                    print(f"   No quote data")
                    
            except Exception as e:
                print(f"   Quote error: {e}")
        
        # Summary of best overall match
        print(f"\n🏆 BEST OVERALL STANDARD NQ OPTION MATCH")
        print("=" * 60)
        
        if price_sorted:
            best = price_sorted[0]
            print(f"Symbol: {best['symbol']}")
            print(f"Latest Price: ${best['latest_price']:.2f} (target: ${target_price})")
            print(f"Volume: {best['total_volume']} contracts (target: {target_volume})")
            print(f"Strike: {best['strike']} (target: ~23,175)")
            print(f"Option Type: {best['option_type']}")
            print(f"Total Trades: {best['trades_count']}")
            
            # Check if this expires tomorrow
            try:
                definition = client.timeseries.get_range(
                    dataset="GLBX.MDP3",
                    symbols=[best['symbol']],
                    schema="definition",
                    start="2025-07-16",
                    end="2025-07-17",
                    limit=5
                )
                
                def_df = definition.to_df()
                if len(def_df) > 0:
                    expiration = def_df['expiration'].iloc[0]
                    print(f"Expiration: {expiration}")
                    
                    if '2025-07-18' in str(expiration):
                        print(f"🎯 EXPIRES TOMORROW!")
                
            except Exception as e:
                print(f"Expiration check error: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
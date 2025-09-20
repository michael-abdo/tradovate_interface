#!/usr/bin/env python3
"""
Search for NQ option that matches these characteristics:
Strike: 23,175.00C
Last: $17.00
Volume: 1,024
Bid: $13.00 / Ask: $13.75
"""

import databento as db
import pandas as pd
import numpy as np

def main():
    """Search for matching option across all available data"""
    print("🔍 SEARCHING FOR MATCHING OPTION")
    print("="*60)
    print("TARGET CHARACTERISTICS:")
    print("   Strike: 23,175.00C")
    print("   Last: $17.00")
    print("   Volume: 1,024")
    print("   Bid: $13.00 / Ask: $13.75")
    print("="*60)
    
    client = db.Historical("db-nYu9cNrisvKGWiUNFQVRcTdLcDYKQ")
    
    target_price = 17.00
    target_volume = 1024
    target_bid = 13.00
    target_ask = 13.75
    target_strike = 23175
    
    try:
        # Get comprehensive option trades data
        print("\n📋 Getting comprehensive NQ option trades...")
        
        trades = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            symbols="NQ.OPT",
            schema="trades",
            start="2025-07-15",  # Get more days of data
            end="2025-07-17",
            stype_in="parent",
            limit=2000  # Get more data
        )
        
        trades_df = trades.to_df()
        print(f"✅ Retrieved {len(trades_df)} option trades")
        
        # Analyze all unique symbols
        unique_symbols = trades_df['symbol'].unique()
        print(f"📊 Found {len(unique_symbols)} unique option symbols")
        
        # 1. SEARCH BY PRICE RANGE
        print(f"\n🎯 SEARCH 1: Options with price near ${target_price}")
        print("-" * 50)
        
        price_matches = []
        for symbol in unique_symbols:
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            if len(symbol_trades) > 0:
                latest_price = symbol_trades['price'].iloc[-1]
                avg_price = symbol_trades['price'].mean()
                total_volume = symbol_trades['size'].sum()
                
                # Check if price is close to target
                if abs(latest_price - target_price) <= 5.0:  # Within $5
                    price_matches.append({
                        'symbol': symbol,
                        'latest_price': latest_price,
                        'avg_price': avg_price,
                        'total_volume': total_volume,
                        'price_diff': abs(latest_price - target_price),
                        'trades_count': len(symbol_trades)
                    })
        
        if price_matches:
            price_matches.sort(key=lambda x: x['price_diff'])
            print(f"   Found {len(price_matches)} options with price near ${target_price}")
            
            for match in price_matches[:10]:
                print(f"   {match['symbol']}: ${match['latest_price']:.2f} (vol: {match['total_volume']}, diff: ${match['price_diff']:.2f})")
        else:
            print(f"   No options found with price near ${target_price}")
        
        # 2. SEARCH BY VOLUME
        print(f"\n🎯 SEARCH 2: Options with volume near {target_volume}")
        print("-" * 50)
        
        volume_matches = []
        for symbol in unique_symbols:
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            if len(symbol_trades) > 0:
                total_volume = symbol_trades['size'].sum()
                latest_price = symbol_trades['price'].iloc[-1]
                
                # Check if volume is close to target
                if abs(total_volume - target_volume) <= 200:  # Within 200 contracts
                    volume_matches.append({
                        'symbol': symbol,
                        'total_volume': total_volume,
                        'latest_price': latest_price,
                        'volume_diff': abs(total_volume - target_volume),
                        'trades_count': len(symbol_trades)
                    })
        
        if volume_matches:
            volume_matches.sort(key=lambda x: x['volume_diff'])
            print(f"   Found {len(volume_matches)} options with volume near {target_volume}")
            
            for match in volume_matches[:10]:
                print(f"   {match['symbol']}: vol={match['total_volume']} (price: ${match['latest_price']:.2f}, diff: {match['volume_diff']})")
        else:
            print(f"   No options found with volume near {target_volume}")
        
        # 3. SEARCH BY STRIKE PATTERN
        print(f"\n🎯 SEARCH 3: Options with strikes containing '23' or similar")
        print("-" * 50)
        
        strike_matches = []
        # Look for symbols that might contain parts of 23175
        for symbol in unique_symbols:
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            if len(symbol_trades) > 0:
                latest_price = symbol_trades['price'].iloc[-1]
                total_volume = symbol_trades['size'].sum()
                
                # Check if symbol contains strike-like patterns
                if any(pattern in symbol for pattern in ['231', '232', '175', '180', '170']):
                    strike_matches.append({
                        'symbol': symbol,
                        'latest_price': latest_price,
                        'total_volume': total_volume,
                        'trades_count': len(symbol_trades)
                    })
        
        if strike_matches:
            # Sort by price closeness to target
            strike_matches.sort(key=lambda x: abs(x['latest_price'] - target_price))
            print(f"   Found {len(strike_matches)} options with relevant strike patterns")
            
            for match in strike_matches[:15]:
                print(f"   {match['symbol']}: ${match['latest_price']:.2f} (vol: {match['total_volume']})")
        
        # 4. COMPREHENSIVE SCORING
        print(f"\n🎯 SEARCH 4: Comprehensive scoring for best match")
        print("-" * 50)
        
        best_matches = []
        for symbol in unique_symbols:
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            if len(symbol_trades) > 0:
                latest_price = symbol_trades['price'].iloc[-1]
                total_volume = symbol_trades['size'].sum()
                
                # Calculate composite score
                price_score = max(0, 10 - abs(latest_price - target_price))
                volume_score = max(0, 10 - abs(total_volume - target_volume) / 100)
                
                # Bonus for call options and relevant strikes
                symbol_bonus = 0
                if ' C' in symbol:
                    symbol_bonus += 2
                if any(pattern in symbol for pattern in ['231', '232', '233']):
                    symbol_bonus += 3
                
                total_score = price_score + volume_score + symbol_bonus
                
                if total_score > 5:  # Only consider decent matches
                    best_matches.append({
                        'symbol': symbol,
                        'latest_price': latest_price,
                        'total_volume': total_volume,
                        'total_score': total_score,
                        'price_score': price_score,
                        'volume_score': volume_score,
                        'trades_count': len(symbol_trades)
                    })
        
        if best_matches:
            best_matches.sort(key=lambda x: x['total_score'], reverse=True)
            print(f"   Top {min(15, len(best_matches))} best matches:")
            
            for i, match in enumerate(best_matches[:15]):
                print(f"   {i+1}. {match['symbol']}: score={match['total_score']:.1f} "
                      f"(price: ${match['latest_price']:.2f}, vol: {match['total_volume']})")
        
        # 5. CHECK QUOTES FOR TOP MATCHES
        if best_matches:
            print(f"\n💰 CHECKING QUOTES FOR TOP 3 MATCHES")
            print("-" * 50)
            
            for i, match in enumerate(best_matches[:3]):
                symbol = match['symbol']
                print(f"\n📊 {i+1}. {symbol}")
                
                try:
                    # Get quotes
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
                        
                        print(f"   Latest Price: ${match['latest_price']:.2f}")
                        print(f"   Volume: {match['total_volume']} contracts")
                        print(f"   Bid: ${bid:.2f}")
                        print(f"   Ask: ${ask:.2f}")
                        
                        # Compare to target
                        bid_diff = abs(bid - target_bid)
                        ask_diff = abs(ask - target_ask)
                        
                        print(f"   Bid vs Target (${target_bid}): ${bid_diff:.2f} difference")
                        print(f"   Ask vs Target (${target_ask}): ${ask_diff:.2f} difference")
                        
                        if bid_diff <= 2.0 and ask_diff <= 2.0:
                            print(f"   🎯 STRONG BID/ASK MATCH!")
                    else:
                        print(f"   No quote data available")
                        
                except Exception as e:
                    print(f"   Quote error: {e}")
        
        # 6. GET EXPIRATION INFO FOR BEST MATCHES
        print(f"\n📅 CHECKING EXPIRATION DATES FOR BEST MATCHES")
        print("-" * 50)
        
        if best_matches:
            # Get definitions for top matches
            top_symbols = [match['symbol'] for match in best_matches[:5]]
            
            try:
                definitions = client.timeseries.get_range(
                    dataset="GLBX.MDP3",
                    symbols=top_symbols,
                    schema="definition",
                    start="2025-07-15",
                    end="2025-07-17",
                    limit=50
                )
                
                def_df = definitions.to_df()
                if len(def_df) > 0:
                    print(f"   Found definition data for {len(def_df)} options")
                    
                    for symbol in top_symbols:
                        symbol_def = def_df[def_df['symbol'] == symbol]
                        if len(symbol_def) > 0:
                            expiration = symbol_def['expiration'].iloc[0]
                            print(f"   {symbol}: expires {expiration}")
                        else:
                            print(f"   {symbol}: expiration data not found")
                
            except Exception as e:
                print(f"   Definition data error: {e}")
        
        print(f"\n🎯 Search complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
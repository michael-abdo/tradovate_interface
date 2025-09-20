#!/usr/bin/env python3
"""
DEAD Simple Strategy Demo
Shows the strategy in action with realistic market data
"""

from solution import DeadSimpleVolumeSpike
from datetime import datetime

def run_demo():
    """Run demonstration of DEAD Simple strategy"""
    
    print("=" * 60)
    print("DEAD SIMPLE STRATEGY DEMO")
    print("Following Institutional Money Flow")
    print("=" * 60)
    
    # Current NQ price
    current_price = 21870
    print(f"\nCurrent NQ Price: ${current_price:,.2f}")
    
    # Realistic options data (based on actual institutional flow patterns)
    options_data = [
        # EXTREME signal - 55x ratio, $1.95M flow
        {
            'strike': 21840,
            'optionType': 'PUT',
            'volume': 2750,
            'openInterest': 50,
            'lastPrice': 35.5,
            'expirationDate': '2024-01-10'
        },
        # Very high signal - 35x ratio, $1M flow
        {
            'strike': 21850,
            'optionType': 'PUT', 
            'volume': 1750,
            'openInterest': 50,
            'lastPrice': 30.0,
            'expirationDate': '2024-01-10'
        },
        # High signal - 25x ratio, $1M flow
        {
            'strike': 21900,
            'optionType': 'CALL',
            'volume': 2000,
            'openInterest': 80,
            'lastPrice': 25.0,
            'expirationDate': '2024-01-10'
        },
        # Moderate signal - 12x ratio, $600K flow
        {
            'strike': 21920,
            'optionType': 'CALL',
            'volume': 1200,
            'openInterest': 100,
            'lastPrice': 25.0,
            'expirationDate': '2024-01-10'
        },
        # Noise - should be filtered out (low ratio)
        {
            'strike': 21800,
            'optionType': 'PUT',
            'volume': 100,
            'openInterest': 200,
            'lastPrice': 40.0,
            'expirationDate': '2024-01-10'
        },
        # Noise - should be filtered out (small size)
        {
            'strike': 21950,
            'optionType': 'CALL',
            'volume': 600,
            'openInterest': 50,
            'lastPrice': 5.0,  # Only $60K - too small
            'expirationDate': '2024-01-10'
        }
    ]
    
    # Initialize analyzer
    analyzer = DeadSimpleVolumeSpike()
    
    # Find institutional flow
    print("\n🔍 Scanning for Institutional Flow...")
    print("-" * 50)
    
    signals = analyzer.find_institutional_flow(options_data, current_price)
    
    print(f"\n✅ Found {len(signals)} Institutional Signals:\n")
    
    # Display each signal
    for i, signal in enumerate(signals, 1):
        print(f"{i}. {signal.strike}{signal.option_type[0]} - {signal.confidence}")
        print(f"   📊 Vol/OI Ratio: {signal.vol_oi_ratio:.1f}x")
        print(f"   💰 Dollar Size: ${signal.dollar_size:,.0f}")
        print(f"   🎯 Direction: {signal.direction} → Target ${signal.target_price:,.2f}")
        print()
    
    # Generate institutional summary
    summary = analyzer.summarize_institutional_activity(signals)
    
    print("\n📈 INSTITUTIONAL POSITIONING SUMMARY")
    print("-" * 50)
    print(f"Total Dollar Volume: ${summary['total_dollar_volume']:,.0f}")
    print(f"Call Volume: ${summary['call_dollar_volume']:,.0f} ({summary['call_percentage']:.1f}%)")
    print(f"Put Volume: ${summary['put_dollar_volume']:,.0f} ({summary['put_percentage']:.1f}%)")
    print(f"Net Positioning: {summary['net_positioning']}")
    
    # Filter for actionable signals
    actionable = analyzer.filter_actionable_signals(signals, current_price, max_distance_percent=2.0)
    
    print(f"\n🎯 ACTIONABLE SIGNALS (within 2% of current price)")
    print("-" * 50)
    print(f"Found {len(actionable)} actionable signals\n")
    
    # Generate trade plans
    for signal in actionable[:2]:  # Top 2 actionable
        trade_plan = analyzer.generate_trade_plan(signal, current_price)
        
        print(f"📍 {signal.strike}{signal.option_type[0]} - {signal.confidence} Signal")
        print(f"   Entry: ${trade_plan['entry_price']:,.2f}")
        print(f"   Target: ${trade_plan['take_profit']:,.2f}")
        print(f"   Stop: ${trade_plan['stop_loss']:,.2f}")
        print(f"   Size Multiplier: {trade_plan['size_multiplier']}x")
        print(f"   Note: {trade_plan['notes']}")
        print()
    
    # Trading recommendations
    print("\n💡 TRADING RECOMMENDATIONS")
    print("-" * 50)
    
    if actionable:
        top_signal = actionable[0]
        if top_signal.confidence == "EXTREME":
            print("🚨 EXTREME INSTITUTIONAL FLOW DETECTED!")
            print(f"   {top_signal.vol_oi_ratio:.0f}x normal volume at {top_signal.strike}")
            print(f"   ${top_signal.dollar_size:,.0f} saying price going to ${top_signal.target_price}")
            print(f"   ACTION: {top_signal.direction} IMMEDIATELY")
        elif top_signal.confidence == "VERY_HIGH":
            print("⚡ VERY HIGH Institutional Activity")
            print(f"   Strong positioning at {top_signal.strike}")
            print(f"   ACTION: {top_signal.direction} with high confidence")
        else:
            print("📌 Institutional Flow Detected")
            print(f"   Notable activity at {top_signal.strike}")
            print(f"   ACTION: Consider {top_signal.direction} position")
    
    # Key insights
    print("\n🔑 KEY INSIGHTS")
    print("-" * 50)
    print("1. Big money has better info - we're just following")
    print("2. 50x+ volume ratios = EXTREME conviction")
    print("3. Price WILL gravitate to high volume strikes")
    print("4. Market makers MUST hedge = mechanical move")
    print("\n✅ Strategy Status: READY FOR LIVE TRADING")

if __name__ == "__main__":
    run_demo()
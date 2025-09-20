#!/usr/bin/env python3
"""
Analyze strikes near a specific level
"""

import json
import sys

def analyze_nearby_strikes(target_strike=21720, range_width=150):
    """Analyze strikes within range of target"""
    
    with open('data/normalized/options_data.json', 'r') as f:
        data = json.load(f)
    
    print(f'Strikes near {target_strike} with significant open interest:')
    print('=' * 60)
    
    contracts = [(c['strike'], 
                  c.get('call_open_interest', 0), 
                  c.get('put_open_interest', 0),
                  c.get('call_mark_price', 0),
                  c.get('put_mark_price', 0)) 
                 for c in data['contracts'] 
                 if target_strike - range_width <= c['strike'] <= target_strike + range_width]
    
    contracts.sort(key=lambda x: x[0])
    
    current_price = 21376.75
    print(f'Current NQ Price: ${current_price:,.2f}')
    print(f'Target Analysis: ${target_strike:,}')
    print(f'Distance from current: {target_strike - current_price:+.0f} points\n')
    
    total_call_risk = 0
    total_put_risk = 0
    
    for strike, call_oi, put_oi, call_price, put_price in contracts:
        if call_oi > 0 or put_oi > 0:
            distance = strike - current_price
            position = "ABOVE" if distance > 0 else "BELOW"
            
            # Calculate actual dollar risk
            call_risk = call_oi * 20 * call_price
            put_risk = put_oi * 20 * put_price
            
            total_call_risk += call_risk
            total_put_risk += put_risk
            
            print(f'Strike {strike}: {distance:+.0f} points {position}')
            print(f'  Call OI: {call_oi:.0f} contracts @ ${call_price:.2f} (${call_risk:,.0f} risk)')
            print(f'  Put OI: {put_oi:.0f} contracts @ ${put_price:.2f} (${put_risk:,.0f} risk)')
            
            if call_risk > put_risk * 1.2:
                print(f'  🐂 BULLS have MORE RISK at this strike')
            elif put_risk > call_risk * 1.2:
                print(f'  🐻 BEARS have MORE RISK at this strike')
            else:
                print(f'  ⚖️  BALANCED RISK at this strike')
            print()
    
    print(f'\n📊 TOTAL RISK NEAR {target_strike}:')
    print(f'  Total Call Risk (Bulls): ${total_call_risk:,.0f}')
    print(f'  Total Put Risk (Bears): ${total_put_risk:,.0f}')
    
    if total_call_risk > total_put_risk:
        print(f'\n🐂 BULLS have MORE TOTAL RISK in this area')
        print(f'  Risk Ratio: {total_call_risk/total_put_risk:.2f}:1 (Bulls:Bears)')
        print(f'  Implication: Bulls will defend/push through this area')
        print(f'  Trading Bias: SUPPORT likely, consider LONG positions')
    else:
        print(f'\n🐻 BEARS have MORE TOTAL RISK in this area')
        print(f'  Risk Ratio: {total_put_risk/total_call_risk:.2f}:1 (Bears:Bulls)')
        print(f'  Implication: Bears will defend this area as resistance')
        print(f'  Trading Bias: RESISTANCE likely, consider SHORT positions')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            strike = int(sys.argv[1])
            analyze_nearby_strikes(strike)
        except ValueError:
            print("Please provide a valid strike price as a number")
    else:
        analyze_nearby_strikes(21720)
#!/usr/bin/env python3
"""
Analyze risk at a specific strike price
"""

import sys
import os

# Add system to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tasks', 'options_trading_system'))

from data_ingestion.integration import run_data_ingestion
from analysis_engine.risk_analysis.solution import RiskAnalyzer

def analyze_strike_risk(strike_price=21720):
    """Analyze who has more risk at a specific strike price"""
    
    print(f'🎯 Analyzing risk at {strike_price} strike...')
    print('=' * 50)
    
    # Load data
    data_config = {
        'barchart': {'file_path': 'data/api_responses/options_data_20250602_141553.json'},
        'tradovate': {'mode': 'demo', 'cid': '6540', 'secret': 'f7a2b8f5-8348-424f-8ffa-047ab7502b7c', 'use_mock': True}
    }
    
    # Get the data
    data_result = run_data_ingestion(data_config)
    if data_result['pipeline_status'] != 'success':
        print('Failed to load data')
        return
    
    # Extract normalized data
    normalized_data = data_result['normalized_data']
    contracts = normalized_data['contracts']
    current_price = 21376.75  # Current NQ price from the data
    
    print(f'Current NQ Price: ${current_price:,.2f}')
    print(f'Target Strike: ${strike_price:,}')
    print(f'Distance from current: {strike_price - current_price:+.0f} points')
    print()
    
    # Find the strike data
    strike_data = None
    for contract in contracts:
        if contract['strike'] == strike_price:
            strike_data = contract
            break
    
    if strike_data:
        print(f'📊 {strike_price} Strike Analysis:')
        call_oi = strike_data.get('call_open_interest', 0)
        put_oi = strike_data.get('put_open_interest', 0)
        call_premium = strike_data.get('call_mark_price', 0)
        put_premium = strike_data.get('put_mark_price', 0)
        
        print(f'   Call Open Interest: {call_oi:.0f} contracts')
        print(f'   Put Open Interest: {put_oi:.0f} contracts')
        print(f'   Call Premium: ${call_premium:.2f}')
        print(f'   Put Premium: ${put_premium:.2f}')
        
        # Calculate dollar risk
        multiplier = 20  # NQ multiplier
        call_risk = call_oi * call_premium * multiplier
        put_risk = put_oi * put_premium * multiplier
        
        print()
        print('💰 Dollar Risk Exposure:')
        print(f'   Call Buyers Risk (Bulls): ${call_risk:,.0f}')
        print(f'   Put Buyers Risk (Bears): ${put_risk:,.0f}')
        
        # Determine position status
        print()
        print('📍 Position Analysis:')
        if strike_price > current_price:
            print(f'   Strike {strike_price} is {strike_price - current_price:.0f} points ABOVE current price')
            print('   📈 CALLS are OTM (Out of The Money)')
            print('   📉 PUTS are ITM (In The Money)')
        else:
            print(f'   Strike {strike_price} is {current_price - strike_price:.0f} points BELOW current price')
            print('   📈 CALLS are ITM (In The Money)')
            print('   📉 PUTS are OTM (Out of The Money)')
        
        # Risk assessment
        print()
        print('=' * 50)
        print('🎯 RISK ASSESSMENT:')
        
        if call_risk > put_risk:
            print(f'🐂 BULLS have MORE RISK at {strike_price}')
            print(f'   Bull Risk: ${call_risk:,.0f}')
            print(f'   Bear Risk: ${put_risk:,.0f}')
            if put_risk > 0:
                print(f'   Risk Ratio: {call_risk/put_risk:.2f}:1 (Bulls:Bears)')
            print()
            print('   📊 This means:')
            print('   - More bulls have positions that will lose if price stays below this strike')
            print('   - Bulls will likely defend this level to protect their positions')
            print('   - Expect SUPPORT around this strike')
        else:
            print(f'🐻 BEARS have MORE RISK at {strike_price}')
            print(f'   Bear Risk: ${put_risk:,.0f}')
            print(f'   Bull Risk: ${call_risk:,.0f}')
            if call_risk > 0:
                print(f'   Risk Ratio: {put_risk/call_risk:.2f}:1 (Bears:Bulls)')
            print()
            print('   📊 This means:')
            print('   - More bears have positions that will lose if price moves above this strike')
            print('   - Bears will likely defend this level to protect their positions')
            print('   - Expect RESISTANCE around this strike')
        
        # Trading implications
        print()
        print('💡 TRADING IMPLICATIONS:')
        if strike_price > current_price:  # Strike is above current price
            if call_risk > put_risk:
                print('   - Bulls need price to rise above this level')
                print('   - This creates MAGNETIC PULL upward')
                print('   - Consider LONG positions with this as target')
            else:
                print('   - Bears want price to stay below this level')
                print('   - This creates RESISTANCE ceiling')
                print('   - Consider SHORT positions from this level')
        else:  # Strike is below current price
            if put_risk > call_risk:
                print('   - Bears need price to fall below this level')
                print('   - This creates MAGNETIC PULL downward')
                print('   - Consider SHORT positions with this as target')
            else:
                print('   - Bulls want price to stay above this level')
                print('   - This creates SUPPORT floor')
                print('   - Consider LONG positions from this level')
    else:
        print(f'❌ Strike {strike_price} not found in the data')
    
    # Overall context
    print()
    print('\n📊 Overall Market Context:')
    risk_analyzer = RiskAnalyzer({'multiplier': 20})
    risk_result = risk_analyzer.analyze_risk(data_config)
    
    if risk_result['status'] == 'success':
        print(f"   {risk_result['summary']['verdict']}")
        print(f"   {risk_result['summary']['bias']}")

if __name__ == "__main__":
    # Check if strike price provided as argument
    if len(sys.argv) > 1:
        try:
            strike = int(sys.argv[1])
            analyze_strike_risk(strike)
        except ValueError:
            print("Please provide a valid strike price as a number")
    else:
        # Default to 21720
        analyze_strike_risk(21720)
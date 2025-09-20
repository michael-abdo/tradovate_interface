#!/usr/bin/env python3
"""Quick risk check at specific strike"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tasks', 'options_trading_system'))

from data_ingestion.integration import run_data_ingestion

# Load data
data_config = {
    'barchart': {'file_path': 'data/api_responses/options_data_20250602_141553.json'},
    'tradovate': {'mode': 'demo', 'cid': '6540', 'secret': 'f7a2b8f5-8348-424f-8ffa-047ab7502b7c', 'use_mock': True}
}

print("Loading options data...")
data_result = run_data_ingestion(data_config)
contracts = data_result['normalized_data']['contracts']

# Analyze around 21720
current_price = 21376.75
target_strike = 21720

print(f'\nRISK ANALYSIS NEAR {target_strike}')
print('=' * 60)
print(f'Current Price: ${current_price:,.2f}')
print(f'Target Strike: ${target_strike:,} ({target_strike-current_price:+.0f} points ABOVE)\n')

# Find exact match
exact_match = None
for contract in contracts:
    if contract['strike'] == target_strike:
        exact_match = contract
        break

if exact_match:
    call_oi = exact_match.get('call_open_interest', 0)
    put_oi = exact_match.get('put_open_interest', 0)
    print(f'Strike {target_strike}: Call OI={call_oi}, Put OI={put_oi}')
else:
    print(f'No exact match for {target_strike}')

# Analyze nearby strikes
print(f'\nNEARBY STRIKES ({target_strike-150} to {target_strike+150}):')
print('-' * 60)

nearby_contracts = []
total_call_risk = 0
total_put_risk = 0

for contract in contracts:
    strike = contract['strike']
    if target_strike - 150 <= strike <= target_strike + 150:
        call_oi = contract.get('call_open_interest', 0)
        put_oi = contract.get('put_open_interest', 0)
        call_price = contract.get('call_mark_price', 0)
        put_price = contract.get('put_mark_price', 0)
        
        if call_oi > 0 or put_oi > 0:
            call_risk = call_oi * call_price * 20
            put_risk = put_oi * put_price * 20
            
            total_call_risk += call_risk
            total_put_risk += put_risk
            
            position = "ABOVE" if strike > current_price else "BELOW"
            distance = strike - current_price
            
            print(f'Strike {strike} ({distance:+.0f} {position}):')
            print(f'  Calls: {call_oi} OI @ ${call_price:.2f} = ${call_risk:,.0f} risk')
            print(f'  Puts: {put_oi} OI @ ${put_price:.2f} = ${put_risk:,.0f} risk')
            
            if call_risk > put_risk:
                print(f'  -> Bulls have more risk')
            elif put_risk > call_risk:
                print(f'  -> Bears have more risk')
            print()

print('\n' + '=' * 60)
print('SUMMARY:')
print(f'Total Call Risk (Bulls) near {target_strike}: ${total_call_risk:,.0f}')
print(f'Total Put Risk (Bears) near {target_strike}: ${total_put_risk:,.0f}')

if total_call_risk > total_put_risk:
    ratio = total_call_risk / total_put_risk if total_put_risk > 0 else 999
    print(f'\n🐂 BULLS HAVE MORE RISK near {target_strike}')
    print(f'Risk Ratio: {ratio:.1f}:1 (Bulls:Bears)')
    print('\nIMPLICATIONS:')
    print('- Bulls will defend this area')
    print('- This level acts as SUPPORT')
    print('- Price likely to bounce if tested')
else:
    ratio = total_put_risk / total_call_risk if total_call_risk > 0 else 999
    print(f'\n🐻 BEARS HAVE MORE RISK near {target_strike}')
    print(f'Risk Ratio: {ratio:.1f}:1 (Bears:Bulls)')
    print('\nIMPLICATIONS:')
    print('- Bears will defend this area')
    print('- This level acts as RESISTANCE') 
    print('- Price likely to reject if tested')

# Overall market context
print('\n' + '=' * 60)
print('OVERALL MARKET CONTEXT:')

total_market_call_risk = sum(c.get('call_open_interest', 0) * c.get('call_mark_price', 0) * 20 
                            for c in contracts)
total_market_put_risk = sum(c.get('put_open_interest', 0) * c.get('put_mark_price', 0) * 20 
                           for c in contracts)

if total_market_put_risk > total_market_call_risk:
    print('🐻 OVERALL: Bears have more risk across all strikes')
    print(f'   Total Put Risk: ${total_market_put_risk:,.0f}')
    print(f'   Total Call Risk: ${total_market_call_risk:,.0f}')
    print('   Market Bias: DOWNWARD PRESSURE')
else:
    print('🐂 OVERALL: Bulls have more risk across all strikes')
    print(f'   Total Call Risk: ${total_market_call_risk:,.0f}')
    print(f'   Total Put Risk: ${total_market_put_risk:,.0f}')
    print('   Market Bias: UPWARD PRESSURE')
#!/usr/bin/env python3
"""
Corrected analysis of MM6N25 data using proper premium calculations
"""

import json
from datetime import datetime

# Load the validated data
with open('outputs/20250630/validated_data/mm6n25_validated_20250630_083024.json', 'r') as f:
    data = json.load(f)

contracts = data['data']['options_data']

# Calculate CORRECT premiums using Volume (not OI)
total_put_premium = 0
total_call_premium = 0
total_put_volume = 0
total_call_volume = 0
total_put_oi = 0
total_call_oi = 0

for contract in contracts:
    if contract['optionType'] == 'Put':
        volume = contract.get('volume', 0) or 0
        price = contract.get('lastPrice', 0) or 0
        oi = contract.get('openInterest', 0) or 0
        
        # Premium = Price × Volume × 20
        premium = price * volume * 20
        total_put_premium += premium
        total_put_volume += volume
        total_put_oi += oi
    else:  # Call
        volume = contract.get('volume', 0) or 0
        price = contract.get('lastPrice', 0) or 0
        oi = contract.get('openInterest', 0) or 0
        
        # Premium = Price × Volume × 20
        premium = price * volume * 20
        total_call_premium += premium
        total_call_volume += volume
        total_call_oi += oi

# Calculate ratios
pcr_premium = total_put_premium / total_call_premium if total_call_premium > 0 else 0
pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
pcr_volume = total_put_volume / total_call_volume if total_call_volume > 0 else 0

print("CORRECTED MM6N25 OPTIONS ANALYSIS")
print("=" * 50)
print(f"Contract: MM6N25 (E-mini S&P Monthly Option)")
print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Total Contracts Analyzed: {len(contracts)}")

print("\n\nVOLUME ANALYSIS:")
print(f"Put Volume Total: {total_put_volume:,}")
print(f"Call Volume Total: {total_call_volume:,}")
print(f"Put/Call Volume Ratio: {pcr_volume:.2f}")

print("\n\nPREMIUM ANALYSIS (Dollar Volume Traded):")
print(f"Put Premium Total: ${total_put_premium:,.2f}")
print(f"Call Premium Total: ${total_call_premium:,.2f}")
print(f"Put/Call Premium Ratio: {pcr_premium:.2f}")

print("\n\nOPEN INTEREST ANALYSIS:")
print(f"Put Open Interest Total: {total_put_oi:,}")
print(f"Call Open Interest Total: {total_call_oi:,}")
print(f"Put/Call Open Interest Ratio: {pcr_oi:.2f}")

print("\n\nMARKET INTERPRETATION:")
if pcr_premium < 0.5:
    print("- Premium Ratio < 0.5: Strong BULLISH bias (more call premium traded)")
elif pcr_premium > 1.5:
    print("- Premium Ratio > 1.5: Strong BEARISH bias (more put premium traded)")
else:
    print(f"- Premium Ratio = {pcr_premium:.2f}: Relatively BALANCED market")

if pcr_oi > 1.2:
    print("- OI Ratio > 1.2: Higher put positions (potential support below)")
elif pcr_oi < 0.8:
    print("- OI Ratio < 0.8: Higher call positions (potential resistance above)")
else:
    print(f"- OI Ratio = {pcr_oi:.2f}: Balanced open interest")

print("\n\nKEY INSIGHT:")
print("Premium = Price × Volume × 20 (represents actual dollars traded)")
print("NOT Price × OI × 20 (which would be total position value)")
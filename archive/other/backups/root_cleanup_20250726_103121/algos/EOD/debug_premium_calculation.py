#!/usr/bin/env python3
"""
Debug script to understand the premium calculation discrepancy
"""

# User's correct values
user_put_premium = 1_113_309.00
user_call_premium = 5_219_492.00

# Example contract from our data
example_contract = {
    "strike": 21325,
    "put_volume": 31,
    "put_oi": 183,
    "put_last_price": 18.0,
    "call_volume": 3,
    "call_oi": 17,
    "call_last_price": 56.75
}

# Our incorrect calculation (Price × OI × 20)
our_put_calc = example_contract["put_last_price"] * example_contract["put_oi"] * 20
our_call_calc = example_contract["call_last_price"] * example_contract["call_oi"] * 20

# Correct calculation (Price × Volume × 20) 
correct_put_calc = example_contract["put_last_price"] * example_contract["put_volume"] * 20
correct_call_calc = example_contract["call_last_price"] * example_contract["call_oi"] * 20

print("PREMIUM CALCULATION ANALYSIS")
print("=" * 50)
print("\nExample Contract: Strike 21325")
print(f"Put: Price=${example_contract['put_last_price']}, Volume={example_contract['put_volume']}, OI={example_contract['put_oi']}")
print(f"Call: Price=${example_contract['call_last_price']}, Volume={example_contract['call_volume']}, OI={example_contract['call_oi']}")

print("\n\nOUR CALCULATION (WRONG - using OI):")
print(f"Put Premium = ${example_contract['put_last_price']} × {example_contract['put_oi']} OI × 20 = ${our_put_calc:,.2f}")
print(f"Call Premium = ${example_contract['call_last_price']} × {example_contract['call_oi']} OI × 20 = ${our_call_calc:,.2f}")

print("\n\nCORRECT CALCULATION (using Volume):")
print(f"Put Premium = ${example_contract['put_last_price']} × {example_contract['put_volume']} Volume × 20 = ${correct_put_calc:,.2f}")
print(f"Call Premium = ${example_contract['call_last_price']} × {example_contract['call_volume']} Volume × 20 = ${correct_call_calc:,.2f}")

print("\n\nKEY INSIGHT:")
print("The 'premium' field in Barchart represents DOLLAR VOLUME TRADED")
print("Premium = Option Price × Volume × 20 (contract multiplier)")
print("This is NOT the same as total position value (Price × OI × 20)")

print("\n\nWHAT THIS MEANS:")
print("- Premium shows actual money that changed hands today")
print("- It's based on Volume (contracts traded), not OI (contracts held)")
print("- OI represents total open positions, Volume represents today's trading activity")
print(f"\nUser's totals: Put Premium ${user_put_premium:,.2f}, Call Premium ${user_call_premium:,.2f}")
print("These represent the total dollar volume traded in puts and calls today")
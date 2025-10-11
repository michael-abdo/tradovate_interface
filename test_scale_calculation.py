#!/usr/bin/env python3
"""Test script to verify scale order calculations"""

from src.dashboard import calculate_scale_orders

def test_scale_calculation():
    """Test scale order calculation with specific parameters"""
    print("🧪 Testing Scale Order Calculation")
    print("=" * 50)
    
    # Test parameters matching your question
    symbol = "NQ"
    quantity = 4
    action = "Buy"
    entry_price = 21000.0  # Example entry price
    scale_levels = 4
    scale_ticks = 20  # 20 ticks between levels
    tick_size = 0.25  # NQ tick size
    
    print(f"Test Parameters:")
    print(f"  Entry Price: ${entry_price}")
    print(f"  Scale Levels: {scale_levels}")
    print(f"  Scale Ticks: {scale_ticks}")
    print(f"  Tick Size: ${tick_size}")
    print()
    
    # Calculate scale orders
    orders = calculate_scale_orders(symbol, quantity, action, entry_price, scale_levels, scale_ticks, tick_size)
    
    print("Expected Entry Points:")
    expected_prices = []
    for i in range(scale_levels):
        offset = i * scale_ticks * tick_size
        expected_price = entry_price - offset
        expected_prices.append(expected_price)
        print(f"  Level {i+1}: ${expected_price:.2f} (entry - {offset})")
    
    print()
    print("Actual Calculated Orders:")
    for i, order in enumerate(orders):
        price = order['entry_price']
        qty = order['quantity']
        print(f"  Level {i+1}: {qty} contracts @ ${price:.2f}")
        
        # Verify price matches expected
        expected = expected_prices[i]
        if abs(price - expected) < 0.01:  # Allow small floating point differences
            print(f"    ✅ CORRECT: Matches expected ${expected:.2f}")
        else:
            print(f"    ❌ ERROR: Expected ${expected:.2f}, got ${price:.2f}")
    
    print()
    print("Summary:")
    print(f"  Total orders: {len(orders)}")
    print(f"  Total quantity: {sum(order['quantity'] for order in orders)} contracts")
    
    # Verify the spacing
    if len(orders) >= 2:
        price_diff = orders[0]['entry_price'] - orders[1]['entry_price']
        expected_diff = scale_ticks * tick_size
        print(f"  Price spacing: ${price_diff:.2f} (expected: ${expected_diff:.2f})")
        if abs(price_diff - expected_diff) < 0.01:
            print(f"    ✅ SPACING CORRECT")
        else:
            print(f"    ❌ SPACING ERROR")

if __name__ == "__main__":
    test_scale_calculation()
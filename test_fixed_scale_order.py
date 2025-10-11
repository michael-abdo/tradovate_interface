#!/usr/bin/env python3

import sys
import time
import json
from src.app import TradovateController

def test_fixed_scale_order():
    """Test scale order with the fixed direct entry price passing"""
    controller = TradovateController()
    
    if len(controller.connections) == 0:
        print("No Tradovate connections found.")
        return False
    
    conn = controller.connections[0]
    if not conn.tab:
        print("No tab available")
        return False
    
    print(f"Testing fixed scale order on {conn.account_name}...")
    
    # Clear console and add start marker
    conn.tab.Runtime.evaluate(expression="""
        console.clear();
        console.log('🎯🎯🎯 TESTING FIXED SCALE ORDER WITH DIRECT ENTRY PRICE PASSING 🎯🎯🎯');
        console.log('Timestamp:', new Date().toISOString());
    """)
    
    print("Console cleared, executing scale order with fixed logic...")
    
    # Get current market price for proper LIMIT order calculation
    market_check = """
    const marketData = getMarketData('NQ');
    JSON.stringify({
        bidPrice: marketData ? parseFloat(marketData.bidPrice) : null,
        offerPrice: marketData ? parseFloat(marketData.offerPrice) : null
    });
    """
    
    market_result = conn.tab.Runtime.evaluate(expression=market_check)
    market_data = json.loads(market_result['result']['value'])
    current_offer = market_data['offerPrice']
    
    print(f"Current market - Bid: {market_data['bidPrice']}, Offer: {current_offer}")
    
    # Create scale orders BELOW current offer price to ensure they're LIMIT orders
    # Current offer is around 25347, so we'll place buy orders below that
    entry_base = current_offer - 10  # Start 10 points below market
    scale_orders = [
        {"quantity": 1, "entry_price": entry_base},      # 10 points below market
        {"quantity": 1, "entry_price": entry_base - 5},  # 15 points below market  
        {"quantity": 1, "entry_price": entry_base - 10}, # 20 points below market
        {"quantity": 1, "entry_price": entry_base - 15}  # 25 points below market
    ]
    
    print(f"Scale orders (all should be LIMIT since below market):")
    for i, order in enumerate(scale_orders):
        print(f"  Order {i+1}: {order['quantity']} @ {order['entry_price']} (market={current_offer})")
    
    # Execute the scale order
    result = conn.auto_trade_scale(
        symbol="NQ", 
        scale_orders=scale_orders, 
        action="Buy", 
        tp_ticks=0,
        sl_ticks=0, 
        tick_size=0.25
    )
    
    print(f"Scale order execution result: {result}")
    
    # Wait for execution
    print("Waiting 8 seconds for execution and logging...")
    time.sleep(8)
    
    # Add completion marker
    conn.tab.Runtime.evaluate(expression="""
        console.log('🎯🎯🎯 FIXED SCALE ORDER TEST COMPLETED 🎯🎯🎯');
        console.log('Final timestamp:', new Date().toISOString());
        
        // Check if we can see any order activity
        'test_completed_successfully';
    """)
    
    print("Test completed!")
    return True

if __name__ == "__main__":
    test_fixed_scale_order()
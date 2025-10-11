#!/usr/bin/env python3

import sys
import time
import json
from src.app import TradovateController

def test_debug_logging():
    """Test scale order with the new debug logging to see where execution stops"""
    controller = TradovateController()
    
    if len(controller.connections) == 0:
        print("No Tradovate connections found.")
        return False
    
    conn = controller.connections[0]
    if not conn.tab:
        print("No tab available")
        return False
    
    print(f"Testing scale order with debug logging on {conn.account_name}...")
    
    # Clear console and add start marker
    conn.tab.Runtime.evaluate(expression="""
        console.clear();
        console.log('🚨🚨🚨 STARTING SCALE ORDER TEST WITH DEBUG LOGGING 🚨🚨🚨');
        console.log('Timestamp:', new Date().toISOString());
    """)
    
    print("Console cleared, executing scale order...")
    
    # Execute scale order - use actual entry prices this time
    scale_orders = [
        {"quantity": 1, "entry_price": 25300.00},  # Entry level
        {"quantity": 1, "entry_price": 25295.00},  # Entry - 20 ticks (20 * 0.25)
        {"quantity": 1, "entry_price": 25290.00},  # Entry - 40 ticks
        {"quantity": 1, "entry_price": 25285.00}   # Entry - 60 ticks
    ]
    
    print(f"Executing scale order with entry prices: {scale_orders}")
    
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
    
    # Wait for execution to complete
    print("Waiting 5 seconds for execution...")
    time.sleep(5)
    
    # Add completion marker
    conn.tab.Runtime.evaluate(expression="""
        console.log('🚨🚨🚨 SCALE ORDER TEST COMPLETED 🚨🚨🚨');
        console.log('Final timestamp:', new Date().toISOString());
    """)
    
    return True

if __name__ == "__main__":
    test_debug_logging()
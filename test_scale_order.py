#!/usr/bin/env python3

import sys
import json
from src.app import TradovateController

def test_scale_order():
    """Test manual scale order execution"""
    controller = TradovateController()
    
    if len(controller.connections) == 0:
        print("No Tradovate connections found.")
        return False
    
    conn = controller.connections[0]
    if not conn.tab:
        print("No tab available")
        return False
    
    print(f"Testing scale order on {conn.account_name}...")
    
    # Create test scale orders (4 levels as expected)
    scale_orders = [
        {"quantity": 1, "tick_offset": 0},    # Entry level
        {"quantity": 1, "tick_offset": -20},  # Entry - 20 ticks  
        {"quantity": 1, "tick_offset": -40},  # Entry - 40 ticks
        {"quantity": 1, "tick_offset": -60}   # Entry - 60 ticks
    ]
    
    print(f"Scale orders to execute: {scale_orders}")
    
    # Call the auto_trade_scale function directly through Python
    try:
        result = conn.auto_trade_scale(
            symbol="NQ", 
            scale_orders=scale_orders, 
            action="Buy", 
            tp_ticks=100, 
            sl_ticks=40, 
            tick_size=0.25
        )
        
        print(f"\n=== SCALE ORDER EXECUTION RESULT ===")
        print(f"Result: {result}")
        
        # Also test by calling the JavaScript function directly
        orders_json = json.dumps(scale_orders)
        js_direct_call = f"""
        console.log('🧪 DIRECT JAVASCRIPT TEST: Calling auto_trade_scale directly');
        console.log('Parameters:', 'NQ', {orders_json}, 'Buy', 100, 40, 0.25);
        
        try {{
            var result = auto_trade_scale('NQ', {orders_json}, 'Buy', 100, 40, 0.25);
            console.log('🧪 Direct call result:', result);
            JSON.stringify({{
                status: 'success',
                result: result || 'completed',
                orders_count: {len(scale_orders)}
            }});
        }} catch (error) {{
            console.error('🧪 Direct call error:', error);
            JSON.stringify({{
                status: 'error',
                error: error.toString(),
                orders_count: {len(scale_orders)}
            }});
        }}
        """
        
        print(f"\n=== DIRECT JAVASCRIPT CALL TEST ===")
        js_result = conn.tab.Runtime.evaluate(expression=js_direct_call)
        print(f"Direct JS result: {js_result}")
        
        return True
        
    except Exception as e:
        print(f"Error executing scale order: {e}")
        return False

if __name__ == "__main__":
    success = test_scale_order()
    if success:
        print("\n✅ Scale order test completed!")
    else:
        print("\n❌ Scale order test failed")
    sys.exit(0 if success else 1)
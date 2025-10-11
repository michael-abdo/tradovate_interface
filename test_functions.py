#!/usr/bin/env python3

import sys
import json
from src.app import TradovateController

def test_functions():
    """Test if functions are available in the browser"""
    controller = TradovateController()
    
    if len(controller.connections) == 0:
        print("No Tradovate connections found.")
        return False
    
    conn = controller.connections[0]
    if not conn.tab:
        print("No tab available")
        return False
    
    print(f"Testing functions on {conn.account_name}...")
    
    # Test if functions exist
    test_script = """
    JSON.stringify({
        autoTrade_exists: typeof window.autoTrade === 'function',
        auto_trade_scale_exists: typeof window.auto_trade_scale === 'function',
        autoTrade_type: typeof window.autoTrade,
        auto_trade_scale_type: typeof window.auto_trade_scale,
        autoTrade_string: window.autoTrade ? window.autoTrade.toString().substring(0, 100) + '...' : 'NOT FOUND',
        auto_trade_scale_string: window.auto_trade_scale ? window.auto_trade_scale.toString().substring(0, 100) + '...' : 'NOT FOUND'
    })
    """
    
    try:
        result = conn.tab.Runtime.evaluate(expression=test_script)
        if 'result' in result and 'value' in result['result']:
            data = json.loads(result['result']['value'])
            
            print(f"\n=== FUNCTION AVAILABILITY TEST ===")
            print(f"autoTrade exists: {data['autoTrade_exists']}")
            print(f"auto_trade_scale exists: {data['auto_trade_scale_exists']}")
            print(f"autoTrade type: {data['autoTrade_type']}")
            print(f"auto_trade_scale type: {data['auto_trade_scale_type']}")
            print(f"autoTrade preview: {data['autoTrade_string']}")
            print(f"auto_trade_scale preview: {data['auto_trade_scale_string']}")
            
            return data['autoTrade_exists'] and data['auto_trade_scale_exists']
        else:
            print(f"Unexpected result format: {result}")
            return False
            
    except Exception as e:
        print(f"Error testing functions: {e}")
        return False

if __name__ == "__main__":
    functions_available = test_functions()
    if functions_available:
        print("\n✅ Both functions are available!")
        sys.exit(0)
    else:
        print("\n❌ Functions are not available")
        sys.exit(1)
#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app import TradovateController

print("=== Testing TradovateController ===")

# Initialize controller
controller = TradovateController()

print(f"\nTotal connections found: {len(controller.connections)}")

# Test each connection
for i, conn in enumerate(controller.connections):
    print(f"\n--- Connection {i}: {conn.account_name} on port {conn.port} ---")
    
    # Try to get account data
    try:
        if conn.tab:
            # Check if getAllAccountTableData exists
            result = conn.tab.Runtime.evaluate(expression="typeof window.getAllAccountTableData")
            func_type = result.get('result', {}).get('value', 'undefined')
            print(f"getAllAccountTableData type: {func_type}")
            
            if func_type == 'function':
                # Execute it
                data_result = conn.tab.Runtime.evaluate(expression="window.getAllAccountTableData()")
                data = data_result.get('result', {}).get('value')
                if data:
                    import json
                    parsed_data = json.loads(data)
                    print(f"Account data: {len(parsed_data)} accounts found")
                    for account in parsed_data:
                        print(f"  - {account.get('Account', 'N/A')}: {account.get('Net Liquidation', 'N/A')}")
                else:
                    print("No account data returned")
        else:
            print("No tab available")
    except Exception as e:
        print(f"Error: {e}")
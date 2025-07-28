#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Flask app and controller
from src.dashboard import app, controller

print(f"=== Dashboard Controller Test ===")
print(f"Total connections: {len(controller.connections)}")

for i, conn in enumerate(controller.connections):
    print(f"\nConnection {i}: {conn.account_name}")
    print(f"  Port: {conn.port}")
    print(f"  Has tab: {conn.tab is not None}")
    
    if conn.tab:
        try:
            # Try to execute getAllAccountTableData directly
            result = conn.tab.Runtime.evaluate(expression="typeof window.getAllAccountTableData")
            func_type = result.get('result', {}).get('value', 'undefined')
            print(f"  getAllAccountTableData type: {func_type}")
            
            if func_type == 'function':
                # Execute it
                data_result = conn.tab.Runtime.evaluate(expression="window.getAllAccountTableData()")
                data = data_result.get('result', {}).get('value')
                if data:
                    import json
                    parsed_data = json.loads(data)
                    print(f"  Account data: {len(parsed_data)} accounts")
                else:
                    print("  No account data returned")
        except Exception as e:
            print(f"  Error: {e}")

# Test with app context
print("\n=== Testing within Flask app context ===")
with app.test_client() as client:
    response = client.get('/api/accounts')
    print(f"API Response Status: {response.status_code}")
    print(f"API Response Data: {response.data.decode()}")
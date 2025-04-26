#!/usr/bin/env python3
import threading
import time
from flask import Flask, render_template, jsonify
import sys
import os
import json

# Import from app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import TradovateController

# Create Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Initialize controller
controller = TradovateController()

def inject_account_data_function():
    """Inject the getAllAccountTableData function into all tabs"""
    for conn in controller.connections:
        if conn.tab:
            try:
                # Read the function from the file
                account_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                       'tampermonkey/getAllAccountTableData.user.js')
                with open(account_data_path, 'r') as file:
                    get_account_data_js = file.read()
                
                # Inject it into the tab
                conn.tab.Runtime.evaluate(expression=get_account_data_js)
                print(f"Injected getAllAccountTableData into {conn.account_name}")
            except Exception as e:
                print(f"Error injecting account data function: {e}")

# Route for dashboard UI
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

# API endpoint to get all account data
@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    print("\n==== Fetching account data ====")
    account_data = []
    print(f"Found {len(controller.connections)} connections")
    
    # Fetch data from all tabs
    for i, conn in enumerate(controller.connections):
        if conn.tab:
            print(f"Processing connection {i+1}: {conn.account_name}")
            try:
                # First make sure the getAllAccountTableData function is available
                try:
                    # Re-inject the function to ensure it's available
                    account_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                           'tampermonkey/getAllAccountTableData.user.js')
                    with open(account_data_path, 'r') as file:
                        get_account_data_js = file.read()
                    conn.tab.Runtime.evaluate(expression=get_account_data_js)
                    print(f"Re-injected getAllAccountTableData into {conn.account_name}")
                except Exception as inject_err:
                    print(f"Error re-injecting function: {inject_err}")
                
                # Execute the getAllAccountTableData() function in each tab
                print(f"Executing getAllAccountTableData() in {conn.account_name}")
                result = conn.tab.Runtime.evaluate(
                    expression="getAllAccountTableData()")
                
                print(f"Result received for {conn.account_name}")
                print(f"Result type: {type(result)}")
                print(f"Result keys: {result.keys() if hasattr(result, 'keys') else 'No keys'}")
                
                if result and 'result' in result:
                    print(f"Result['result'] keys: {result['result'].keys() if hasattr(result['result'], 'keys') else 'No keys'}")
                
                if result and 'result' in result and 'value' in result['result']:
                    print(f"Value type: {type(result['result']['value'])}")
                    print(f"Value content sample: {result['result']['value'][:100] if isinstance(result['result']['value'], str) else 'Not a string'}")
                    
                    try:
                        # Parse the JSON result
                        tab_data = json.loads(result['result']['value'])
                        print(f"Parsed JSON data type: {type(tab_data)}")
                        print(f"Found {len(tab_data) if isinstance(tab_data, list) else 'non-list'} items")
                        
                        if not tab_data:
                            print(f"No account data returned from {conn.account_name}")
                            continue
                            
                        # Add account identifier to each item
                        for item in tab_data:
                            item['account_name'] = conn.account_name
                            item['account_index'] = i
                        
                        account_data.extend(tab_data)
                        print(f"Added {len(tab_data)} items from {conn.account_name}")
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON from {conn.account_name}: {e}")
                        print(f"Raw value: {result['result']['value']}")
                else:
                    print(f"No valid result structure for {conn.account_name}")
            except Exception as e:
                print(f"Error getting account data from {conn.account_name}: {e}")
    
    print(f"Total account data items: {len(account_data)}")
    print("==== End of account data fetch ====\n")
    return jsonify(account_data)

# API endpoint to get summary data
@app.route('/api/summary', methods=['GET'])
def get_summary():
    # We'll forward this to the accounts endpoint since we're now focusing on account data
    accounts_response = get_accounts()
    accounts_data = json.loads(accounts_response.get_data(as_text=True))
    
    # Calculate summary stats
    total_pnl = 0
    total_margin = 0
    
    for account in accounts_data:
        # Try to extract P&L (check both original and standardized names)
        pnl_fields = ['Total P&L', 'Dollar Total P L']
        for field in pnl_fields:
            if field in account:
                val = account[field]
                if isinstance(val, (int, float)):
                    total_pnl += val
                elif isinstance(val, str):
                    try:
                        total_pnl += float(val.replace('$', '').replace(',', ''))
                    except (ValueError, TypeError):
                        pass
                break
                    
        # Try to extract margin (check both original and standardized names)
        margin_fields = ['Available Margin', 'Total Available Margin']
        for field in margin_fields:
            if field in account:
                val = account[field]
                if isinstance(val, (int, float)):
                    total_margin += val
                elif isinstance(val, str):
                    try:
                        total_margin += float(val.replace('$', '').replace(',', ''))
                    except (ValueError, TypeError):
                        pass
                break
    
    return jsonify({
        'total_pnl': total_pnl,
        'total_margin': total_margin,
        'account_count': len(accounts_data)
    })

# Run the app
def run_flask_dashboard():
    inject_account_data_function()
    app.run(host='0.0.0.0', port=6001)

if __name__ == '__main__':
    # Start the Flask server
    inject_account_data_function()
    app.run(host='0.0.0.0', port=6001, debug=True)
    print("Dashboard running at http://localhost:6001")
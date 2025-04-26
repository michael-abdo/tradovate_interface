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
    account_data = []
    # Fetch data from all tabs
    for i, conn in enumerate(controller.connections):
        if conn.tab:
            try:
                # Execute the getAllAccountTableData() function in each tab
                result = conn.tab.Runtime.evaluate(
                    expression="getAllAccountTableData()")
                
                if result and 'result' in result and 'value' in result['result']:
                    # Add account identifier to the data
                    tab_data = json.loads(result['result']['value'])
                    for item in tab_data:
                        item['account_name'] = conn.account_name
                        item['account_index'] = i
                    
                    account_data.extend(tab_data)
            except Exception as e:
                print(f"Error getting account data from {conn.account_name}: {e}")
    
    return jsonify(account_data)

# API endpoint to get summary data
@app.route('/api/summary', methods=['GET'])
def get_summary():
    total_pnl = 0
    account_summaries = []
    
    # Fetch data from all tabs
    for i, conn in enumerate(controller.connections):
        if conn.tab:
            try:
                # Get account data
                result = conn.tab.Runtime.evaluate(
                    expression="getAllAccountTableData()")
                
                if result and 'result' in result and 'value' in result['result']:
                    tab_data = json.loads(result['result']['value'])
                    
                    # Calculate account PnL
                    account_pnl = 0
                    for item in tab_data:
                        pnl = item.get('P&L', 0)
                        if isinstance(pnl, str):
                            # Remove $ and commas from the string and convert to float
                            pnl = pnl.replace('$', '').replace(',', '')
                            try:
                                pnl = float(pnl)
                            except ValueError:
                                pnl = 0
                        account_pnl += pnl
                    
                    # Add to total
                    total_pnl += account_pnl
                    
                    # Add account summary
                    account_summaries.append({
                        'account_name': conn.account_name,
                        'account_index': i,
                        'pnl': account_pnl,
                        'position_count': len(tab_data)
                    })
            except Exception as e:
                print(f"Error getting summary data from {conn.account_name}: {e}")
    
    return jsonify({
        'total_pnl': total_pnl,
        'account_count': len(controller.connections),
        'accounts': account_summaries
    })

# Run the app
def run_flask_dashboard():
    inject_account_data_function()
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    # Start the Flask server
    inject_account_data_function()
    app.run(host='0.0.0.0', port=5000, debug=True)
    print("Dashboard running at http://localhost:5000")
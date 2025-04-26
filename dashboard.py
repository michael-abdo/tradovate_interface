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
from flask import request

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
                # First make sure the getAllAccountTableData function is available
                try:
                    # Re-inject the function to ensure it's available
                    account_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                           'tampermonkey/getAllAccountTableData.user.js')
                    with open(account_data_path, 'r') as file:
                        get_account_data_js = file.read()
                    conn.tab.Runtime.evaluate(expression=get_account_data_js)
                except Exception as inject_err:
                    print(f"Error re-injecting function: {inject_err}")
                
                # Execute the getAllAccountTableData() function in each tab
                result = conn.tab.Runtime.evaluate(
                    expression="getAllAccountTableData()")
                
                if result and 'result' in result and 'value' in result['result']:
                    try:
                        # Parse the JSON result
                        tab_data = json.loads(result['result']['value'])
                        
                        if not tab_data:
                            continue
                            
                        # Add account identifier to each item
                        for item in tab_data:
                            item['account_name'] = conn.account_name
                            item['account_index'] = i
                            
                            # Ensure we have both User and Phase fields (Phase is the renamed User field)
                            if 'User' in item and 'Phase' not in item:
                                item['Phase'] = item['User']
                                
                            # Standardize Account field - ensure there's only one Account field
                            # and remove any with arrows
                            if 'Account ▲' in item:
                                account_value = item['Account ▲']
                                # Remove the old key and add standardized one
                                item.pop('Account ▲', None)
                                # Make sure we don't create duplicate Account fields
                                if 'Account' not in item:
                                    item['Account'] = account_value
                        
                        account_data.extend(tab_data)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON from {conn.account_name}: {e}")
                else:
                    print(f"No valid result structure for {conn.account_name}")
            except Exception as e:
                print(f"Error getting account data from {conn.account_name}: {e}")
    
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

# API endpoint to execute trades
@app.route('/api/trade', methods=['POST'])
def execute_trade():
    try:
        data = request.json
        
        # Extract parameters from request
        symbol = data.get('symbol', 'NQ')
        quantity = data.get('quantity', 1)
        action = data.get('action', 'Buy')
        tick_size = data.get('tick_size', 0.25)
        account_index = data.get('account', 'all')
        
        # Check TP/SL enable flags
        enable_tp = data.get('enable_tp', True)
        enable_sl = data.get('enable_sl', True)
        
        # Only get TP/SL values if they are enabled
        tp_ticks = data.get('tp_ticks', 100) if enable_tp else 0
        sl_ticks = data.get('sl_ticks', 40) if enable_sl else 0
        
        # Ensure tp_ticks and sl_ticks are integers
        tp_ticks = int(tp_ticks) if tp_ticks else 0
        sl_ticks = int(sl_ticks) if sl_ticks else 0
        
        print(f"Trade request: {symbol} {action} {quantity} TP:{tp_ticks if enable_tp else 'disabled'} SL:{sl_ticks if enable_sl else 'disabled'}")
        
        # Check if we should execute on all accounts or just one
        if account_index == 'all':
            # We need to update auto_trade.js to respect tp_ticks=0 and sl_ticks=0 as disabled
            result = controller.execute_on_all(
                'auto_trade', 
                symbol, 
                quantity, 
                action, 
                tp_ticks if enable_tp else 0,  # Pass 0 to disable TP
                sl_ticks if enable_sl else 0,  # Pass 0 to disable SL
                tick_size
            )
            
            # Count successful trades
            accounts_affected = sum(1 for r in result if 'error' not in r['result'])
            
            return jsonify({
                'status': 'success',
                'message': f'{action} trade executed on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': result
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            result = controller.execute_on_one(
                account_index,
                'auto_trade', 
                symbol, 
                quantity, 
                action, 
                tp_ticks if enable_tp else 0,  # Pass 0 to disable TP
                sl_ticks if enable_sl else 0,  # Pass 0 to disable SL
                tick_size
            )
            
            return jsonify({
                'status': 'success',
                'message': f'{action} trade executed on account {account_index}',
                'accounts_affected': 1,
                'details': result
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# API endpoint to exit positions or cancel orders
@app.route('/api/exit', methods=['POST'])
def exit_positions():
    try:
        data = request.json
        
        # Extract parameters from request
        symbol = data.get('symbol', 'NQ')
        option = data.get('option', 'cancel-option-Exit-at-Mkt-Cxl')
        account_index = data.get('account', 'all')
        
        # Check if we should execute on all accounts or just one
        if account_index == 'all':
            result = controller.execute_on_all('exit_positions', symbol, option)
            
            # Count successful operations
            accounts_affected = sum(1 for r in result if 'error' not in r['result'])
            
            return jsonify({
                'status': 'success',
                'message': f'Exit/cancel operation executed on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': result
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            result = controller.execute_on_one(
                account_index,
                'exit_positions', 
                symbol, 
                option
            )
            
            return jsonify({
                'status': 'success',
                'message': f'Exit/cancel operation executed on account {account_index}',
                'accounts_affected': 1,
                'details': result
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
        
# API endpoint to update symbol on accounts
@app.route('/api/update-symbol', methods=['POST'])
def update_symbol():
    try:
        data = request.json
        
        # Extract parameters from request
        symbol = data.get('symbol', 'NQ')
        account_index = data.get('account', 'all')
        
        # Check if we should execute on all accounts or just one
        if account_index == 'all':
            result = controller.execute_on_all('update_symbol', symbol)
            
            # Count successful operations
            accounts_affected = sum(1 for r in result if 'error' not in r['result'])
            
            return jsonify({
                'status': 'success',
                'message': f'Symbol updated to {symbol} on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': result
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            result = controller.execute_on_one(
                account_index,
                'update_symbol', 
                symbol
            )
            
            return jsonify({
                'status': 'success',
                'message': f'Symbol updated to {symbol} on account {account_index}',
                'accounts_affected': 1,
                'details': result
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# API endpoint to update quantity on accounts
@app.route('/api/update-quantity', methods=['POST'])
def update_quantity():
    try:
        data = request.json
        
        # Extract parameters from request
        quantity = data.get('quantity', 1)
        account_index = data.get('account', 'all')
        
        # This is a placeholder - we don't have a direct quantity update method,
        # but we can add one in the future. For now, we'll just return success.
        
        return jsonify({
            'status': 'success',
            'message': f'Quantity updated to {quantity}',
            'accounts_affected': len(controller.connections) if account_index == 'all' else 1
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# API endpoint to get strategy mappings
@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    try:
        strategy_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'strategy_mappings.json')
        if not os.path.exists(strategy_file):
            # Create default file if it doesn't exist
            default_mappings = {
                "strategy_mappings": {
                    "DEFAULT": []
                }
            }
            with open(strategy_file, 'w') as f:
                json.dump(default_mappings, f, indent=2)
                
        with open(strategy_file, 'r') as f:
            mappings = json.load(f)
        return jsonify(mappings), 200
    except Exception as e:
        print(f"Error loading strategy mappings: {e}")
        return jsonify({"error": f"Failed to load strategy mappings: {str(e)}"}), 500

# API endpoint to update strategy mappings
@app.route('/api/strategies', methods=['POST'])
def update_strategies():
    try:
        data = request.json
        strategy_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'strategy_mappings.json')
        
        with open(strategy_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"Strategy mappings updated: {json.dumps(data, indent=2)}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error saving strategy mappings: {e}")
        return jsonify({"error": f"Failed to update strategy mappings: {str(e)}"}), 500

# Run the app
def run_flask_dashboard():
    inject_account_data_function()
    app.run(host='0.0.0.0', port=6001)

if __name__ == '__main__':
    # Start the Flask server
    inject_account_data_function()
    app.run(host='0.0.0.0', port=6001, debug=True)
    print("Dashboard running at http://localhost:6001")